from .parse import StringFormattedValue, abstract

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class Identifier(StringFormattedValue):
    min_length = 1


class BcpLangString(StringFormattedValue):
    min_length = 1


class NonEmptyString(StringFormattedValue):
    min_length = 1


class VersionString(StringFormattedValue):
    min_length = 1


class RevisionString(StringFormattedValue):
    min_length = 1


class DateTimeUtc(StringFormattedValue):
    min_length = 1


class Duration(StringFormattedValue):
    min_length = 1


class Blob(StringFormattedValue):
    min_length = 1


class ContentType(StringFormattedValue):
    min_length = 1


class Path(StringFormattedValue):
    min_length = 1


class DataType(StringFormattedValue):
    min_length = 1


class ValueType(StringFormattedValue):
    min_length = 1


class MessageTopic(StringFormattedValue):
    min_length = 1


class IdShort(StringFormattedValue):
    min_length = 1


class LangStringTextType(NonEmptyString):
    min_length = 1


# Reference


class KeyType(Enum):
    AnnotatedRelationshipElement = 'AnnotatedRelationshipElement'
    AssetAdministrationShell = 'AssetAdministrationShell'
    BasicEventElement = 'BasicEventElement'
    Blob = 'Blob'
    Capability = 'Capability'
    ConceptDescription = 'ConceptDescription'
    DataElement = 'DataElement'
    Entity = 'Entity'
    EventElement = 'EventElement'
    File = 'File'
    FragmentReference = 'FragmentReference'
    GlobalReference = 'GlobalReference'
    Identifiable = 'Identifiable'
    MultiLanguageProperty = 'MultiLanguageProperty'
    Operation = 'Operation'
    Property = 'Property'
    Range = 'Range'
    Referable = 'Referable'
    ReferenceElement = 'ReferenceElement'
    RelationshipElement = 'RelationshipElement'
    Submodel = 'Submodel'
    SubmodelElement = 'SubmodelElement'
    SubmodelElementCollection = 'SubmodelElementCollection'
    SubmodelElementList = 'SubmodelElementList'


@dataclass
class Key:
    type: KeyType
    value: NonEmptyString


class ReferenceType(Enum):
    ExternalReference = 'ExternalReference'
    ModelReference = 'ModelReference'


@dataclass
class Reference:
    type: ReferenceType
    referred_semantic_id: Optional["Reference"]
    keys: Optional[List[Key]]

# Section 5.3.2: Common Attributes

# HasDataSpecification


@dataclass
class DataSpecificationContent:
    pass


@dataclass
class EmbeddedDataSpecification:
    data_specification: Reference
    data_specification_content: DataSpecificationContent


@dataclass
class HasDataSpecification:
    embedded_data_specifications: Optional[List[EmbeddedDataSpecification]]


@dataclass
class ValueReferencePair:
    value: NonEmptyString
    value_id: NonEmptyString


@dataclass
class ValueList:
    value_reference_pairs: List[ValueReferencePair]


class DataTypeIec61360(Enum):
    BLOB = 'BLOB'
    BOOLEAN = 'BOOLEAN'
    DATE = 'DATE'
    FILE = 'FILE'
    HTML = 'HTML'
    INTEGER_COUNT = 'INTEGER_COUNT'
    INTEGER_CURRENCY = 'INTEGER_CURRENCY'
    INTEGER_MEASURE = 'INTEGER_MEASURE'
    IRDI = 'IRDI'
    IRI = 'IRI'
    RATIONAL = 'RATIONAL'
    RATIONAL_MEASURE = 'RATIONAL_MEASURE'
    REAL_COUNT = 'REAL_COUNT'
    REAL_CURRENCY = 'REAL_CURRENCY'
    REAL_MEASURE = 'REAL_MEASURE'
    STRING = 'STRING'
    STRING_TRANSLATABLE = 'STRING_TRANSLATABLE'
    TIME = 'TIME'
    TIMESTAMP = 'TIMESTAMP'


@dataclass
class LevelType:
    min: bool
    nom: bool
    typ: bool
    max: bool


@dataclass
class DataSpecificationIec61360(DataSpecificationContent):
    preferred_name: List[NonEmptyString]
    short_name: Optional[List[NonEmptyString]]
    unit: Optional[List[NonEmptyString]]
    unit_id: Optional[List[Reference]]
    source_of_definition: Optional[NonEmptyString]
    symbol: Optional[NonEmptyString]
    data_type: Optional[DataTypeIec61360]
    definition: Optional[List[NonEmptyString]]
    value_format: Optional[NonEmptyString]
    value_list: Optional[ValueList]
    value: Optional[NonEmptyString]
    level_type: Optional[LevelType]


# Identifiable

@dataclass
class AbstractLangString:
    language: BcpLangString
    text: NonEmptyString


@dataclass
class HasSemantics:
    semantic_id: Optional[Reference]
    supplemental_semantic_ids: Optional[List[Reference]]


@dataclass
class Extension(HasSemantics):
    name: NonEmptyString
    value_type: Optional[NonEmptyString]
    value: Optional[str]
    referes_to: Optional[List[Reference]]


@dataclass
class HasExtensions:
    extensions: Optional[List[Extension]]


@dataclass
class Referable(HasExtensions):
    # TODO: category is deprecated
    category: Optional[NonEmptyString]
    id_short: Optional[IdShort]
    display_name: Optional[List[AbstractLangString]]
    description: Optional[List[AbstractLangString]]


class ModellingKind(Enum):
    Instance = "Instance"
    Template = "Template"


@dataclass
class HasKind:
    kind: Optional[ModellingKind]


@dataclass
class AdministrativeInformation(HasDataSpecification):
    version: Optional[VersionString]
    revision: Optional[RevisionString]
    creator: Optional[Reference]
    template_id: Optional[Identifier]


@dataclass
class Identifiable(Referable):
    administration: Optional[AdministrativeInformation]
    id: Identifier


@dataclass
class SpecificAssetId(HasSemantics):
    name: NonEmptyString
    value: Identifier
    external_subject_id: Optional[Reference]


# Qualifiable


class QualifierKind(Enum):
    ConceptQualifier = 'ConceptQualifier'
    TemplateQualifier = 'TemplateQualifier'
    ValueQualifier = 'ValueQualifier'


@dataclass
class Qualifier(HasSemantics):
    kind: Optional[QualifierKind]
    type: NonEmptyString
    value_type: NonEmptyString
    value: Optional[str]
    value_id: Optional[Reference]


@dataclass
class Qualifiable:
    qualifiers: Optional[List[Qualifier]]


# Submodel Elements


@dataclass
@abstract
class SubmodelElement(Referable, HasSemantics, Qualifiable, HasDataSpecification):
    pass


@dataclass
@abstract
class DataElement(SubmodelElement):
    pass


@dataclass
class RelationshipElement(SubmodelElement):
    first: Reference
    second: Reference


@dataclass
class AnnotatedRelationshipElement(RelationshipElement):
    annotations: Optional[List[DataElement]]


@dataclass
class EventElement(SubmodelElement):
    pass


class StateOfEvent(Enum):
    OFF = 'off'
    ON = 'on'


class Direction(Enum):
    INPUT = 'input'
    OUTPUT = 'output'


@dataclass
class BasicEventElement(EventElement):
    observed: Reference
    direction: Direction
    state: StateOfEvent
    message_topic: Optional[MessageTopic]
    message_broker: Optional[Reference]
    last_update: Optional[DateTimeUtc]
    min_interval: Optional[Duration]
    max_interval: Optional[Duration]


@dataclass
class Blob(DataElement):
    value: Optional[Blob]
    content_type: ContentType


@dataclass
class Capability(SubmodelElement):
    pass


class EntityType(Enum):
    CoManagedEntity = 'CoManagedEntity'
    SelfManagedEntity = 'SelfManagedEntity'


@dataclass
class Entity(SubmodelElement):
    statements: Optional[List[SubmodelElement]]
    entity_type: EntityType
    global_asset_id: Optional[Identifier]
    specific_asset_id: Optional[List[SpecificAssetId]]


@dataclass
class File(DataElement):
    value: Optional[Path]
    content_type: ContentType


class GloballyIdentifiables(Enum):
    GlobalReference = 'GlobalReference'
    AssetAdministrationShell = 'AssetAdministrationShell'
    ConceptDescription = 'ConceptDescription'
    Identifiable = 'Identifiable'
    Submodel = 'Submodel'


class GenericGloballyIdentifiables(Enum):
    GlobalReference = 'GlobalReference'


class AasIdentifiables(Enum):
    AssetAdministrationShell = 'AssetAdministrationShell'
    ConceptDescription = 'ConceptDescription'
    Identifiable = 'Identifiable'
    Submodel = 'Submodel'


@dataclass
class MultiLanguageProperty(DataElement):
    value: Optional[List[AbstractLangString]]
    value_id: Optional[Reference]


@dataclass
class OperationVariable:
    value: SubmodelElement


@dataclass
class Operation(SubmodelElement):
    input_variables: Optional[List[OperationVariable]]
    output_variables: Optional[List[OperationVariable]]
    inoutput_variables: Optional[List[OperationVariable]]


@dataclass
class Property(DataElement):
    value_type: ValueType
    value: Optional[str]
    type: Optional[str]
    value_id: Optional[Reference]


@dataclass
class Range(DataElement):
    value_type: NonEmptyString
    min: Optional[str]
    max: Optional[str]


@dataclass
class ReferenceElement(DataElement):
    value: Optional[Reference]


@dataclass
class SubmodelElementCollection(SubmodelElement):
    value: Optional[List[SubmodelElement]]


class AasSubmodelElements(Enum):
    AnnotatedRelationshipElement = 'AnnotatedRelationshipElement'
    BasicEventElement = 'BasicEventElement'
    Blob = 'Blob'
    Capability = 'Capability'
    DataElement = 'DataElement'
    Entity = 'Entity'
    EventElement = 'EventElement'
    File = 'File'
    MultiLanguageProperty = 'MultiLanguageProperty'
    Operation = 'Operation'
    Property = 'Property'
    Range = 'Range'
    ReferenceElement = 'ReferenceElement'
    RelationshipElement = 'RelationshipElement'
    SubmodelElement = 'SubmodelElement'
    SubmodelElementCollection = 'SubmodelElementCollection'
    SubmodelElementList = 'SubmodelElementList'


@dataclass
class SubmodelElementList(SubmodelElement):
    order_relevant: Optional[bool]
    semantic_id_list_element: Optional[Reference]
    type_value_list_element: AasSubmodelElements
    value_type_list_element: Optional[DataType]
    value: Optional[List[SubmodelElement]]


# Environment

class AssetKind(Enum):
    INSTANCE = 'Instance'
    NOT_APPLICABLE = 'NotApplicable'
    TYPE = 'Type'


@dataclass
class Resource:
    path: Path
    content_type: Optional[ContentType]


@dataclass
class AssetInformation:
    asset_kind: AssetKind
    global_asset_id: Optional[Identifier]
    specific_asset_ids: Optional[List[SpecificAssetId]]
    asset_type: Optional[Identifier]
    default_thumbnail: Optional[Resource]


@dataclass
class AssetAdministrationShell(Identifiable, HasDataSpecification):
    derived_from: Optional[Reference]
    asset_information: AssetInformation
    submodels: Optional[List[Reference]]


@dataclass
class Submodel(Identifiable, HasKind, HasSemantics, Qualifiable, HasDataSpecification):
    submodel_elements: Optional[List[SubmodelElement]]


@dataclass
class ConceptDescription(Identifiable, HasDataSpecification):
    is_case_of: Optional[List[Reference]]


@dataclass
class Environment:
    asset_administration_shells: Optional[List[AssetAdministrationShell]]
    submodels: Optional[List[Submodel]]
    concept_descriptions: Optional[List[ConceptDescription]]
