from typing import List, Set, Optional, Tuple, Dict
from .result import AasTestResult, Level
import zipfile
from xml.etree import ElementTree

NS_CONTENT_TYPES = "{http://schemas.openxmlformats.org/package/2006/content-types}"
NS_RELATIONSHIPS = "{http://schemas.openxmlformats.org/package/2006/relationships}"


def normpath(path: str) -> str:
    """
    Normalizes a given path.
    E.g. normpath('///a/../b/)') == '/b'
    This implementation is platform independent and behaves like os.normpath on a unix system.
    See https://docs.python.org/3/library/os.path.html#os.path.normpath for more details.
    """
    path = path.strip()
    if len(path) == 0:
        return ""
    result = []
    for token in path.split("/"):
        if token.strip() == "" or token == ".":
            continue
        if token == "..":
            if result:
                result.pop()
        else:
            result.append(token)
    if path.startswith("/"):
        return "/" + "/".join(result)
    else:
        return "/".join(result)


def splitpath(path: str) -> Tuple[str, str]:
    """
    Splits a path into a pair (head, tail)
    This implementation is platform independent and behaves like os.path.split on a unix system.
    See https://docs.python.org/3/library/os.path.html#os.path.split for more details.
    """
    prefix, _, suffix = path.rpartition("/")
    return prefix, suffix


class Relationship:

    def __init__(self, type: str, target: str) -> None:
        self.type = type
        self.target = target
        self.sub_rels: List[Relationship] = []

    def sub_rels_by_type(self, type: str) -> List["Relationship"]:
        return [i for i in self.sub_rels if i.type == type]

    def dump(self, indent=0):
        type_suffix = self.type.split("/")[-1]
        print("  " * indent + f"{self.target} [{type_suffix}]")
        for sub_rel in self.sub_rels:
            sub_rel.dump(indent + 1)


def _check_content_type(zipfile: zipfile.ZipFile) -> AasTestResult:
    content_types_xml = "[Content_Types].xml"
    result = AasTestResult(f"Checking {content_types_xml}")
    try:
        with zipfile.open(content_types_xml, "r") as f:
            content_types = ElementTree.parse(f)
            expected_tag = f"{NS_CONTENT_TYPES}Types"
            if content_types.getroot().tag != expected_tag:
                result.append(
                    AasTestResult(
                        f"root must have tag {expected_tag}, got {content_types.getroot().tag}",
                        Level.ERROR,
                    )
                )
    except KeyError:
        result.append(AasTestResult(f"{content_types_xml} not found", Level.ERROR))

    return result


def _scan_relationships(
    zipfile: zipfile.ZipFile,
    parent_rel: Relationship,
    dir: str,
    file: str,
    visited_targets: Set[str],
    deprecated_types: Dict[str, str],
) -> Optional[AasTestResult]:
    try:
        with zipfile.open(f"{dir}_rels/{file}.rels", "r") as f:
            relationships = ElementTree.parse(f).getroot()
    except KeyError:
        # file does not exist
        return None
    expected_tag = f"{NS_RELATIONSHIPS}Relationships"
    if relationships.tag != expected_tag:
        return AasTestResult(
            f"Invalid root tag {relationships.tag}, expected {expected_tag}",
            Level.ERROR,
        )

    if dir:
        result = AasTestResult(f"Checking relationships of {dir}{file}")
    else:
        result = AasTestResult(f"Checking root relationship")
    for idx, rel in enumerate(relationships):
        if rel.tag != f"{NS_RELATIONSHIPS}Relationship":
            result.append(AasTestResult(f"Invalid tag {rel.tag}", Level.ERROR))
            continue
        try:
            type = rel.attrib["Type"]
            target = rel.attrib["Target"]
        except KeyError as e:
            result.append(AasTestResult(f"Attribute {e} is missing", Level.ERROR))
            continue

        if type in deprecated_types:
            new_type = deprecated_types[type]
            result.append(
                AasTestResult(
                    f"Deprecated type {type}, considering as {new_type}",
                    level=Level.WARNING,
                )
            )
            type = new_type

        if target.startswith("/"):
            target = target[1:]
        else:
            target = dir + target
        target = normpath(target)

        sub_dir, file = splitpath(target)
        sub_rel = Relationship(type, target)
        result.append(AasTestResult(f"Relationship {sub_rel.target} is of type {sub_rel.type}", Level.INFO))
        parent_rel.sub_rels.append(sub_rel)
        if target in visited_targets:
            result.append(AasTestResult(f"Already checked {target}", Level.INFO))
            continue
        visited_targets.add(target)
        if target not in zipfile.namelist():
            result.append(AasTestResult(f"Relationship has non-existing target {target}", Level.ERROR))
            continue
        r = _scan_relationships(zipfile, sub_rel, sub_dir + "/", file, visited_targets, deprecated_types)
        if r:
            result.append(r)

    return result


def _check_relationships(
    zipfile: zipfile.ZipFile, root_rel: Relationship, deprecated_types: Dict[str, str]
) -> AasTestResult:
    result = AasTestResult("Checking relationships")
    visited_targets = set()
    r = _scan_relationships(zipfile, root_rel, "", "", visited_targets, deprecated_types)
    if r:
        result.append(r)
    else:
        result.append(AasTestResult(f"Root relationship does not exist", Level.ERROR))
    return result


def read_opc(
    zipfile: zipfile.ZipFile,
    root_rel: Relationship,
    root_result: AasTestResult,
    deprecated_types: Dict[str, str],
):
    root_result.append(_check_content_type(zipfile))
    if not root_result.ok():
        return
    root_result.append(_check_relationships(zipfile, root_rel, deprecated_types))
    if not root_result.ok():
        return
