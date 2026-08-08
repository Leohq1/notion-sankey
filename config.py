"""Configuration for the Sankey diagram generator.

Edit this file to customize your diagram's appearance — no need to touch
any other code.
"""

# Diagram title shown at the top of the HTML page.
TITLE = "Internship Application Pipeline"

# Colors for each stage and outcome node.
# Keys must match the stage/outcome names in your Notion database exactly.
# Any name not listed here gets a color from the d3 category-10 palette.
COLORS = {
    "Applied":     "#4a9eff",  # blue
    "OA":          "#f4a261",  # orange
    "Interview":   "#e76f51",  # red
    "Offer":       "#2a9d8f",  # teal
    "Rejected":    "#999999",  # gray
    "Ghosted":     "#cccccc",  # light gray
    "In Progress": "#c084fc",  # purple
}

# Node bar width in pixels.
NODE_WIDTH = 20

# Vertical gap between nodes in pixels.
NODE_PADDING = 12

# Transparency of flow links, 0.0 (invisible) to 1.0 (fully opaque).
FLOW_OPACITY = 0.4

# SVG viewport dimensions in pixels.
PAGE_WIDTH = 960
PAGE_HEIGHT = 600

# Margins inside the SVG (top, right, bottom, left) in pixels.
MARGINS = {"top": 20, "right": 20, "bottom": 20, "left": 20}

# URL for the "Refresh Data" link in the page footer.
# Change this to your own repo's Actions workflow URL.
REFRESH_URL = "https://github.com/Leohq1/notion-sankey/actions/workflows/refresh.yml"
