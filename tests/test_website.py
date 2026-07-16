from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).parents[1]
WEBSITE = ROOT / "website"


class DocumentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.canonical = ""
        self.h1_count = 0
        self.json_ld: list[str] = []
        self.links: list[str] = []
        self.meta: dict[tuple[str, str], str] = {}
        self._in_json_ld = False
        self._json_buffer: list[str] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        values = {key: value or "" for key, value in attrs}
        if tag == "h1":
            self.h1_count += 1
        if tag in {"a", "link"} and values.get("href"):
            self.links.append(values["href"])
        if tag in {"img", "script"} and values.get("src"):
            self.links.append(values["src"])
        if tag == "link" and values.get("rel") == "canonical":
            self.canonical = values.get("href", "")
        if tag == "meta":
            if values.get("name"):
                self.meta[("name", values["name"])] = values.get("content", "")
            if values.get("property"):
                self.meta[("property", values["property"])] = values.get(
                    "content",
                    "",
                )
        if (
            tag == "script"
            and values.get("type") == "application/ld+json"
        ):
            self._in_json_ld = True
            self._json_buffer = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._in_json_ld:
            self.json_ld.append("".join(self._json_buffer))
            self._in_json_ld = False

    def handle_data(self, data: str) -> None:
        if self._in_json_ld:
            self._json_buffer.append(data)


def parse_index() -> tuple[str, DocumentParser]:
    html = (WEBSITE / "index.html").read_text()
    parser = DocumentParser()
    parser.feed(html)
    return html, parser


def test_website_has_complete_search_metadata() -> None:
    _, parser = parse_index()

    assert parser.h1_count == 1
    assert parser.canonical == "https://eminogrande.github.io/mn-uncensored/"
    assert 80 <= len(parser.meta[("name", "description")]) <= 170
    assert parser.meta[("name", "robots")].startswith("index,follow")
    assert parser.meta[("property", "og:title")]
    assert parser.meta[("property", "og:description")]
    assert parser.meta[("property", "og:image")].endswith(
        "/assets/og-card.png"
    )
    assert parser.meta[("name", "twitter:card")] == "summary_large_image"


def test_website_structured_data_is_valid_json() -> None:
    _, parser = parse_index()

    assert parser.json_ld
    documents = [json.loads(value) for value in parser.json_ld]
    graph_types = {
        entry["@type"]
        for document in documents
        for entry in document.get("@graph", [])
    }
    assert {
        "Organization",
        "WebSite",
        "SoftwareApplication",
        "ItemList",
        "FAQPage",
    } <= graph_types


def test_internal_assets_and_documents_exist() -> None:
    _, parser = parse_index()

    for value in parser.links:
        if value.startswith(("#", "mailto:", "tel:")):
            continue
        parsed = urlparse(value)
        if parsed.scheme or value.startswith("//"):
            continue
        path = value.split("#", 1)[0].split("?", 1)[0]
        if not path:
            continue
        target = WEBSITE / path
        assert target.exists(), f"missing website resource: {value}"


def test_whatsapp_access_cta_is_consistent() -> None:
    html, _ = parse_index()
    links = set(
        re.findall(r'href="(https://wa\.me/[^"]+)"', html)
    )

    assert links == {
        "https://wa.me/13103408213?text=Hi%20Emin%2C%20I%20would%20like%20to%20request%20access%20to%20ABLITERATED.cloud"
    }


def test_agent_and_discovery_files_are_present_and_valid() -> None:
    expected = [
        "index.md",
        "llms.txt",
        "llms-full.txt",
        "auth.md",
        "openapi.json",
        "robots.txt",
        "sitemap.xml",
        ".well-known/api-catalog.json",
        ".well-known/security.txt",
        ".well-known/skills.json",
        "skills/abliterated-cloud/SKILL.md",
    ]
    for relative in expected:
        assert (WEBSITE / relative).is_file(), relative

    json.loads((WEBSITE / "openapi.json").read_text())
    json.loads((WEBSITE / ".well-known/api-catalog.json").read_text())
    json.loads((WEBSITE / ".well-known/skills.json").read_text())
    ET.parse(WEBSITE / "sitemap.xml")

    robots = (WEBSITE / "robots.txt").read_text()
    assert "Sitemap:" in robots
    assert "GPTBot" in robots
    assert "ClaudeBot" in robots
    assert "OAI-SearchBot" in robots


def test_homepage_has_no_external_runtime_dependencies_or_api_polling() -> None:
    html, parser = parse_index()
    css = (WEBSITE / "styles.css").read_text()
    javascript = (WEBSITE / "app.js").read_text()

    external_runtime = [
        value
        for value in parser.links
        if value.startswith(("http://", "https://"))
        and not value.startswith(
            (
                "https://wa.me/",
                "https://github.com/",
                "https://huggingface.co/",
                "https://eminogrande.github.io/",
            )
        )
    ]
    assert external_runtime == []
    assert "@import" not in css
    assert "url(http" not in css
    assert "fetch(" not in javascript
    assert "XMLHttpRequest" not in javascript
    assert "modal.run" not in javascript
    assert re.search(r"sk-mn-[A-Za-z0-9_-]{16,}", html) is None


def test_homepage_performance_budget() -> None:
    critical = [
        WEBSITE / "index.html",
        WEBSITE / "styles.css",
        WEBSITE / "app.js",
        WEBSITE / "assets/logo.svg",
        WEBSITE / "assets/favicon.svg",
    ]
    total_bytes = sum(path.stat().st_size for path in critical)

    assert total_bytes < 125_000
    assert (WEBSITE / "assets/og-card.png").stat().st_size < 250_000
