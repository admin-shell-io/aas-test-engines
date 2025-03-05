from unittest import TestCase
from aas_test_engines.opc import normpath, splitpath


class NormPathTest(TestCase):

    def test_empty(self):
        self.assertEqual(normpath(""), "")
        self.assertEqual(normpath("   "), "")

    def test_double_slashes(self):
        self.assertEqual(normpath("//a//b//c"), "/a/b/c")
        self.assertEqual(normpath("//"), "/")

    def test_dot(self):
        self.assertEqual(normpath("."), "")
        self.assertEqual(normpath("a/./b/./c"), "a/b/c")
        self.assertEqual(normpath("a/b/."), "a/b")

    def test_trailing_slashes(self):
        self.assertEqual(normpath("/abc/def/"), "/abc/def")
        self.assertEqual(normpath("abc/def// //"), "abc/def")

    def test_double_dot(self):
        self.assertEqual(normpath("foo/../bar"), "bar")
        self.assertEqual(normpath("/foo/../bar///"), "/bar")
        self.assertEqual(normpath("a/b/../c"), "a/c")
        self.assertEqual(normpath("a/b/../c/.."), "a")
        self.assertEqual(normpath("/a/b/../c/.."), "/a")

    def test_illegal_double_dot(self):
        self.assertEqual(normpath(".."), "")
        self.assertEqual(normpath("/.."), "/")
        self.assertEqual(normpath("../x"), "x")
        self.assertEqual(normpath("/../x"), "/x")


class SplitPathTest(TestCase):

    def test_empty(self):
        self.assertEqual(splitpath(""), ("", ""))

    def test_ends_with_slash(self):
        self.assertEqual(splitpath("a/b.txt/"), ("a/b.txt", ""))
        self.assertEqual(splitpath("/"), ("", ""))
        self.assertEqual(splitpath("/a/b/"), ("/a/b", ""))

    def test_no_slash(self):
        self.assertEqual(splitpath("foo.txt"), ("", "foo.txt"))
