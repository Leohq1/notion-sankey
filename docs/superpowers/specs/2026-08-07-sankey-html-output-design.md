# Design: Sankey Diagram HTML Output

**Date:** 2026-08-07
**Topic:** Replace SankeyMATIC manual copy-paste workflow with direct HTML output, deployable to GitHub Pages and embeddable in Notion.

## Overview

Currently `notion_sankey.py` fetches internship application data from a Notion database and outputs SankeyMATIC-formatted text that must be manually pasted into sankeymatic.com. The goal is to eliminate the manual step: the script should output a self-contained HTML file with a d3-sankey diagram, ready to be hosted on GitHub Pages and embedded into a Notion page via `/embed`.

## Architecture

```
Notion API ──→ notion_sankey.py (fetch + build flows)
                    │
                    ↓
              render.py (flows → HTML via template)
                    │
                    ↓
              output/sankey.html (standalone, self-contained)
                    │
                    ↓ git push
              GitHub Pages (yourusername.github.io/notion-sankey/output/sankey.html)
                    │
                    ↓ Notion /embed
              Notion page (live diagram)
```

### File Structure

```
notion_sankey/
├── notion_sankey.py       # main script (fetch Notion + build flows dict)
├── config.py              # colors, title, layout settings
├── render.py              # takes flows dict → generates output/sankey.html
├── output/
│   └── sankey.html        # generated HTML, committed to repo (required for GitHub Pages)
├── .env                   # NOTION_TOKEN (gitignored)
└── .github/workflows/
    └── refresh.yml        # (future) scheduled auto-refresh via GitHub Actions
```

## Components

### 1. config.py — User-editable settings

A Python file holding all configurable values. Users edit this to customize their diagram without touching the rendering code.

- `TITLE: str` — diagram title shown as `<h1>` on the page
- `COLORS: dict[str, str]` — maps stage/outcome names to hex colors. Fallback: d3 category colors for unmapped names
- `NODE_WIDTH: int` — node bar width in px (default 20)
- `NODE_PADDING: int` — vertical gap between nodes in px (default 12)
- `FLOW_OPACITY: float` — link opacity 0.0–1.0 (default 0.4)
- `PAGE_WIDTH: int` / `PAGE_HEIGHT: int` — diagram viewport dimensions
- `MARGINS: dict` — top/right/bottom/left margins

### 2. notion_sankey.py — No structural changes

The existing script already does the right things: authenticate, paginate the Notion database, extract stage paths and outcomes, build a `dict[tuple[str,str], int]` of flow counts. We add a call to `render.py` at the end instead of (or in addition to) printing SankeyMATIC text.

### 3. render.py — New file

Takes the flows dict + config values and produces `output/sankey.html`.

```
def render_sankey_html(
    flows: dict[tuple[str, str], int],
    config: ...,
    output_path: str = "output/sankey.html",
) -> None:
```

Logic:
1. Build a list of `{"source": str, "target": str, "value": int}` from the flows dict
2. Collect all unique node names (sources + targets)
3. Serialize flows, nodes, colors, title to JSON
4. Embed JSON + d3-sankey rendering JS into the HTML template
5. Write to output path

### 4. output/sankey.html — Generated artifact

Single self-contained HTML file. Structure:

- `<h1>` with the configured title
- `<p class="updated">` showing generation timestamp
- `<svg>` container for the d3 diagram
- `<script src="https://unpkg.com/d3@7">` — d3 from CDN
- `<script src="https://unpkg.com/d3-sankey@0.12">` — d3-sankey layout
- Inline `<script>` with embedded data as a JS object, plus ~40 lines of d3 rendering code that:
  - Creates a `d3.sankey()` layout from the data
  - Renders `<rect>` nodes with the configured colors
  - Renders `<path>` links with gradient coloring (source color → target color, with opacity)
  - Adds `<text>` labels next to nodes
  - Adds hover tooltips showing flow count and path

## Deployment

### GitHub Pages

1. User creates a GitHub repo (or uses existing one)
2. Enable GitHub Pages in repo Settings → Pages → Source: "Deploy from a branch" → `main` branch, `/` (root) directory
3. After pushing, the page is available at `https://<username>.github.io/<repo>/output/sankey.html`
4. Notion: use `/embed` block, paste the URL

### Secrets

- `.env` file (with `NOTION_TOKEN`) is `.gitignore`d — never committed
- For GitHub Actions auto-refresh (future): `NOTION_TOKEN` stored as a GitHub Secret

### Auto-Refresh (Future Enhancement)

- **Scheduled polling:** A GitHub Action workflow runs on a cron schedule (e.g., every hour), fetches from Notion using the token in GitHub Secrets, generates new HTML, commits and pushes. GitHub Pages deploys automatically.
- **Refresh button:** The HTML page includes a button that hits a GitHub `repository_dispatch` webhook, triggering the same Action on-demand. After trigger, the page polls for the updated file and auto-reloads.
- **Limitation:** Notion does not offer webhooks, so true event-driven refresh is not possible. Polling is the best available approach.

## Constraints & Trade-offs

| Constraint | Impact |
|-----------|--------|
| Notion has no webhooks | Cannot auto-refresh on data change; must poll |
| HTML page is static (no server) | Diagram data is snapshot-in-time; "last updated" timestamp communicates freshness |
| No Python deps for rendering | d3 runs entirely in the browser; `render.py` only does string templating |
| CDN dependency for d3 | Page requires internet to load. Mitigation: could bundle d3 inline if offline support needed |

## Not in Scope (V1)

- Interactive color picker on the HTML page (config is Python-side only)
- Multiple diagrams/dashboards in one output
- Data filtering by date range in the UI
- Push-button refresh from the page
- Scheduling automation (GitHub Actions workflow)
