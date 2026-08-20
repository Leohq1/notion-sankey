#!/usr/bin/env python3
"""
notion_sankey.py

Reads an internship-tracker database from Notion and generates a
self-contained Sankey diagram HTML file (output/sankey.html).

Each application's OWN ordered path through the pipeline is captured
(a multi-select property, tags added in the order the stages were
actually completed), so different companies can follow different funnels.

SETUP
-----
1. Create a Notion integration:  https://www.notion.so/my-integrations
   Copy the "Internal Integration Secret" into your .env file as NOTION_TOKEN.

2. Share your tracker database with that integration:
   open the database in Notion -> "..." menu -> Connections -> add your integration.

3. Get the database ID: open the database as a full page, copy the 32-char
   hex string from the URL (the part right before "?v=").
   Put it in your .env file as NOTION_DATA_SOURCE_ID.

4. Make sure your database has:
   - A multi-select property (name set in STAGES_PROPERTY below) whose
     tags you add IN ORDER as an application progresses, e.g. an
     application that did Applied -> OA -> Interview has all three
     tags on it, added in that order.
   - A text or select property (name set in OUTCOME_PROPERTY below)
     holding how the application ended, e.g. "In Progress", "Rejected",
     "Ghosted", "Offer".

5. pip install requests
   python notion_sankey.py   →   generates output/sankey.html
"""

import os
import sys
from collections import defaultdict
from pathlib import Path

import requests

import render


# ---------------------------------------------------------------------------
# Load .env file (simple loader, no extra dependency)
# ---------------------------------------------------------------------------

def _load_dotenv():
    """Load key=value pairs from .env into os.environ (if not already set)."""
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv()

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
DATABASE_ID = os.environ.get("NOTION_DATA_SOURCE_ID", "")
NOTION_VERSION = "2025-09-03"

# Exact property names in your Notion database.
STAGES_PROPERTY = "Stages Reached"   # multi-select, tags in completion order
OUTCOME_PROPERTY = "Outcome"           # text or select

# ---------------------------------------------------------------------------
# NOTION FETCH
# ---------------------------------------------------------------------------

def fetch_all_pages(database_id: str) -> list[dict]:
    """Query a Notion database (data source), following pagination, return all page objects."""
    url = f"https://api.notion.com/v1/data_sources/{database_id}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }

    results = []
    payload = {}
    while True:
        resp = requests.post(url, headers=headers, json=payload)
        if resp.status_code != 200:
            print(f"Notion API error {resp.status_code}: {resp.text}", file=sys.stderr)
            sys.exit(1)
        data = resp.json()
        results.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        payload = {"start_cursor": data["next_cursor"]}
    return results


def extract_stage_path(page: dict) -> list[str]:
    """Pull the ordered list of completed stages (multi-select) off a page."""
    prop = page.get("properties", {}).get(STAGES_PROPERTY)
    if not prop or prop.get("type") != "multi_select":
        return []
    return [tag["name"] for tag in (prop.get("multi_select") or [])]


def extract_outcome(page: dict) -> str | None:
    """Pull the outcome value (text or select) off a page."""
    prop = page.get("properties", {}).get(OUTCOME_PROPERTY)
    if not prop:
        return None
    ptype = prop.get("type")
    if ptype == "rich_text":
        parts = prop.get("rich_text") or []
        text = "".join(p.get("plain_text", "") for p in parts).strip()
        return text or None
    if ptype == "select":
        val = prop.get("select")
        return val["name"] if val else None
    if ptype == "status":
        val = prop.get("status")
        return val["name"] if val else None
    return None


def extract_company(page: dict) -> str:
    """Best-effort label for error messages -- pulls the title property."""
    for prop in page.get("properties", {}).values():
        if prop.get("type") == "title":
            parts = prop.get("title") or []
            text = "".join(p.get("plain_text", "") for p in parts).strip()
            if text:
                return text
    return "(untitled)"


# ---------------------------------------------------------------------------
# SANKEY BUILDING
# ---------------------------------------------------------------------------

def build_flows(applications: list[tuple[str, list[str], str | None]]) -> dict[tuple[str, str], int]:
    """
    applications: list of (company, ordered_stage_path, outcome)

    For each application:
      - add a flow for every consecutive pair in its own stage path
        (this is what lets different companies have different paths)
      - add a flow from its LAST completed stage to its outcome, unless
        the outcome duplicates the last stage (e.g. last stage "Offer"
        and outcome "Offer")
    """
    flows: dict[tuple[str, str], int] = defaultdict(int)
    skipped = []

    for company, path, outcome in applications:
        if not path:
            skipped.append(company)
            continue

        for a, b in zip(path, path[1:]):
            flows[(a, b)] += 1

        if outcome and outcome != path[-1]:
            flows[(path[-1], outcome)] += 1

    if skipped:
        print(
            f"# NOTE: {len(skipped)} application(s) had no stages set and were "
            f"skipped: {skipped}",
            file=sys.stderr,
        )

    return flows


def print_sankeymatic(flows: dict[tuple[str, str], int]) -> None:
    for (source, target), count in sorted(flows.items(), key=lambda kv: -kv[1]):
        print(f"{source} [{count}] {target}")


# ---------------------------------------------------------------------------

def main():
    if not NOTION_TOKEN or not DATABASE_ID:
        print(
            "Set NOTION_TOKEN and NOTION_DATA_SOURCE_ID in your .env file first "
            "(see the SETUP comment at the top of this file).",
            file=sys.stderr,
        )
        sys.exit(1)

    pages = fetch_all_pages(DATABASE_ID)
    applications = [
        (extract_company(p), extract_stage_path(p), extract_outcome(p))
        for p in pages
    ]

    if not applications:
        print("No applications found in the database.", file=sys.stderr)
        sys.exit(1)

    flows = build_flows(applications)
    render.render_sankey_html(flows)


if __name__ == "__main__":
    main()
