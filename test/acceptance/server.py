#! /usr/bin/env python3

from aas_test_engines import api

conf = api.ExecConf(
    server='http://aasx-server:5001/api/v3.0',
)

result_aas_repo, mat = api.execute_tests(conf, "https://admin-shell.io/aas/API/3/0/AssetAdministrationShellRepositoryServiceSpecification/SSP-002")
result_aas_repo.dump()
mat.print()

result_submodel_repo, mat = api.execute_tests(conf, "https://admin-shell.io/aas/API/3/0/SubmodelRepositoryServiceSpecification/SSP-002")
result_submodel_repo.dump()
mat.print()

assert result_aas_repo.ok()
assert result_submodel_repo.ok()
