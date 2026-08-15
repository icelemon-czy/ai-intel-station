"""Regression tests for the arxiv Atom feed parsing in
``collect.papers.fetch_papers_by_category``.

The parser used to dereference ``element.text`` without checking the
element was non-None, so a row missing ``<title>``, ``<summary>``,
``<published>``, etc. would crash mid-loop and drop every paper after
the bad row.
"""
from __future__ import annotations

import unittest
from urllib.error import HTTPError
from unittest.mock import patch
from xml.etree import ElementTree as ET

from collect.papers import PapersFetchError, fetch_papers_by_category, parse_atom_entry


class _FakeResponse:
    def __init__(self, body: bytes, *, content_length: str | None = None) -> None:
        self._body = body
        self.headers = {}
        if content_length is not None:
            self.headers["Content-Length"] = content_length

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def read(self, max_bytes: int) -> bytes:
        return self._body[:max_bytes]


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
    def test_category_fetch_closes_the_arxiv_api_connection(self) -> None:
        response = _FakeResponse(
            b'<feed xmlns="http://www.w3.org/2005/Atom"></feed>'
        )

        def _open(request, *, timeout: int):
            self.assertEqual(
                request.full_url.split("?", 1)[0],
                "https://export.arxiv.org/api/query",
            )
            self.assertEqual(request.get_header("Connection"), "close")
            self.assertEqual(timeout, 15)
            return response

        with patch("collect.papers.urlopen", side_effect=_open):
            papers = fetch_papers_by_category(
                ["cs.AI"],
                max_results=1,
                raise_on_error=True,
            )

        self.assertEqual(papers, [])

    def test_category_fetch_retries_one_transient_timeout(self) -> None:
        response = _FakeResponse(
            b'<feed xmlns="http://www.w3.org/2005/Atom"></feed>'
        )

        with (
            patch(
                "collect.papers.urlopen",
                side_effect=[TimeoutError("read timed out"), response],
            ) as open_mock,
            patch("collect.papers.sleep", create=True) as sleep_mock,
        ):
            papers = fetch_papers_by_category(
                ["cs.AI"],
                max_results=1,
                raise_on_error=True,
            )

        self.assertEqual(papers, [])
        self.assertEqual(open_mock.call_count, 2)
        sleep_mock.assert_called_once_with(3)

    def test_category_fetch_falls_back_to_official_atom_feed_on_429(self) -> None:
        response = _FakeResponse(
            b'''<feed xmlns="http://www.w3.org/2005/Atom"
                         xmlns:dc="http://purl.org/dc/elements/1.1/">
              <entry>
                <id>oai:arXiv.org:2608.12325v1</id>
                <title>Fallback paper</title>
                <summary>Fallback abstract.</summary>
                <published>2026-08-14T00:00:00-04:00</published>
                <updated>2026-08-14T00:00:00-04:00</updated>
                <dc:creator>Ada Researcher, Grace Scientist</dc:creator>
                <category term="cs.AI" />
                <link rel="alternate" type="text/html"
                      href="https://arxiv.org/abs/2608.12325v1" />
              </entry>
              <entry>
                <id>oai:arXiv.org:2608.99999v1</id>
                <title>Must be truncated</title>
                <summary>Second fallback abstract.</summary>
                <published>2026-08-14T00:00:00-04:00</published>
                <updated>2026-08-14T00:00:00-04:00</updated>
                <dc:creator>Second Author</dc:creator>
                <category term="cs.AI" />
                <link rel="alternate" type="text/html"
                      href="https://arxiv.org/abs/2608.99999v1" />
              </entry>
            </feed>'''
        )
        throttled = HTTPError(
            "https://export.arxiv.org/api/query",
            429,
            "Too Many Requests",
            {"Retry-After": "7"},
            None,
        )

        requested_urls: list[str] = []

        def _open(request, *, timeout: int):
            requested_urls.append(request.full_url)
            if "export.arxiv.org/api/query" in request.full_url:
                raise throttled
            self.assertEqual(request.full_url, "https://rss.arxiv.org/atom/cs.AI")
            self.assertEqual(timeout, 15)
            return response

        with (
            patch("collect.papers.urlopen", side_effect=_open),
            patch("collect.papers.sleep") as sleep_mock,
        ):
            papers = fetch_papers_by_category(
                ["cs.AI"],
                max_results=1,
                raise_on_error=True,
            )

        self.assertEqual([paper["title"] for paper in papers], ["Fallback paper"])
        self.assertEqual(
            papers[0]["authors"],
            ["Ada Researcher", "Grace Scientist"],
        )
        self.assertEqual(papers[0]["arxiv_id"], "2608.12325v1")
        self.assertEqual(
            papers[0]["pdf_url"],
            "https://arxiv.org/pdf/2608.12325v1",
        )
        self.assertEqual(len(requested_urls), 2)
        self.assertIn("export.arxiv.org/api/query", requested_urls[0])
        self.assertEqual(requested_urls[1], "https://rss.arxiv.org/atom/cs.AI")
        sleep_mock.assert_not_called()

    def test_category_fetch_falls_back_after_exhausting_5xx_retry(self) -> None:
        response = _FakeResponse(
            b'''<feed xmlns="http://www.w3.org/2005/Atom"
                         xmlns:dc="http://purl.org/dc/elements/1.1/">
              <entry>
                <id>oai:arXiv.org:2608.12325v1</id>
                <title>Recovered after 5xx</title>
                <summary>Recovered abstract.</summary>
                <published>2026-08-14T00:00:00-04:00</published>
                <updated>2026-08-14T00:00:00-04:00</updated>
                <dc:creator>Ada Researcher</dc:creator>
                <category term="cs.AI" />
                <link rel="alternate" type="text/html"
                      href="https://arxiv.org/abs/2608.12325v1" />
              </entry>
            </feed>'''
        )
        service_unavailable = HTTPError(
            "https://export.arxiv.org/api/query",
            503,
            "Service Unavailable",
            {"Retry-After": "90"},
            None,
        )
        bad_gateway = HTTPError(
            "https://export.arxiv.org/api/query",
            502,
            "Bad Gateway",
            {},
            None,
        )
        requested_urls: list[str] = []

        def _open(request, *, timeout: int):
            requested_urls.append(request.full_url)
            if len(requested_urls) == 1:
                raise service_unavailable
            if len(requested_urls) == 2:
                raise bad_gateway
            self.assertEqual(request.full_url, "https://rss.arxiv.org/atom/cs.AI")
            self.assertEqual(timeout, 15)
            return response

        with (
            patch("collect.papers.urlopen", side_effect=_open),
            patch("collect.papers.sleep") as sleep_mock,
        ):
            papers = fetch_papers_by_category(
                ["cs.AI"],
                max_results=1,
                raise_on_error=True,
            )

        self.assertEqual(
            [paper["title"] for paper in papers],
            ["Recovered after 5xx"],
        )
        self.assertEqual(len(requested_urls), 3)
        self.assertTrue(
            all(
                "export.arxiv.org/api/query" in url
                for url in requested_urls[:2]
            )
        )
        self.assertEqual(requested_urls[2], "https://rss.arxiv.org/atom/cs.AI")
        sleep_mock.assert_called_once_with(30)

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

    def test_single_category_caller_can_surface_remote_failure(self) -> None:
        with (
            patch(
                "collect.papers.urlopen",
                side_effect=OSError("offline"),
            ) as open_mock,
            patch("collect.papers.sleep") as sleep_mock,
        ):
            with self.assertRaises(PapersFetchError) as context:
                fetch_papers_by_category(
                    ["cs.AI"],
                    max_results=1,
                    raise_on_error=True,
                )

        self.assertEqual(open_mock.call_count, 3)
        sleep_mock.assert_called_once_with(3)
        self.assertIn("cs.AI", str(context.exception))
        self.assertIn("offline", str(context.exception))

    def test_single_category_caller_rejects_unknown_category_before_network(self) -> None:
        with patch("collect.papers.urlopen") as urlopen_mock:
            with self.assertRaises(PapersFetchError) as context:
                fetch_papers_by_category(
                    ["cs.UNKNOWN"],
                    max_results=1,
                    raise_on_error=True,
                )

        urlopen_mock.assert_not_called()
        self.assertIn("cs.UNKNOWN", str(context.exception))

    def test_single_category_caller_surfaces_oversized_response_header(self) -> None:
        max_bytes = 5 * 1024 * 1024
        response = _FakeResponse(
            b'<feed xmlns="http://www.w3.org/2005/Atom"></feed>',
            content_length=str(max_bytes + 1),
        )

        with patch("collect.papers.urlopen", return_value=response):
            with self.assertRaises(PapersFetchError) as context:
                fetch_papers_by_category(
                    ["cs.AI"],
                    max_results=1,
                    raise_on_error=True,
                )

        self.assertIn("cs.AI", str(context.exception))
        self.assertIn("byte cap", str(context.exception))

    def test_single_category_caller_surfaces_full_buffer_without_header(self) -> None:
        max_bytes = 5 * 1024 * 1024
        response = _FakeResponse(b"x" * max_bytes)

        with patch("collect.papers.urlopen", return_value=response):
            with self.assertRaises(PapersFetchError) as context:
                fetch_papers_by_category(
                    ["cs.AI"],
                    max_results=1,
                    raise_on_error=True,
                )

        self.assertIn("cs.AI", str(context.exception))
        self.assertIn("truncated-buffer", str(context.exception))


if __name__ == "__main__":
    unittest.main()
