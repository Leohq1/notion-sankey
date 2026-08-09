# Notion Sankey

Generate an interactive Sankey diagram from an internship (or job) application tracker stored in Notion. The script reads each application's ordered pipeline stages from a Notion database and outputs a standalone HTML file powered by D3.js and d3-sankey.

![Sankey diagram example](output/sankey.html)

## Features

- **Ordered pipelines** — Each application tracks its own stage progression via a Notion multi-select property (tags added in order). Different companies can follow different funnels.
- **Interactive HTML output** — Hover over nodes and links to see exact counts. The diagram is self-contained — no server needed.
- **Configurable appearance** — Colors, dimensions, and layout are all tweakable in `config.py`.
- **Automated daily refresh** — A GitHub Actions workflow fetches fresh data and commits the updated diagram on a schedule.
- **Manual refresh via URL** — A "Refresh Data" link in the diagram footer triggers the workflow on demand.

## How It Works

```
Notion API  →  notion_sankey.py  →  render.py  →  output/sankey.html
```

1. `notion_sankey.py` queries your Notion database via the Notion API, extracting each page's stage path and outcome.
2. `render.py` builds a self-contained HTML file with an embedded D3.js Sankey diagram from the aggregated flows.
3. `index.html` at the repo root redirects to `output/sankey.html` for easy GitHub Pages hosting.

## Setup

### 1. Create a Notion integration

Go to [Notion Integrations](https://www.notion.so/my-integrations) and create a new internal integration. Copy the **Internal Integration Secret**.

### 2. Share your database

Open your tracker database in Notion → **...** menu → **Connections** → add your integration.

### 3. Get your database ID

Open the database as a full page in Notion and copy the 32-character hex string from the URL (the part right before `?v=`).

### 4. Configure environment

```bash
# Clone the repo
git clone https://github.com/Leohq1/notion-sankey.git
cd notion-sankey

# Install dependencies
pip install requests

# Create your .env file
echo 'NOTION_TOKEN=your-integration-secret' > .env
echo 'NOTION_DATA_SOURCE_ID=your-database-id' >> .env
```

### 5. Database schema

Your Notion database should have:

| Property | Type | Purpose |
|---|---|---|
| `Stages Completed` | Multi-select | Tags added **in order** as an application progresses (e.g. Applied → OA → Interview → Offer) |
| `Outcome` | Text or Select | How the application ended (e.g. "In Progress", "Rejected", "Ghosted", "Offer") |

Property names are configurable — edit `STAGES_PROPERTY` and `OUTCOME_PROPERTY` in `notion_sankey.py`.

### 6. Generate the diagram

```bash
python notion_sankey.py
```

This writes `output/sankey.html`. Open it in any browser.

## Configuration

Edit `config.py` to customize:

| Setting | Description |
|---|---|
| `TITLE` | Page title and heading |
| `COLORS` | Color mapping for each stage/outcome node |
| `NODE_WIDTH` | Width of node bars in pixels |
| `NODE_PADDING` | Vertical gap between nodes |
| `FLOW_OPACITY` | Transparency of flow links (0–1) |
| `PAGE_WIDTH` / `PAGE_HEIGHT` | SVG viewport size |
| `MARGINS` | Padding inside the SVG |
| `REFRESH_URL` | Link for the "Refresh Data" footer button |

## GitHub Actions

The included workflow (`.github/workflows/refresh.yml`) runs daily at 8am ET and can also be triggered manually from the Actions tab.

**Required secrets** in your repo settings:
- `NOTION_TOKEN` — your Notion integration secret
- `NOTION_DATA_SOURCE_ID` — your database ID

## GitHub Pages

To host the diagram publicly:

1. Go to your repo **Settings → Pages**
2. Set **Source** to **Deploy from a branch** and select `master`, `/ (root)`
3. Visit `https://<your-username>.github.io/notion-sankey/` — the root `index.html` will redirect to the latest diagram

## Project Structure

```
notion_sankey/
├── notion_sankey.py      # Main script: fetch from Notion, build flows
├── render.py             # HTML generator with D3.js Sankey template
├── config.py             # Appearance and layout settings
├── index.html            # Root redirect for GitHub Pages
├── output/
│   └── sankey.html       # Generated diagram (auto-refreshed by CI)
├── .github/workflows/
│   └── refresh.yml       # Daily auto-refresh workflow
└── .env                  # Notion credentials (gitignored, local only)
```

## License

MIT
