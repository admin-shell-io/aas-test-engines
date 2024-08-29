from unittest import TestCase
import subprocess
import os

script_dir = os.path.dirname(os.path.realpath(__file__))


class CheckFileCli(TestCase):

    json_file = os.path.join(script_dir, 'fixtures', 'aasx', 'valid', 'json', 'aasx', 'the_aas.json')
    xml_file = os.path.join(script_dir, 'fixtures', 'aasx', 'valid', 'xml', 'aasx', 'the_aas.xml')

    def invoke(self, args: list):
        result = subprocess.check_output(["python", "-m", "aas_test_engines", "check_file"] + args)
        return result.decode()

    def test_no_arguments(self):
        with self.assertRaises(subprocess.CalledProcessError):
            self.invoke([])

    def test_json(self):
        self.invoke([self.json_file, '--format', 'json'])

    def test_xml(self):
        self.invoke([self.xml_file, '--format', 'xml'])

    def test_html_output(self):
        result = self.invoke([self.json_file, '--format', 'json', '--output', 'html'])
        self.assertTrue(result.startswith('<!DOCTYPE html>'))

    def test_invalid_file(self):
        with self.assertRaises(subprocess.CalledProcessError):
            self.invoke([self.json_file, '--format', 'xml'])


class CheckServerCli(TestCase):

    def invoke(self, args: list):
        result = subprocess.check_output(["python", "-m", "aas_test_engines", "check_server"] + args)
        return result.decode()

    def test_no_arguments(self):
        with self.assertRaises(subprocess.CalledProcessError):
            self.invoke([])

    def test_suite_ambiguous(self):
        with self.assertRaises(subprocess.CalledProcessError):
            self.invoke(["https://localhost:5000", "RepositoryServiceSpecification/SSP-002", "--dry"])

    def test_dry(self):
        self.invoke(["https://localhost:5000", "https://admin-shell.io/aas/API/3/0/AssetAdministrationShellRepositoryServiceSpecification/SSP-002", "--dry"])
