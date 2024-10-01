#! /usr/bin/env python3

import os
import subprocess
import time
from dataclasses import dataclass

from aas_test_engines.api import execute_tests, ExecConf
import requests

script_dir = os.path.dirname(os.path.realpath(__file__))
root_dir = os.path.realpath(os.path.join(script_dir, "check_servers"))
test_data_dir = os.path.join(root_dir, 'test_data')

profile = 'https://admin-shell.io/aas/API/3/0/AssetAdministrationShellRepositoryServiceSpecification/SSP-002'

# https://stackoverflow.com/questions/27981545
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

@dataclass
class Server:
    name: str
    url: str

    def is_https(self):
        return self.url.startswith('https://')


servers = [
    Server('basyx_java', 'http://localhost:8000'),
    Server('faaast', 'https://localhost:8000/api/v3.0'),
    Server('basyx_python', 'http://localhost:8000/api/v3.0'),
    Server('aasx_server', 'http://localhost:8000/api/v3.0'),
]


def wait_for_server(url: str, max_tries=10):
    for _ in range(max_tries):
        try:
            requests.get(url, verify=False)
            print(f"Server is up at {url}")
            return
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    print(f"Cannot reach server at {url}")


def create_if_not_exists(path):
    try:
        os.mkdir(path)
    except FileExistsError:
        pass


# Workaround for aasx server (see https://github.com/eclipse-aaspe/server/issues/354)
create_if_not_exists(os.path.join(test_data_dir, 'files'))
create_if_not_exists(os.path.join(test_data_dir, 'xml'))


def docker_compose(cwd, *args):
    subprocess.check_call([
        "docker", "compose",
        "-f", os.path.join(cwd, 'compose.yml'),
        *args
    ], cwd=cwd)


def main():

    # Remove left-overs
    for server in servers:
        server_dir = os.path.join(root_dir, 'servers', server.name)
        docker_compose(server_dir, 'kill')

    # Run tests
    mats = []
    for server in servers:
        print(f"Checking {server.name}")
        server_dir = os.path.join(root_dir, 'servers', server.name)
        result_file = os.path.join(root_dir, 'results', f"{server.name}.html")
        print(f"cwd:    {server_dir}")
        print(f"result: {result_file}")

        docker_compose(server_dir, 'up', '-d')
        wait_for_server(server.url)
        result, mat = execute_tests(ExecConf(server=server.url, verify=False), profile)
        with open(result_file, "w") as f:
            f.write(result.to_html())
        mats.append(mat)
        # to save some time, we are not gentle here
        docker_compose(server_dir, 'kill')
        print()

    for mat, server in zip(mats, servers):
        print(server.name)
        mat.print()
        print(f"Accuracy: {round(mat.accuracy()*100)}%")
        print()


main()
