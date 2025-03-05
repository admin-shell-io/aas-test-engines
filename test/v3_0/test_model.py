from unittest import TestCase
from aas_test_engines.test_cases.v3_0.model import (
    Submodel,
    SubmodelElementCollection,
    SubmodelElementList,
    Property,
    IdentifierString,
    NameTypeString,
    File,
    Range,
)


class TestSubmodelElement(TestCase):

    def test_iterate(self):
        submodel = Submodel(
            embedded_data_specifications=None,
            qualifiers=None,
            semantic_id=None,
            supplemental_semantic_ids=None,
            kind=None,
            extensions=None,
            category=None,
            id_short=None,
            display_name=None,
            description=None,
            administration=None,
            id=IdentifierString("ID"),
            submodel_elements=[
                SubmodelElementList(
                    embedded_data_specifications=None,
                    qualifiers=None,
                    semantic_id=None,
                    supplemental_semantic_ids=None,
                    extensions=None,
                    category=None,
                    id_short=NameTypeString("SML"),
                    display_name=None,
                    description=None,
                    order_relevant=None,
                    semantic_id_list_element=None,
                    type_value_list_element=None,
                    value_type_list_element=None,
                    id_short_path=None,
                    value=[
                        File(
                            embedded_data_specifications=None,
                            qualifiers=None,
                            semantic_id=None,
                            supplemental_semantic_ids=None,
                            extensions=None,
                            category=None,
                            id_short=NameTypeString("File"),
                            display_name=None,
                            description=None,
                            id_short_path=None,
                            value=None,
                            content_type=None,
                        ),
                        SubmodelElementCollection(
                            embedded_data_specifications=None,
                            qualifiers=None,
                            semantic_id=None,
                            supplemental_semantic_ids=None,
                            extensions=None,
                            category=None,
                            id_short=NameTypeString("SMC"),
                            display_name=None,
                            description=None,
                            id_short_path=None,
                            value=[
                                Range(
                                    embedded_data_specifications=None,
                                    qualifiers=None,
                                    semantic_id=None,
                                    supplemental_semantic_ids=None,
                                    extensions=None,
                                    category=None,
                                    id_short=NameTypeString("Range"),
                                    display_name=None,
                                    description=None,
                                    id_short_path=None,
                                    value_type=None,
                                    min=None,
                                    max=None,
                                )
                            ],
                        ),
                    ],
                ),
                Property(
                    embedded_data_specifications=None,
                    qualifiers=None,
                    semantic_id=None,
                    supplemental_semantic_ids=None,
                    extensions=None,
                    category=None,
                    id_short=NameTypeString("Property"),
                    display_name=None,
                    description=None,
                    id_short_path=None,
                    value=None,
                    value_type=None,
                    value_id=None,
                ),
            ],
        )
        submodel.update_id_shorts()
        paths = [str(i.id_short_path) for i in submodel.elements()]
        self.assertEqual(len(paths), 5)
        self.assertEqual(paths[0], "ID:SML")
        self.assertEqual(paths[1], "ID:SML.0")
        self.assertEqual(paths[2], "ID:SML.1")
        self.assertEqual(paths[3], "ID:SML.1.Range")
        self.assertEqual(paths[4], "ID:Property")
