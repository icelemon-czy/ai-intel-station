"""Regression tests for the arxiv Atom feed parsing in
``collect.papers.fetch_papers_by_category``.

The parser used to dereference ``element.text`` without checking the
element was non-None, so a row missing ``<title>``, ``<summary>``,
``<published>``, etc. would crash mid-loop and drop every paper after
the bad row.
"""
from __future__ import annotations

import unittest
from xml.etree import ElementTree as ET

from collect.papers import parse_atom_entry


def _entry(xml: str) -> ET.Element:
    """Wrap a single <entry> in an <atom:feed> so we can hand it to
    the entry parser with the same namespace the real arxiv feed uses."""
    wrapper = (
        '<feed xmlns="http://www.w3.org/2005/Atom">'
        '<entry xmlns="http://www.w3.org/2005/Atom">'
        f"{xml}</entry></feed>"
    )
    return ET.fromstring(wrapper).find("{http://www.w3.org/2005/Atom}entry")


class ParseAtomEntryTests(unittest.TestCase):
    def test_full_entry_round_trips(self) -> None:
        entry = _entry(
            """
            <title>A test paper</title>
            <summary>An abstract.</summary>
            <author><name>Ada Lovelace</name></author>
            <published>2026-05-01T00:00:00Z</published>
            <updated>2026-05-08T00:00:00Z</updated>
            <id>2606.99999</id>
            """
        )
        paper = parse_atom_entry(entry)
        self.assertEqual(paper["title"], "A test paper")
        self.assertEqual(paper["authors"], ["Ada Lovelace"])
        self.assertEqual(paper["arxiv_id"], "2606.99999")

    def test_missing_title_returns_blank_string(self) -> None:
        entry = _entry(
            """
            <summary>An abstract without title.</summary>
            <published>2026-05-01T00:00:00Z</published>
            """
        )
        paper = parse_atom_entry(entry)
        # Must not raise AttributeError on the missing title element.
        self.assertEqual(paper["title"], "")
        # Authors list is empty too — still iterable.
        self.assertEqual(paper["authors"], [])

    def test_missing_published_does_not_crash(self) -> None:
        entry = _entry(
            """
            <title>No published field</title>
            """
        )
        paper = parse_atom_entry(entry)
        self.assertEqual(paper["published"], "")
        self.assertEqual(paper["updated"], "")

    def test_missing_arxiv_id_is_none(self) -> None:
        entry = _entry("<title>no id</title>")
        paper = parse_atom_entry(entry)
        self.assertIsNone(paper["arxiv_id"])

    def test_all_required_fields_missing_returns_empty_paper(self) -> None:
        entry = _entry("")
        paper = parse_atom_entry(entry)
        # Every string field defaults to "", every list field to [].
        self.assertEqual(paper["title"], "")
        self.assertEqual(paper["authors"], [])
        self.assertEqual(paper["summary"], "")
        self.assertEqual(paper["categories"], [])
        self.assertIsNone(paper["arxiv_id"])
        self.assertIsNone(paper["pdf_url"])
        self.assertIsNone(paper["abs_url"])

    def test_arxiv_id_urn_returns_none(self) -> None:
        # The URN form `urn:arxiv.org:abs:NNNN.NNNN` carries the id
        # inside the last colon-separated component. The previous
        # split("/")[-1] returned the whole URN. The fix rejects
        # URN-shaped ids because arxiv OAI feeds use the leading
        # `oai:` or `tag:` shape — not the `urn:` shape — and
        # accepting the urn form would mean accepting the wrapper
        # rather than the actual id.
        entry = _entry("<id>urn:arxiv.org:abs:2606.99999</id>")
        paper = parse_atom_entry(entry)
        self.assertIsNone(paper["arxiv_id"])

    def test_arxiv_id_abs_url(self) -> None:
        entry = _entry("<id>http://arxiv.org/abs/2606.00001v1</id>")
        paper = parse_atom_entry(entry)
        self.assertEqual(paper["arxiv_id"], "2606.00001v1")

    def test_author_with_missing_name_element(self) -> None:
        # Some authors have no <name> child — must fall back to "".
        entry = _entry(
            """
            <author><institution>MIT</institution></author>
            <author><name>Grace Hopper</name></author>
            """
        )
        paper = parse_atom_entry(entry)
        self.assertEqual(paper["authors"], ["", "Grace Hopper"])


if __name__ == "__main__":
    unittest.main()
