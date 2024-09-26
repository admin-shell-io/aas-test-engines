from aas_test_engines.result import AasTestResult, Level, write, start, abort, ResultException
from html.parser import HTMLParser

from unittest import TestCase


class ResultTest(TestCase):

    def setUp(self) -> None:
        self.result = AasTestResult('test', '', Level.INFO)
        self.result.append(AasTestResult('test1', '', Level.INFO))
        sub_result = AasTestResult('test2', '')
        self.result.append(sub_result)
        self.result.append(AasTestResult('test3', '', Level.ERROR))
        sub_result.append(AasTestResult('sub', '', Level.WARNING))

    def test_ok(self):
        self.assertTrue(AasTestResult('', '', Level.INFO).ok())
        self.assertTrue(AasTestResult('', '', Level.WARNING).ok())
        self.assertFalse(AasTestResult('', '', Level.ERROR).ok())

    def test_append(self):
        result = AasTestResult('test', '', Level.INFO)
        self.assertEqual(result.level, Level.INFO)
        result.append(AasTestResult('test1', '', Level.INFO))
        self.assertEqual(result.level, Level.INFO)
        result.append(AasTestResult('test2', '', Level.WARNING))
        self.assertEqual(result.level, Level.WARNING)
        result.append(AasTestResult('test2', '', Level.ERROR))
        self.assertEqual(result.level, Level.ERROR)
        self.assertEqual(len(result.sub_results), 3)

    def test_dump(self):
        self.result.dump()

    def test_to_json(self):
        j = self.result.to_dict()
        result = AasTestResult.from_json(j)
        self.assertEqual(len(self.result.sub_results), len(result.sub_results))
        self.assertEqual(self.result.level, result.level)
        self.assertEqual(self.result.message, result.message)

    def test_to_html(self):
        class SimpleHtmlChecker(HTMLParser):
            tags = []

            def handle_starttag(self, tag, attrs) -> None:
                self.tags.append(tag)

            def handle_endtag(self, tag) -> None:
                assert tag == self.tags.pop(-1)
        content = self.result.to_html()
        self.assertIn(self.result.message, content)
        checker = SimpleHtmlChecker()
        checker.feed(content)
        self.assertTrue(len(checker.tags) == 0)
        checker.close()


class ContextManagerTest(TestCase):

    def test_write_without_context(self):
        with self.assertRaises(RuntimeError):
            write("foo")

    def test_write_with_context(self):
        with start("foo") as r:
            write("bar")
        self.assertEqual(r.message, "foo")
        self.assertEqual(len(r.sub_results), 1)
        self.assertEqual(r.sub_results[0].message, "bar")
        self.assertEqual(len(r.sub_results[0].sub_results), 0)
        self.assertTrue(r.ok())

    def test_abort_without_context(self):
        with self.assertRaises(ResultException):
            abort("foo")

    def test_abort_with_context(self):
        with start("foo") as r:
            abort("bar")
        self.assertEqual(r.message, "foo")
        self.assertEqual(len(r.sub_results), 1)
        self.assertEqual(r.sub_results[0].message, "bar")
        self.assertEqual(len(r.sub_results[0].sub_results), 0)
        self.assertFalse(r.ok())
        r.dump()

    def test_start(self):
        with start('foo') as r:
            pass
        self.assertEqual(r.message, "foo")
        self.assertEqual(len(r.sub_results), 0)
        self.assertTrue(r.ok())
        r.dump()

    def test_nested_start(self):
        with start('foo') as r:
            write('foo_start')
            with start('bar'):
                write('bar_x')
            write('foo_end')
            
        self.assertEqual(r.message, "foo")
        self.assertEqual(len(r.sub_results), 3)
        self.assertEqual(r.sub_results[0].message, "foo_start")
        self.assertEqual(r.sub_results[1].message, "bar")
        self.assertEqual(r.sub_results[2].message, "foo_end")
        self.assertEqual(len(r.sub_results[1].sub_results), 1)
        self.assertEqual(r.sub_results[1].sub_results[0].message, "bar_x")
        self.assertEqual(len(r.sub_results[1].sub_results[0].sub_results), 0)
        self.assertTrue(r.ok())
        r.dump()

    def test_continue_after_abort(self):
        with start('foo') as r:
            write('foo_start')
            with start('bar'):
                abort('bar_x')
                write('bar_y') # won't be reached
            write('foo_end') # must be written
            
        r.dump()
        self.assertEqual(r.message, "foo")
        self.assertEqual(len(r.sub_results), 3)
        self.assertEqual(r.sub_results[0].message, "foo_start")
        self.assertEqual(r.sub_results[1].message, "bar")
        self.assertEqual(r.sub_results[2].message, "foo_end")
        self.assertEqual(len(r.sub_results[1].sub_results), 1)
        self.assertEqual(r.sub_results[1].sub_results[0].message, "bar_x")
        self.assertEqual(len(r.sub_results[1].sub_results[0].sub_results), 0)
        self.assertFalse(r.ok())

    def test_nested_abort(self):
        with start("foo") as r:
            with start("bar"):
                abort("x")
            abort("y")
        r.dump()
        self.assertEqual(r.message, "foo")
        self.assertEqual(len(r.sub_results), 2)
        self.assertEqual(r.sub_results[0].message, "bar")
        self.assertEqual(len(r.sub_results[0].sub_results), 1)
        self.assertEqual(r.sub_results[0].sub_results[0].message, 'x')
        self.assertEqual(r.sub_results[1].message, 'y')
        self.assertFalse(r.ok())

    def test_foreign_exception(self):
        with self.assertRaises(RuntimeError):
            with start("foo") as r:
                write("bar")
                raise RuntimeError("xyz")
        self.assertEqual(r.message, "foo")
        self.assertEqual(r.sub_results[0].message, "bar")
