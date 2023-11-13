import argparse
import sys
from aas_test_engines import api, file


def run_file_test(argv):
    parser = argparse.ArgumentParser(description='Runs test cases')
    parser.add_argument('file',
                        type=argparse.FileType('r'),
                        help='the file to check')
    args = parser.parse_args(argv)
    result = file.check_aasx_file(args.file)
    print(result)


def run_api_test(argv):
    parser = argparse.ArgumentParser(description='Runs test cases')
    parser.add_argument('server',
                        type=str,
                        help='server to run the tests against')
    parser.add_argument('--dry',
                        action='store_true',
                        help="dry run, do not send requests")
    parser.add_argument('--suite',
                        type=str,
                        help='selected test suite')
    args = parser.parse_args(argv)
    if args.suite:
        suites = set([args.suite])
    else:
        suites = None
    tests = api.generate_tests(suites=suites)
    for result in api.execute_tests(tests, args.server, args.dry):
        result.dump()


commands = {
    'file': run_file_test,
    'api': run_api_test,
}

if len(sys.argv) <= 1:
    print(f"Usage: {sys.argv[0]} COMMAND OPTIONS...")
    print("Available commands:")
    print("  file     Check a file for compliance.")
    print("  api      Check a server instance for compliance.")
    exit(1)

command = sys.argv[1]

if command not in commands:
    print(f"Unknown command '{command}', must be one of {', '.join(commands)}")
    exit(1)

remaining_args = sys.argv[2:]
commands[command](remaining_args)
