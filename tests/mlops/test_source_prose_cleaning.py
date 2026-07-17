# -*- coding: utf-8 -*-
import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))

from pipeline.mlops.ft_dataset.text_cleaning import clean_source_prose  # noqa: E402


class TestCleanSourceProse(unittest.TestCase):
    def test_empty_and_none(self):
        self.assertEqual(clean_source_prose(""), "")
        self.assertEqual(clean_source_prose(None), "")

    def test_strips_html_and_entities(self):
        raw = "Denji is a <i>Devil Hunter</i>.<br>He merges &amp; fights."
        out = clean_source_prose(raw)
        self.assertNotIn("<", out)
        self.assertIn("Denji is a Devil Hunter.", out)
        self.assertIn("merges & fights", out)

    def test_keeps_spoiler_inner_text_drops_markers(self):
        raw = "Tanjiro fights ~!the demon king Muzan!~ in the finale."
        out = clean_source_prose(raw)
        self.assertNotIn("~!", out)
        self.assertNotIn("!~", out)
        self.assertIn("the demon king Muzan", out)

    def test_removes_replacement_char(self):
        raw = "resolves to become a �demon slayer� so that he can"
        out = clean_source_prose(raw)
        self.assertNotIn("�", out)
        self.assertIn("demon slayer", out)

    def test_collapses_whitespace(self):
        self.assertEqual(clean_source_prose("a   b\n\nc"), "a b c")

    def test_truncates_on_sentence_boundary(self):
        text = ("Sentence one is here. " * 100).strip()  # ~2200 chars
        out = clean_source_prose(text, max_chars=100)
        self.assertLessEqual(len(out), 100)
        self.assertTrue(out.endswith("."))

    def test_hard_cut_when_no_boundary(self):
        text = "x" * 500
        out = clean_source_prose(text, max_chars=100)
        self.assertEqual(len(out), 100)


if __name__ == "__main__":
    unittest.main()
