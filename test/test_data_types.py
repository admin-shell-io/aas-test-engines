from unittest import TestCase
from aas_test_engines import data_types
from base64 import urlsafe_b64decode


def b64urlsafe_decode(s: str) -> str:
    # Append missing padding
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return urlsafe_b64decode(s).decode()


class Base64UrlTest(TestCase):

    def test_all(self):
        for value in [
            "",
            " ",
            "=",
            "ab",
            "abc",
            "#" * 80,
        ]:
            encoded = data_types.base64_urlsafe(value)
            self.assertNotIn("=", encoded)
            self.assertEqual(b64urlsafe_decode(encoded), value)
