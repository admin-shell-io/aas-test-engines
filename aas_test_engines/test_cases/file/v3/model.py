from .parse import StringFormattedValue, abstract, CheckConstraintException

from dataclasses import dataclass
from typing import List, Optional, Set
from enum import Enum
from .data_types import _is_bounded_integer

# 5.3.11.2 Primitive Data Types


class BlobString(StringFormattedValue):
    min_length = 1


class ContentType(StringFormattedValue):
    min_length = 1
    max_length = 100


class IdentifierString(StringFormattedValue):
    min_length = 1
    max_length = 2000


class LabelString(StringFormattedValue):
    min_length = 1
    max_length = 64


class MessageTopicString(StringFormattedValue):
    min_length = 1
    max_length = 255


class MultiLanguageNameType(StringFormattedValue):
    min_length = 1
    max_length = 128
    # TODO: bcp lang string


class MultiLanguageTextType(StringFormattedValue):
    min_length = 1
    max_length = 1023


class NameTypeString(StringFormattedValue):
    min_length = 1
    max_length = 128
    pattern = r"[a-zA-Z][a-zA-Z0-9_]*"


class Path(StringFormattedValue):
    min_length = 1
    max_length = 2048


class RevisionString(StringFormattedValue):
    min_length = 1
    max_length = 4
    pattern = r"(0|[1-9][0-9]*)"


QualifierType = NameTypeString


class VersionString(StringFormattedValue):
    min_length = 1
    max_length = 4
    pattern = r"(0|[1-9][0-9]*)"


class ValueDataType(StringFormattedValue):
    pass


class DateTimeUtc(StringFormattedValue):
    min_length = 1


class Duration(StringFormattedValue):
    min_length = 1


class DataType(StringFormattedValue):
    min_length = 1


class ValueType(StringFormattedValue):
    min_length = 1


class DataTypeDefXsd(Enum):
    anyURI = "xs:anyURI"
    base64Binary = "xs:base64Binary"
    boolean = "xs:boolean"
    byte = "xs:byte"
    date = "xs:date"
    dateTime = "xs:dateTime"
    decimal = "xs:decimal"
    double = "xs:double"
    duration = "xs:duration"
    float = "xs:float"
    gDay = "xs:gDay"
    gMonth = "xs:gMonth"
    gMonthDay = "xs:gMonthDay"
    gYear = "xs:gYear"
    gYearMonth = "xs:gYearMonth"
    hexBinary = "xs:hexBinary"
    int = "xs:int"
    integer = "xs:integer"
    long = "xs:long"
    negativeInteger = "xs:negativeInteger"
    nonNegativeInteger = "xs:nonNegativeInteger"
    nonPositiveInteger = "xs:nonPositiveInteger"
    positiveInteger = "xs:positiveInteger"
    short = "xs:short"
    string = "xs:string"
    time = "xs:time"
    unsignedByte = "xs:unsignedByte"
    unsignedInt = "xs:unsignedInt"
    unsignedLong = "xs:unsignedLong"
    unsignedShort = "xs:unsignedShort"


# 5.3.10.2 Reference

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

    def matches(self, obj) -> bool:
        return obj.__class__.__name__ == self.value


AasSubmodelElements = {
    KeyType.AnnotatedRelationshipElement,
    KeyType.BasicEventElement,
    KeyType.Blob,
    KeyType.Capability,
    KeyType.DataElement,
    KeyType.Entity,
    KeyType.EventElement,
    KeyType.File,
    KeyType.MultiLanguageProperty,
    KeyType.Operation,
    KeyType.Property,
    KeyType.Range,
    KeyType.ReferenceElement,
    KeyType.RelationshipElement,
    KeyType.SubmodelElement,
    KeyType.SubmodelElementCollection,
    KeyType.SubmodelElementList,
}

GenericGloballyIdentifiables = {
    KeyType.GlobalReference,
}

AasIdentifiables = {
    KeyType.AssetAdministrationShell,
    KeyType.ConceptDescription,
    KeyType.Identifiable,
    KeyType.Submodel,
}

GenericFragmentKeys = {
    KeyType.FragmentReference,
}

GloballyIdentifiables = AasIdentifiables | GenericGloballyIdentifiables

FragmentKeys = GenericFragmentKeys | AasSubmodelElements


@dataclass
class Key:
    type: KeyType
    value: IdentifierString

    def __eq__(self, other: "Key") -> bool:
        return self.type == other.type and self.value == other.value

    def __str__(self):
        return self.value.raw_value


class ReferenceType(Enum):
    ExternalReference = 'ExternalReference'
    ModelReference = 'ModelReference'


@ dataclass
class Reference:
    type: ReferenceType
    referred_semantic_id: Optional["Reference"]
    keys: Optional[List[Key]]

    def check_aasd_121(self):
        """
        Constraint AASd-121: For References, the value of Key/type of the first key of Reference/keys shall be one
        of GloballyIdentifiables.
        """
        if not self.keys:
            return
        if self.keys[0].type not in GloballyIdentifiables:
            raise CheckConstraintException("Constraint AASd-121 violated: first key must one of GloballyIdentifiables")

    def check_aasd_122(self):
        """
        Constraint AASd-122: For external references, i.e. References with Reference/type = ExternalReference, the
        value of Key/type of the first key of Reference/keys shall be one of GenericGloballyIdentifiables.
        """
        if self.type != ReferenceType.ExternalReference or self.keys is None:
            return
        if self.keys[0].type not in GenericGloballyIdentifiables:
            raise CheckConstraintException("Constraint AASd-122 violated: first key must one of GenericGloballyIdentifiables")

    def check_aasd_123(self):
        """
        Constraint AASd-123: For model references, i.e. References with Reference/type = ModellReference, the
        value of Key/type of the first key of Reference/keys shall be one of AasIdentifiables.
        """
        if self.type != ReferenceType.ModelReference or self.keys is None:
            return
        if self.keys[0].type not in AasIdentifiables:
            raise CheckConstraintException("Constraint AASd-123 violated: first key must one of AasIdentifiables")

    def check_aasd_124(self):
        """
        Constraint AASd-124: For external references, i.e. References with Reference/type = ExternalReference, the
        last key of Reference/keys shall be either one of GenericGloballyIdentifiables or one of
        GenericFragmentKeys.
        """
        if self.type != ReferenceType.ExternalReference or self.keys is None:
            return
        if self.keys[-1].type not in GenericGloballyIdentifiables and self.keys[-1].type not in GenericFragmentKeys:
            raise CheckConstraintException("Constraint AASd-124 violated: last key must one of GenericGloballyIdentifiables or GenericFragmentKeys")

    def check_aasd_125(self):
        """
        Constraint AASd-125: For model references, i.e. References with Reference/type = ModelReference with
        more than one key in Reference/keys, the value of Key/type of each of the keys following the first key of
        Reference/keys shall be one of FragmentKeys.
        """
        if self.type != ReferenceType.ModelReference or self.keys is None:
            return
        for idx, key in enumerate(self.keys[1:]):
            if key.type not in FragmentKeys:
                raise CheckConstraintException(f"Constraint AASd-125 violated: key {idx} must be a FragmentKey")

    def check_aasd_126(self):
        """
        Constraint AASd-126: For model references, i.e. References with Reference/type = ModelReference with
        more than one key in Reference/keys, the value of Key/type of the last Key in the reference key chain may
        be one of GenericFragmentKeys or no key at all shall have a value out of GenericFragmentKeys.
        """
        if self.type != ReferenceType.ModelReference or self.keys is None or len(self.keys) <= 1:
            return
        for idx, key in enumerate(self.keys[:-1]):
            if key.type in GenericFragmentKeys:
                raise CheckConstraintException(f"Constraint AASd-126 violated: key {idx} must not be a GenericFragmentKey")

    def check_aasd_127(self):
        """
        Constraint AASd-127: For model references, i.e. References with Reference/type = ModelReference with
        more than one key in Reference/keys, a key with Key/type FragmentReference shall be preceded by a key
        with Key/type File or Blob. All other Asset Administration Shell fragments, i.e. Key/type values out of
        AasSubmodelElements, do not support fragments.
        """
        if self.type != ReferenceType.ModelReference or self.keys is None or len(self.keys) <= 1:
            return
        for idx, key in enumerate(self.keys):
            if key.type == KeyType.FragmentReference and idx >= 1:
                if self.keys[idx-1].type not in {KeyType.File, KeyType.Blob}:
                    raise CheckConstraintException(f"Constraint AASd-127 violated: key {idx} must be preceded by File or Blob")

    def check_aasd_128(self):
        """
        Constraint AASd-128: For model references, i.e. References with Reference/type = ModelReference, the
        Key/value of a Key preceded by a Key with Key/type=SubmodelElementList is an integer number denoting
        the position in the array of the submodel element list. 
        """
        if self.type != ReferenceType.ModelReference or self.keys is None:
            return
        for idx, key in enumerate(self.keys):
            if key.type == KeyType.SubmodelElementList and idx < len(self.keys)-1:
                if not _is_bounded_integer(self.keys[idx+1].value.raw_value, 0, float('inf')):
                    raise CheckConstraintException(f"Constraint AASd-128 violated: key {idx} must be followed by an integer")

    def __eq__(self, other: "Reference") -> bool:
        if self.type != other.type:
            return False
        if len(self.keys) != len(other.keys):
            return False
        for x, y in zip(self.keys, other.keys):
            if x != y:
                return False
        return True

    def __str__(self) -> str:
        result = self.type.value
        if self.keys:
            result += "/".join([str(key) for key in self.keys])
        return result

# 5.3.2.3 Has Data Specification


@ dataclass
class DataSpecificationContent:
    pass


@ dataclass
class EmbeddedDataSpecification:
    data_specification: Reference
    data_specification_content: DataSpecificationContent


@ dataclass
class HasDataSpecification:
    embedded_data_specifications: Optional[List[EmbeddedDataSpecification]]


@ dataclass
class ValueReferencePair:
    value: IdentifierString
    value_id: Reference


@ dataclass
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


@ dataclass
class LevelType:
    min: bool
    nom: bool
    typ: bool
    max: bool


class NonEmptyString(StringFormattedValue):
    min_length = 1


@ dataclass
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

@ dataclass
class MultiLanguageNameType:
    language: MultiLanguageNameType
    text: MultiLanguageTextType

# 5.3.2.6 Has Semantics


@ dataclass
class HasSemantics:
    # TODO: Note: it is recommended to use an external reference
    semantic_id: Optional[Reference]
    # TODO: Note: it is recommended to use an external reference
    supplemental_semantic_ids: Optional[List[Reference]]

    def check_aasd_118(self):
        """
        Constraint AASd-118: If a supplemental semantic ID
        (HasSemantics/supplementalSemanticId) is defined, there shall also be a main
        semantic ID (HasSemantics/semanticId)
        """
        if self.supplemental_semantic_ids is not None and self.semantic_id is None:
            raise CheckConstraintException("AASd-118 violated: supplementalSemanticId is given but semanticId is missing")

# 5.3.2.4 Extensions


@ dataclass
class Extension(HasSemantics):
    name: NameTypeString
    # TODO: default: xs:string
    value_type: Optional[DataTypeDefXsd]
    value: Optional[ValueDataType]
    # TODO: must be a model reference
    refers_to: Optional[List[Reference]]


@ dataclass
class HasExtensions:
    extensions: Optional[List[Extension]]

# 5.3.2.10 Referable


@ dataclass
class Referable(HasExtensions):
    # TODO: category is deprecated
    category: Optional[NameTypeString]
    id_short: Optional[NameTypeString]
    display_name: Optional[List[MultiLanguageNameType]]
    description: Optional[List[MultiLanguageNameType]]
    # TODO: Constraint AASd-002: idShort of Referables shall only feature letters, digits, underscore ("_");
    # starting mandatory with a letter, i.e. [a-zA-Z][a-zA-Z0-9_]*.

# 5.3.2.5 Has Kind


class ModellingKind(Enum):
    Instance = "Instance"
    Template = "Template"


@ dataclass
class HasKind:
    kind: Optional[ModellingKind]

# 5.3.2.2 Administrative Information


@ dataclass
class AdministrativeInformation(HasDataSpecification):
    version: Optional[VersionString]
    revision: Optional[RevisionString]
    creator: Optional[Reference]
    template_id: Optional[IdentifierString]

    def check_constraint_aasd_005(self):
        """
        Constraint AASd-005: If AdministrativeInformation/version is not specified,
        AdministrativeInformation/revision shall also be unspecified. This means that a revision
        requires a version. If there is no version, there is no revision. Revision is optional.
        """
        if self.revision is not None and self.version is None:
            raise CheckConstraintException("AASd-005 violated: version is given but no revision")

# 5.3.2.7 Identifiable


@ dataclass
class Identifiable(Referable):
    administration: Optional[AdministrativeInformation]
    id: IdentifierString


# 5.3.2.8 Qualifiable


class QualifierKind(Enum):
    ConceptQualifier = 'ConceptQualifier'
    TemplateQualifier = 'TemplateQualifier'
    ValueQualifier = 'ValueQualifier'


@ dataclass
class Qualifier(HasSemantics):
    # TODO: Default: ConceptQualifier
    kind: Optional[QualifierKind]
    type: QualifierType
    value_type: DataTypeDefXsd
    value: Optional[ValueDataType]
    # TODO: Note: it is recommended to use an external reference.
    value_id: Optional[Reference]

    def check_aasd_006(self):
        """
        Constraint AASd-006: If both, the value and the valueId of a Qualifier are present, the value
        needs to be identical to the value of the referenced coded value in Qualifier/valueId.
        => not checkable
        """
        pass

    def check_aasd_020(self):
        """
        Constraint AASd-020: The value of Qualifier/value shall be consistent with the data type as
        defined in Qualifier/valueType.
        """
        # TODO
        pass


@ dataclass
class Qualifiable:
    qualifiers: Optional[List[Qualifier]]

# 5.3.4 Asset Information


@ dataclass
class SpecificAssetId(HasSemantics):
    name: LabelString
    value: IdentifierString
    external_subject_id: Optional[Reference]

    def check_aasd_133(self):
        """
        Constraint AASd-133: SpecificAssetId/externalSubjectId shall be a global reference, i.e.
        Reference/type = ExternalReference.
        """
        if self.external_subject_id and self.external_subject_id.type != ReferenceType.ExternalReference:
            raise CheckConstraintException("Constraint AASd-133 violated: type must be ExternalReference")


@ dataclass
class Resource:
    path: Path
    content_type: Optional[ContentType]


class AssetKind(Enum):
    INSTANCE = 'Instance'
    NOT_APPLICABLE = 'NotApplicable'
    TYPE = 'Type'


@ dataclass
class AssetInformation:
    asset_kind: AssetKind
    global_asset_id: Optional[IdentifierString]
    specific_asset_ids: Optional[List[SpecificAssetId]]
    asset_type: Optional[IdentifierString]
    default_thumbnail: Optional[Resource]

    def check_aasd_131(self):
        """
        Constraint AASd-131: The globalAssetId or at least one specificAssetId shall be defined for
        AssetInformation.
        """
        if not self.global_asset_id and not self.specific_asset_ids:
            raise CheckConstraintException("Constraint AASd-131 violated: neither globalAssetId nor specificAssetIds given")

# 5.3.6 Submodel Element


@ dataclass
@ abstract
class SubmodelElement(Referable, HasSemantics, Qualifiable, HasDataSpecification):
    pass

# 5.3.7.6 Data Element


@ dataclass
@ abstract
class DataElement(SubmodelElement):

    def check_aasd_090(self):
        """
        Constraint AASd-090: for data elements, category (inherited by Referable) shall be one of
        the following values: CONSTANT, PARAMETER or VARIABLE. Default: VARIABLE
        """
        allowed_values = ["CONSTANT", "PARAMETER", "VARIABLE"]
        if self.category is not None and self.category.raw_value not in allowed_values:
            raise CheckConstraintException(f"Constraint AASd-090: category {self.category.raw_value} is not one of {allowed_values}")


# 5.3.7.15 Relationship Element

@ dataclass
class RelationshipElement(SubmodelElement):
    first: Reference
    second: Reference

# 5.3.7.2 Annotated Relationship Element


@ dataclass
class AnnotatedRelationshipElement(RelationshipElement):
    annotations: Optional[List[DataElement]]


# 5.3.7.8 Event Element

@ dataclass
class EventElement(SubmodelElement):
    pass

# 5.3.7.3 Basic Event Element


class StateOfEvent(Enum):
    OFF = 'off'
    ON = 'on'


class Direction(Enum):
    INPUT = 'input'
    OUTPUT = 'output'


@ dataclass
class BasicEventElement(EventElement):
    observed: Reference
    direction: Direction
    state: StateOfEvent
    message_topic: Optional[MessageTopicString]
    message_broker: Optional[Reference]
    last_update: Optional[DateTimeUtc]
    min_interval: Optional[Duration]
    max_interval: Optional[Duration]

    def check_observed(self):
        if self.observed.type != ReferenceType.ModelReference:
            raise CheckConstraintException("observed must be a model reference")

    def check_message_broker(self):
        if self.message_broker and self.message_broker.type != ReferenceType.ModelReference:
            raise CheckConstraintException("observed must be a model reference")

# 5.3.7.4 Blob


@ dataclass
class Blob(DataElement):
    value: Optional[BlobString]
    content_type: ContentType

# 5.3.7.5 Capability


@ dataclass
class Capability(SubmodelElement):
    pass


# 5.3.7.7 Entity

class EntityType(Enum):
    CoManagedEntity = 'CoManagedEntity'
    SelfManagedEntity = 'SelfManagedEntity'


@ dataclass
class Entity(SubmodelElement):
    statements: Optional[List[SubmodelElement]]
    entity_type: EntityType
    global_asset_id: Optional[IdentifierString]
    specific_asset_ids: Optional[List[SpecificAssetId]]

    def check_aasd_014(self):
        """
        Constraint AASd-014: Either the attribute globalAssetId or specificAssetId of an Entity must
        be set if Entity/entityType is set to "SelfManagedEntity". Otherwise, they do not exist.
        """
        if self.entity_type == EntityType.SelfManagedEntity:
            if self.global_asset_id is None and self.specific_asset_ids is None:
                raise CheckConstraintException("Constraint AASd-014 violated: entity is self-manged by neither globalAssetId nor specificAssetId are set")
        else:
            if self.global_asset_id or self.specific_asset_ids:
                raise CheckConstraintException("Constraint AASd-014 violated: entity is co-manged by either globalAssetId or specificAssetId are set")

# 5.3.7.9 File


@ dataclass
class File(DataElement):
    value: Optional[Path]
    content_type: ContentType


# 5.3.7.10 Multi Language Property


@ dataclass
class MultiLanguageProperty(DataElement):
    # TODO: MultiLanguageNameType ?
    value: Optional[List[MultiLanguageNameType]]
    # TODO: Note: it is recommended to use an external reference.
    value_id: Optional[Reference]

    def check_constraint_aasd_012(self):
        """
        Constraint AASd-012: if both the MultiLanguageProperty/value and the
        MultiLanguageProperty/valueId are present, the meaning must be the same for each string
        in a specific language, as specified in MultiLanguageProperty/valueId.
        => not checked
        """
        pass

# 5.3.7.11 Operation


@ dataclass
class OperationVariable:
    value: SubmodelElement


@ dataclass
class Operation(SubmodelElement):
    input_variables: Optional[List[OperationVariable]]
    output_variables: Optional[List[OperationVariable]]
    inoutput_variables: Optional[List[OperationVariable]]

    def _check_list(self, l: Optional[List[OperationVariable]], all_id_shorts: Set[str]):
        if l is None:
            return
        for i in l:
            if i.value.id_short is None:
                continue
            if i.value.id_short.raw_value in all_id_shorts:
                raise CheckConstraintException("Constraint AASd-134 violated: duplicate id short")
            all_id_shorts.add(i.value.id_short.raw_value)

    def check_aasd_134(self):
        """
        Constraint AASd-134: For an Operation, the idShort of all inputVariable/value,
        outputVariable/value, and inoutputVariable/value shall be unique.
        """
        all_id_shorts = set()
        self._check_list(self.input_variables, all_id_shorts)
        self._check_list(self.output_variables, all_id_shorts)
        self._check_list(self.inoutput_variables, all_id_shorts)

# 5.3.7.12 Property


@ dataclass
class Property(DataElement):
    value_type: DataTypeDefXsd
    value: Optional[ValueDataType]
    # TODO: Note: it is recommended to use an external reference.
    value_id: Optional[Reference]

    def check_aasd_007(self):
        """
        Constraint AASd-007: If both the Property/value and the Property/valueId are present, the
        value of Property/value needs to be identical to the value of the referenced coded value in
        Property/valueId.
        -> cannot check
        """
        pass

# 5.3.7.13 Range


@ dataclass
class Range(DataElement):
    value_type: DataTypeDefXsd
    min: Optional[ValueDataType]
    max: Optional[ValueDataType]

# 5.3.7.14 Reference Element


@ dataclass
class ReferenceElement(DataElement):
    value: Optional[Reference]


# 5.3.7.16 Submodel Element Collection

@ dataclass
class SubmodelElementCollection(SubmodelElement):
    value: Optional[List[SubmodelElement]]

# 5.3.7.17 Submodel Element List


@ dataclass
class SubmodelElementList(SubmodelElement):
    # TODO: default: true
    order_relevant: Optional[bool]
    # TODO: Note: it is recommended to use an external reference.
    semantic_id_list_element: Optional[Reference]
    type_value_list_element: Optional[KeyType]
    value_type_list_element: Optional[DataTypeDefXsd]
    value: Optional[List[SubmodelElement]]

    def check_type_value_list_element(self):
        if self.type_value_list_element not in AasSubmodelElements:
            raise CheckConstraintException("type_value_list_element must be a AasSubmodelElement")

    def check_aasd_107(self):
        """
        Constraint AASd-107: If a first level child element in a SubmodelElementList has a
        semanticId, it shall be identical to SubmodelElementList/semanticIdListElement.
        """
        if not self.value or not self.semantic_id:
            return
        for idx, el in enumerate(self.value):
            if not el.semantic_id:
                continue
            if el.semantic_id != self.semantic_id_list_element:
                raise CheckConstraintException(f"Constraint AASd-107 violated: Element {idx} has invalid semantic id {el.semantic_id}, should be {self.semantic_id_list_element}")

    def check_aasd_114(self):
        """
        Constraint AASd-114: If two first level child elements in a SubmodelElementList
        have a semanticId, they shall be identical.
        """
        if not self.value:
            return
        semantic_id = None
        for idx, el in enumerate(self.value):
            if not el.semantic_id:
                continue
            if semantic_id:
                if el.semantic_id != semantic_id:
                    raise CheckConstraintException(f"Constraint AASd-114 violated: Element {idx} must have semanticId {semantic_id}")
            else:
                semantic_id = el.semantic_id

    def check_aasd_115(self):
        """
        Constraint AASd-115: If a first level child element in a SubmodelElementList does
        not specify a semanticId, the value is assumed to be identical to
        SubmodelElementList/semanticIdListElement.
        -> not checked
        """
        pass

    def check_aasd_108(self):
        """
        Constraint AASd-108: All first level child elements in a SubmodelElementList shall
        have the same submodel element type as specified in
        SubmodelElementList/typeValueListElement.
        """
        if not self.value:
            return
        for idx, el in enumerate(self.value):
            if not self.type_value_list_element.matches(el):
                raise CheckConstraintException(f"Constraint AASd-108 violated: Element {idx} must be {self.type_value_list_element.value}")

    def check_aasd_109(self):
        """
        Constraint AASd-109: If SubmodelElementList/typeValueListElement is equal to
        Property or Range, SubmodelElementList/valueTypeListElement shall be set and
        all first level child elements in the SubmodelElementList shall have the value type
        as specified in SubmodelElementList/valueTypeListElement.
        """
        if not self.value:
            return
        for idx, el in enumerate(self.value):
            if isinstance(el, (Property, Range)):
                if self.value_type_list_element is None:
                    raise CheckConstraintException(f"Constraint AASd-109 violated: valueTypeListElement must be set since there are Properties/Ranges")
                if el.value_type != self.value_type_list_element:
                    raise CheckConstraintException(f"Constraint AASd-109 violated: value type of element {idx} does not match valueTypeListElement")


# 5.3.3 Asset Administration Shell


@ dataclass
class AssetAdministrationShell(Identifiable, HasDataSpecification):
    derived_from: Optional[Reference]
    asset_information: AssetInformation
    submodels: Optional[List[Reference]]

    def check_derived_from(self):
        if self.derived_from and self.derived_from.type != ReferenceType.ModelReference:
            raise CheckConstraintException("derivedFrom must be a model reference")

    def check_submodels(self):
        if self.submodels:
            for i in self.submodels:
                if i.type != ReferenceType.ModelReference:
                    raise CheckConstraintException("submodels must contain only model references")

# 5.3.5 Submodel


@ dataclass
class Submodel(Identifiable, HasKind, HasSemantics, Qualifiable, HasDataSpecification):
    submodel_elements: Optional[List[SubmodelElement]]


# 5.3.8 Concept Description

@ dataclass
class ConceptDescription(Identifiable, HasDataSpecification):
    # TODO: Note: it is recommended to use an external reference, i.e. Reference/type = ExternalReference.
    is_case_of: Optional[List[Reference]]

# 5.3.9 Environment


@ dataclass
class Environment:
    asset_administration_shells: Optional[List[AssetAdministrationShell]]
    submodels: Optional[List[Submodel]]
    concept_descriptions: Optional[List[ConceptDescription]]
