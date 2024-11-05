from typing import Optional, Tuple, Dict, List
from dataclasses import dataclass, field
from aas_test_engines.result import AasTestResult, Level
from enum import Enum

from .model import Submodel, Environment
from .parse_submodel import parse_submodel, LangString
from .parse import check_constraints, CheckConstraintException
from .adapter import AdapterPath

templates = {}


def template(semantic_id: str):
    assert semantic_id not in templates

    def decorator(fn):
        templates[semantic_id] = fn
        return fn
    return decorator


class RoleOfContactPerson(Enum):
    Administrative = "0173-1#07-AAS927#001"
    Commercial = "0173-1#07-AAS928#001"
    Other = "0173-1#07-AAS929#001"
    HazardousGoods = "0173-1#07-AAS930#001"
    Technical = "0173-1#07-AAS931#001"


@dataclass
class ContactInformation:
    role_of_contact_person: Optional[RoleOfContactPerson] = field(metadata={
        "semantic_id": "0173-1#02-AAO204#003",
    })
    national_code: Optional[LangString] = field(metadata={
        "semantic_id": "0173-1#02-AAO134#002",
    })
    language: Optional[List[str]] = field(metadata={
        "semantic_id": "https://adminshell.io/zvei/nameplate/1/0/ContactInformations/ContactInformation/Language",
    })
    city_town: Optional[str] = field(metadata={
        "semantic_id": "https://adminshell.io/zvei/nameplate/1/0/ContactInformations/ContactInformation/TimeZone",
    })
    company: Optional[LangString] = field(metadata={
        "semantic_id": "0173-1#02-AAW001#001",
    })


@dataclass
@template("https://admin-shell.io/zvei/nameplate/1/0/ContactInformations")
class ContactInformations:
    contact_information: List[ContactInformation] = field(metadata={
        "semantic_id": "https://adminshell.io/zvei/nameplate/1/0/ContactInformations/ContactInformation",
    })


@dataclass
@template("https://admin-shell.io/zvei/nameplate/2/0/Nameplate")
class DigitalNameplate:
    uri_of_the_product: str = field(metadata={
        'semantic_id': '0173-1#02-AAY811#001',
    })
    manufacturer_name: LangString = field(metadata={
        'semantic_id': '0173-1#02-AAO677#002',
    })
    manufacturer_product_designation: LangString = field(metadata={
        'semantic_id': '0173-1#02-AAW338#001',
    })
    contact_information: ContactInformation = field(metadata={
        "semantic_id": "https://adminshell.io/zvei/nameplate/1/0/ContactInformations/ContactInformation",
    })
    serial_number: Optional[str] = field(metadata={
        "semantic_id": "0173-1#02-AAM556#002",
    })
    manufacturer_product_family: Optional[LangString] = field(metadata={
        "semantic_id": "0173-1#02-AAU732#001",
    })
    manufacturer_product_type: Optional[LangString] = field(metadata={
        "semantic_id": "0173-1#02-AAO057#002",
    })

    def check_family_or_type_present(self):
        if self.manufacturer_product_family is None and self.manufacturer_product_type is None:
            raise CheckConstraintException("Either ManufacturerProductFamily or ManufacturerProductType is required")


def parse_submodel_templates(root_result: AasTestResult, env: Environment):
    for submodel in env.submodels or []:
        if not submodel.semantic_id or not submodel.semantic_id.keys:
            continue
        sid = submodel.semantic_id.keys[0].value.raw_value
        sub_result = AasTestResult(f"Check submodel '{submodel.id}'")
        try:
            template = templates[sid]
        except KeyError:
            sub_result.append(AasTestResult(f"Unknown semantic id '{sid}'", level=Level.WARNING))
            continue
        sub_result.append(AasTestResult(f"Template: {template.__name__} ({sid})"))
        parsed_submodel = parse_submodel(sub_result, template, submodel)
        if sub_result.ok():
            check_constraints(parsed_submodel, sub_result, AdapterPath())
        root_result.append(sub_result)
