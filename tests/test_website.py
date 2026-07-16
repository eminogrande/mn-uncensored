from __future__ import annotations

import hashlib
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


def test_signal_access_cta_is_consistent() -> None:
    html, _ = parse_index()
    links = set(
        re.findall(r'href="(https://signal\.me/[^"]+)"', html)
    )

    assert links == {"https://signal.me/#p/+13103408213"}

    active_access_documents = [
        html,
        (WEBSITE / "index.md").read_text(),
        (WEBSITE / "auth.md").read_text(),
        (WEBSITE / "llms.txt").read_text(),
        (WEBSITE / "llms-full.txt").read_text(),
    ]
    for document in active_access_documents:
        assert "wa.me" not in document
        assert "WhatsApp" not in document


def test_real_model_names_and_planned_prices_are_explicit() -> None:
    html, _ = parse_index()

    models = {
        "huihui-ai/Huihui-Qwen3.6-35B-A3B-abliterated": "$5.45/h",
        "YuYu1015/YuYu1015-Ornith-1.0-35B-abliterated": "$5.45/h",
        "huihui-ai/Huihui-Qwythos-9B-Claude-Mythos-5-1M-abliterated":
            "$2.34/h",
        "cebeuq/Ornith-1.0-397B-abliterated-W4A16": "$10.90/h",
    }
    plain_html = html.replace("<wbr>", "")

    for model, price in models.items():
        assert model in plain_html
        assert price in html

    assert "Free means the model weight files have no purchase price." in html
    assert "Published prices · access by invitation" in html
    assert "Customer accounts, quotas, metering, billing and invoicing" in html
    assert "Managed cloud inference is paid" in html
    assert "jailbroken" in html
    assert "zero refusals" in html
    assert "20% markup" not in html
    assert "gross margin" not in html


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
        ".well-known/api-catalog",
        ".well-known/agent-skills/index.json",
        ".well-known/agent-card.json",
        ".well-known/agent.json",
        ".well-known/http-message-signature-directory",
        ".well-known/http-message-signatures-directory",
        ".well-known/mcp/server-card.json",
        ".well-known/oauth-authorization-server",
        ".well-known/oauth-protected-resource",
        ".well-known/openid-configuration",
        ".well-known/webmcp.json",
        ".well-known/skills/index.json",
        ".well-known/security.txt",
        ".well-known/skills.json",
        "skills/abliterated-cloud/SKILL.md",
    ]
    for relative in expected:
        assert (WEBSITE / relative).is_file(), relative

    openapi = json.loads((WEBSITE / "openapi.json").read_text())
    model_catalog = openapi["x-model-catalog"]
    assert len(model_catalog) == 4
    assert {
        entry["hugging_face_model"] for entry in model_catalog
    } == {
        "huihui-ai/Huihui-Qwen3.6-35B-A3B-abliterated",
        "YuYu1015/YuYu1015-Ornith-1.0-35B-abliterated",
        "huihui-ai/Huihui-Qwythos-9B-Claude-Mythos-5-1M-abliterated",
        "cebeuq/Ornith-1.0-397B-abliterated-W4A16",
    }
    assert {
        entry["price_usd_per_hour"] for entry in model_catalog
    } == {5.45, 2.34, 10.9}
    api_catalog_json = json.loads(
        (WEBSITE / ".well-known/api-catalog.json").read_text()
    )
    api_catalog = json.loads(
        (WEBSITE / ".well-known/api-catalog").read_text()
    )
    assert api_catalog["linkset"]
    catalog_entry = api_catalog["linkset"][0]
    assert catalog_entry["anchor"].startswith("https://")
    assert catalog_entry["service-desc"][0]["href"].endswith("/openapi.json")
    assert catalog_entry["service-doc"]
    assert api_catalog_json == api_catalog
    json.loads((WEBSITE / ".well-known/skills.json").read_text())
    legacy_skills = json.loads(
        (WEBSITE / ".well-known/skills/index.json").read_text()
    )
    assert legacy_skills["version"] == "0.1.0"

    skill_index = json.loads(
        (WEBSITE / ".well-known/agent-skills/index.json").read_text()
    )
    assert skill_index["$schema"].endswith("/0.2.0/schema.json")
    skill = skill_index["skills"][0]
    assert skill["type"] == "skill-md"
    skill_path = WEBSITE / "skills/abliterated-cloud/SKILL.md"
    digest = hashlib.sha256(skill_path.read_bytes()).hexdigest()
    assert skill["digest"] == f"sha256:{digest}"
    ET.parse(WEBSITE / "sitemap.xml")

    robots = (WEBSITE / "robots.txt").read_text()
    assert "Sitemap:" in robots
    assert "Content-Signal: ai-train=no, search=yes, ai-input=yes" in robots
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
                "https://signal.me/",
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
    assert (WEBSITE / "assets/hero-brain.avif").stat().st_size < 200_000
    assert (WEBSITE / "assets/hero-brain.webp").stat().st_size < 500_000
