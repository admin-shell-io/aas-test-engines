import argparse
import sys
import os
import json
from aas_test_engines import api, file
from enum import Enum

# https://stackoverflow.com/questions/27981545
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class InputFormats(Enum):
    xml = 'xml'
    json = 'json'
    aasx = 'aasx'

    def __str__(self):
        return self.value


class OutputFormats(Enum):
    TEXT = 'text'
    JSON = 'json'
    HTML = 'html'


def run_file_test(argv):
    parser = argparse.ArgumentParser(description='Checks a file for compliance with the AAS meta-model')
    parser.add_argument('file',
                        type=argparse.FileType('rb'),
                        help='the file to check')
    parser.add_argument('--format',
                        type=InputFormats,
                        default=InputFormats.aasx,
                        choices=list(InputFormats))
    parser.add_argument('--submodel_template',
                        type=str,
                        default=None,
                        help="Additionally check for compliance to a submodel template")
    parser.add_argument('--output',
                        type=OutputFormats,
                        default=OutputFormats.TEXT,
                        choices=list(OutputFormats))
    args = parser.parse_args(argv)
    if args.submodel_template is None:
        submodel_templates = set()
    else:
        submodel_templates = set([args.submodel_template])

    if args.format == InputFormats.aasx:
        result = file.check_aasx_file(args.file)
    elif args.format == InputFormats.json:
        result = file.check_json_file(args.file, submodel_templates=submodel_templates)
    elif args.format == InputFormats.xml:
        result = file.check_xml_file(args.file)
    else:
        raise Exception(f"Invalid format {args.format}")
    if args.output == OutputFormats.TEXT:
        result.dump()
    elif args.output == OutputFormats.HTML:
        print(result.to_html())
    elif args.output == OutputFormats.JSON:
        print(json.dumps(result.to_dict()))
    else:
        raise Exception(f"Invalid output {args.output}")
    exit(0 if result.ok() else 1)


def run_api_test(argv):
    parser = argparse.ArgumentParser(description='Checks a server instance for compliance with the AAS api')
    parser.add_argument('server',
                        type=str,
                        help='server to run the tests against')
    parser.add_argument('suite',
                        type=str,
                        help='test suite (or substring of it)')
    parser.add_argument('--dry',
                        action='store_true',
                        help="dry run, do not send requests")
    parser.add_argument('--version',
                        type=str,
                        default=api.latest_version())
    parser.add_argument('--no-verify',
                        action='store_true',
                        help='do not check TLS certificate')
    parser.add_argument('--remove-path-prefix',
                        type=str,
                        default='',
                        help='remove prefix from all paths')
    parser.add_argument('--output',
                        type=OutputFormats,
                        default=OutputFormats.TEXT,
                        choices=list(OutputFormats))
    args = parser.parse_args(argv)
    try:
        available_suites = api.supported_versions()[args.version]
    except KeyError:
        sys.stderr.write(f"Unknown version, must be one of {api.supported_versions().keys()}\n")
    suites = [i for i in available_suites if args.suite in i]
    if len(suites) == 0:
        sys.stderr.write(f"Unknown suite '{args.suite}', must be one of:\n")
        for i in available_suites:
            sys.stderr.writelines(f" - {i}\n")
        exit(1)
    elif len(suites) > 1:
        sys.stderr.write(f"Substring '{args.suite}' is not unique, covers:\n")
        for i in suites:
            sys.stderr.write(f" - {i}\n")
        exit(1)
    else:
        suite = suites[0]

    exec_conf = api.ExecConf(
        server=args.server,
        dry=args.dry,
        verify=not args.no_verify,
        remove_path_prefix=args.remove_path_prefix,
    )
    result, mat = api.execute_tests(exec_conf, suite, args.version)
    if args.output == OutputFormats.TEXT:
        result.dump()
    elif args.output == OutputFormats.HTML:
        print(result.to_html())
    elif args.output == OutputFormats.JSON:
        print(json.dumps(result.to_dict()))
    else:
        raise Exception(f"Invalid output {args.output}")
    exit(0 if result.ok() else 1)


def generate_files(argv):
    parser = argparse.ArgumentParser(description='Generates aas files which can be used to test your software')
    parser.add_argument('directory',
                        type=str,
                        help='Directory to place files in')
    args = parser.parse_args(argv)
    if os.path.exists(args.directory):
        print(f"Directory '{args.directory}' already exists, please remove it")
        exit(1)
    os.mkdir(args.directory)
    for idx, (is_valid, sample) in enumerate(file.generate()):
        tag = 'valid' if is_valid else 'invalid'
        with open(os.path.join(args.directory, f"{idx}_{tag}.json"), "w") as f:
            json.dump(sample, f)


commands = {
    'check_file': run_file_test,
    'check_server': run_api_test,
    'generate_files': generate_files,
}


def main():

    if len(sys.argv) <= 1:
        print(f"Usage: {sys.argv[0]} COMMAND OPTIONS...")
        print("Available commands:")
        print("  check_file      Check a file for compliance.")
        print("  check_server    Check a server instance for compliance.")
        print("  generate_files  Generate files for testing")
        exit(1)

    command = sys.argv[1]

    if command not in commands:
        print(f"Unknown command '{command}', must be one of {', '.join(commands)}")
        exit(1)

    remaining_args = sys.argv[2:]
    commands[command](remaining_args)


if __name__ == '__main__':
    main()
