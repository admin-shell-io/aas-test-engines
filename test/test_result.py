from aas_test_engines.result import AasTestResult, Level
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
