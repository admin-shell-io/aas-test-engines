from typing import Optional, Tuple, Dict, List
from dataclasses import dataclass, field
from aas_test_engines.result import AasTestResult, Level
from enum import Enum
import datetime

from .model import Environment
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


class TypeOfTelephone(Enum):
    Office = "0173-1#07-AAS754#001"
    OfficeMobile = "0173-1#07-AAS755#001"
    Secretary = "0173-1#07-AAS756#001"
    Substitute = "0173-1#07-AAS757#001"
    Home = "0173-1#07-AAS758#001"
    PrivateMobile = "0173-1#07-AAS759#001"


@dataclass
class Phone:
    telephone_number: LangString = field(
        metadata={
            "semantic_id": "0173-1#02-AAO136#002",
        }
    )
    type_of_telephone: Optional[TypeOfTelephone] = field(metadata={"semantic_id": "0173-1#02-AAO137#003"})
    available_time: Optional[LangString] = field(
        metadata={
            "semantic_id": "https://admin-shell.io/zvei/nameplate/1/0/ContactInformations/ContactInformation/AvailableTime/",
        }
    )


class TypeOfFaxNumber(Enum):
    Office = "0173-1#07-AAS754#001"
    Secretary = "0173-1#07-AAS756#001"
    Home = "0173-1#07-AAS758#001"


@dataclass
class Fax:
    fax_number: LangString = field(
        metadata={
            "semantic_id": "0173-1#02-AAO195#002",
        }
    )
    type_of_fax_number: Optional[TypeOfFaxNumber] = field(
        metadata={
            "semantic_id": "0173-1#02-AAO196#003",
        }
    )


class TypeOfEmailAddress(Enum):
    Office = "0173-1#07-AAS754#001"
    Secretary = "0173-1#07-AAS756#001"
    Substitute = "0173-1#07-AAS757#001"
    Home = "0173-1#07-AAS758#001"


@dataclass
class Email:
    email_address: str = field(
        metadata={
            "semantic_id": "0173-1#02-AAO198#002",
        }
    )
    public_key: Optional[LangString] = field(
        metadata={
            "semantic_id": "0173-1#02-AAO200#002",
        }
    )
    type_of_email_address: Optional[TypeOfEmailAddress] = field(metadata={"semantic_id": "0173-1#02-AAO199#003"})
    type_of_public_key: Optional[LangString] = field(metadata={"semantic_id": "0173-1#02-AAO201#002"})


@dataclass
class IPCommunication:
    address_of_additional_link: str = field(
        metadata={
            "semantic_id": "0173-1#02-AAQ326#002",
        }
    )
    type_of_communication: Optional[str] = field(
        metadata={
            "semantic_id": "https://admin-shell.io/zvei/nameplate/1/0/ContactInformations/ContactInformation/IPCommunication/TypeOfCommunication",
        }
    )
    available_time: Optional[str] = field(
        metadata={
            "semantic_id": "https://admin-shell.io/zvei/nameplate/1/0/ContactInformations/ContactInformation/AvailableTime/",
        }
    )


@dataclass
class ContactInformation:
    role_of_contact_person: Optional[RoleOfContactPerson] = field(
        metadata={
            "semantic_id": "0173-1#02-AAO204#003",
        }
    )
    national_code: Optional[LangString] = field(
        metadata={
            "semantic_id": "0173-1#02-AAO134#002",
        }
    )
    language: Optional[List[str]] = field(
        metadata={
            "semantic_id": "https://admin-shell.io/zvei/nameplate/1/0/ContactInformations/ContactInformation/Language",
        }
    )
    time_zone: Optional[str] = field(
        metadata={
            "semantic_id": "https://admin-shell.io/zvei/nameplate/1/0/ContactInformations/ContactInformation/TimeZone",
        }
    )
    # TODO: Add hint: "mandatory property according to EU MachineDirective 2006/42/EC."
    city_town: Optional[LangString] = field(
        metadata={
            "semantic_id": "0173-1#02-AAO132#002",
        }
    )
    company: Optional[LangString] = field(
        metadata={
            "semantic_id": "0173-1#02-AAW001#001",
        }
    )
    department: Optional[LangString] = field(
        metadata={
            "semantic_id": "0173-1#02-AAO127#003",
        }
    )
    phone: Optional[Phone] = field(
        metadata={
            "semantic_id": "https://admin-shell.io/zvei/nameplate/1/0/ContactInformations/ContactInformation/Phone",
        }
    )
    fax: Optional[Fax] = field(
        metadata={
            "semantic_id": "0173-1#02-AAQ834#005",
        }
    )
    email: Optional[Email] = field(
        metadata={
            "semantic_id": "0173-1#02-AAQ836#005",
        }
    )
    ipc_communication: Optional[List[IPCommunication]] = field(
        metadata={
            "semantic_id": "https://admin-shell.io/zvei/nameplate/1/0/ContactInformations/ContactInformation/IPCommunication",
        }
    )
    street: Optional[LangString] = field(
        metadata={
            "semantic_id": "0173-1#02-AAO128#002",
        }
    )
    zip_code: Optional[LangString] = field(
        metadata={
            "semantic_id": "0173-1#02-AAO129#002",
        }
    )
    po_box: Optional[LangString] = field(
        metadata={
            "semantic_id": "0173-1#02-AAO130#002",
        }
    )
    zip_code_of_po_box: Optional[LangString] = field(
        metadata={
            "semantic_id": "0173-1#02-AAO131#002",
        }
    )
    state_country: Optional[LangString] = field(
        metadata={
            "semantic_id": "0173-1#02-AAO133#002",
        }
    )
    name_of_contact: Optional[LangString] = field(
        metadata={
            "semantic_id": "0173-1#02-AAO205#002",
        }
    )
    first_name: Optional[LangString] = field(
        metadata={
            "semantic_id": "0173-1#02-AAO206#002",
        }
    )
    middle_name: Optional[LangString] = field(
        metadata={
            "semantic_id": "0173-1#02-AAO207#002",
        }
    )
    title: Optional[LangString] = field(
        metadata={
            "semantic_id": "0173-1#02-AAO208#003",
        }
    )
    academic_title: Optional[LangString] = field(
        metadata={
            "semantic_id": "0173-1#02-AAO209#003",
        }
    )
    further_details_of_contact: Optional[LangString] = field(
        metadata={
            "semantic_id": "0173-1#02-AAO210#002",
        }
    )
    address_of_additional_link: Optional[str] = field(
        metadata={
            "semantic_id": "] 0173-1#02-AAQ326#002",
        }
    )


@dataclass
@template("https://admin-shell.io/zvei/nameplate/1/0/ContactInformations")
class ContactInformations:
    contact_information: List[ContactInformation] = field(
        metadata={
            "semantic_id": "https://admin-shell.io/zvei/nameplate/1/0/ContactInformations/ContactInformation",
        }
    )


@dataclass
@template("https://admin-shell.io/zvei/nameplate/2/0/Nameplate")
class DigitalNameplate:
    uri_of_the_product: str = field(
        metadata={
            "semantic_id": "0173-1#02-AAY811#001",
        }
    )
    manufacturer_name: LangString = field(
        metadata={
            "semantic_id": "0173-1#02-AAO677#002",
        }
    )
    manufacturer_product_designation: LangString = field(
        metadata={
            "semantic_id": "0173-1#02-AAW338#001",
        }
    )
    contact_information: ContactInformation = field(
        metadata={
            "semantic_id": "https://admin-shell.io/zvei/nameplate/1/0/ContactInformations/ContactInformation",
        }
    )
    manufacturer_product_root: Optional[LangString] = field(
        metadata={
            "semantic_id": "0173-1#02-AAU732#001",
        }
    )
    manufacturer_product_family: Optional[LangString] = field(
        metadata={
            "semantic_id": "0173-1#02-AAU731#001",
        }
    )
    manufacturer_product_type: Optional[LangString] = field(
        metadata={
            "semantic_id": "0173-1#02-AAO057#002",
        }
    )
    order_code_of_manufacturer: Optional[LangString] = field(
        metadata={
            "semantic_id": "0173-1#02-AAO227#002",
        }
    )
    product_article_number_of_manufacturer: Optional[LangString] = field(
        metadata={"semantic_id": "0173-1#02-AAO676#003"}
    )
    serial_number: Optional[str] = field(
        metadata={
            "semantic_id": "0173-1#02-AAM556#002",
        }
    )
    year_of_construction: str = field(
        metadata={
            "semantic_id": "0173-1#02-AAP906#001",
        }
    )
    date_of_manufacture: Optional[datetime.date] = field(
        metadata={
            "semantic_id": "0173-1#02-AAR972#002",
        }
    )
    hardware_version: Optional[LangString] = field(
        metadata={
            "semantic_id": "0173-1#02-AAN270#002",
        }
    )
    firmware_version: Optional[LangString] = field(
        metadata={
            "semantic_id": "0173-1#02-AAM985#002",
        }
    )
    software_version: Optional[LangString] = field(
        metadata={
            "semantic_id": "0173-1#02-AAM737#002",
        }
    )
    country_of_origin: Optional[str] = field(metadata={"semantic_id": "0173-1#02-AAO259#004"})
    # TODO: company_logo, markings, asset_specific_properties

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


def supported_templates() -> List[str]:
    return list(templates.keys())
