from typing import List

class Resolver:

    def __init__(self, root_document: any):
        self.root_document = root_document

    def lookup(self, pointer: str):
        if pointer.startswith('#/'):
            pointer = pointer[2:]
        components = pointer.split("/")
        return self._lookup(components, self.root_document)

    def _lookup(self, components: List[str], data: any):
        if not components:
            return data
        key = components.pop(0)
        return self._lookup(components, data[key])