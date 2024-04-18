import argparse
import sys
import os
from aas_test_engines import api, file
from enum import Enum


class Formats(Enum):
    xml = 'xml'
    json = 'json'
    aasx = 'aasx'

    def __str__(self):
        return self.value


def run_file_test(argv):
    parser = argparse.ArgumentParser(description='Checks a file for compliance with the AAS meta-model')
    parser.add_argument('file',
                        type=argparse.FileType('rb'),
                        help='the file to check')
    parser.add_argument('--format',
                        type=Formats,
                        default=Formats.aasx,
                        choices=list(Formats))
    parser.add_argument('--html',
                        type=argparse.FileType('w'),
                        default=None)
    args = parser.parse_args(argv)
    if args.format == Formats.aasx:
        result = file.check_aasx_file(args.file)
    elif args.format == Formats.json:
        result = file.check_json_file(args.file)
    elif args.format == Formats.xml:
        result = file.check_xml_file(args.file)
    else:
        raise Exception(f"Invalid format {args.format}")
    if args.html:
        args.html.write(result.to_html())
    else:
        result.dump()


def run_api_test(argv):
    parser = argparse.ArgumentParser(description='Checks a server instance for compliance with the AAS api')
    parser.add_argument('server',
                        type=str,
                        help='server to run the tests against')
    parser.add_argument('--dry',
                        action='store_true',
                        help="dry run, do not send requests")
    parser.add_argument('--suite',
                        type=str,
                        help='selected test suite')
    parser.add_argument('--no-verify',
                        action='store_true',
                        help='do not check TLS certificate')
    args = parser.parse_args(argv)
    if args.suite:
        suites = set([args.suite])
    else:
        suites = None
    tests = api.generate_tests(suites=suites)
    exec_conf = api.run.ExecConf(
        server=args.server,
        dry=args.dry,
        verify=not args.no_verify,
    )
    for result in api.execute_tests(tests, exec_conf):
        result.dump()


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
    i = 0
    for sample in file.generate():
        with open(os.path.join(args.directory, f"{i}.json"), "w") as f:
            f.write(sample)
        i += 1
        if i > 100:
            break

commands = {
    'check_file': run_file_test,
    'check_server': run_api_test,
    'generate_files': generate_files,
}

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
