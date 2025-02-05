#! /usr/bin/env python3

import urllib3
import os
import subprocess
import time
from typing import List
from dataclasses import dataclass, field
import base64

from aas_test_engines.api import execute_tests, ExecConf
import requests
from fences.core.util import ConfusionMatrix, Table, print_table

script_dir = os.path.dirname(os.path.realpath(__file__))
root_dir = os.path.realpath(os.path.join(script_dir, "check_servers"))
test_data_dir = os.path.join(root_dir, 'test_data')

SSP_PREFIX = "https://admin-shell.io/aas/API/3/0/"
AAS_ID = base64.b64encode(b"www.example.com/ids/aas/8132_4102_8042_7561").decode()
SUBMODEL_ID = base64.b64encode(b"www.example.com/ids/sm/8132_4102_8042_1861").decode()


@dataclass
class Profile:
    short_name: str
    spec_name: str
    url_suffix: str
    discard_prefix: str
    mats: List[ConfusionMatrix] = field(default_factory=list)

profiles = [
    Profile(
        'aas-repo',
        f'{SSP_PREFIX}AssetAdministrationShellRepositoryServiceSpecification/SSP-002',
        '',
        '',
    ),
    Profile(
        'submodel-repo',
        f'{SSP_PREFIX}SubmodelRepositoryServiceSpecification/SSP-002',
        '',
        '',
    ),
    Profile(
        'aas',
        f'{SSP_PREFIX}AssetAdministrationShellServiceSpecification/SSP-002',
        f'/shells/{AAS_ID}',
        '/aas',
    ),
    Profile(
        'submodel',
        f'{SSP_PREFIX}SubmodelServiceSpecification/SSP-002',
        f'/shells/{AAS_ID}/submodels/{SUBMODEL_ID}',
        '/submodel',
    )
]

# https://stackoverflow.com/questions/27981545
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@dataclass
class Server:
    name: str
    url: str

    def is_https(self):
        return self.url.startswith('https://')


servers = [
    Server('basyx_python', 'http://localhost:8000/api/v3.0'),
    Server('basyx_java', 'http://localhost:8000'),
    Server('faaast', 'https://localhost:8000/api/v3.0'),
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

    # Remove left-overs (e.g, if script crashed in last run)
    for server in servers:
        server_dir = os.path.join(root_dir, 'servers', server.name)
        docker_compose(server_dir, 'kill')

    # Run tests
    for profile in profiles:
        print(profile.short_name)
        for server in servers:
            print(f"Checking {server.name}")
            server_dir = os.path.join(root_dir, 'servers', server.name)
            result_file = os.path.join(root_dir, 'results', f"{profile.short_name}_{server.name}.html")
            print(f"cwd:    {server_dir}")
            print(f"result: {result_file}")

            docker_compose(server_dir, 'up', '-d')
            wait_for_server(server.url)
            conf = ExecConf(
                server=server.url + profile.url_suffix,
                verify=False,
                remove_path_prefix=profile.discard_prefix
            )
            result, mat = execute_tests(conf, profile.spec_name)
            with open(result_file, "w") as f:
                f.write(result.to_html())
            profile.mats.append(mat)
            # to save some time, we are not gentle here
            docker_compose(server_dir, 'kill')
            print()

    # Print results
    table: Table = []
    table.append(['Profile'] + [i.name for i in servers])
    table.append(None)
    for profile in profiles:
        print(profile.short_name)
        line = [profile.short_name]
        for mat, server in zip(profile.mats, servers):
            print(server.name)
            mat.print()
            line.append(f"{round(mat.accuracy()*100)}%")
            print()
        table.append(line)
    print_table(table)

main()
