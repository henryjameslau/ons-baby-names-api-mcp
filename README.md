# ONS Baby Names API — MCP Server

An [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) server that exposes England & Wales baby names data from the [ONS birth registration dataset](https://baby-names-api.netlify.app), deployable to Vercel.

Once deployed, you can connect Claude (or any MCP-compatible client) to ask questions like:
- *"What were the top baby names in 2024?"*
- *"How has the popularity of Oliver changed over time?"*
- *"What names are similar to Olivia for girls?"*
- *"Which area had the most babies called Alfie in 2024?"*

## Tools

| Tool | Description |
|---|---|
| `get_meta` | Available years and geography years in the dataset |
| `get_names` | Full list of registered names (all / boys / girls) with slugs |
| `search_names` | Search names by substring |
| `get_year_data` | All names and counts for a given year |
| `get_top_names` | Ranked top N names for a given year |
| `get_name_data` | Full time-series (count + rank per year) for a single name |
| `get_geographic_data` | Regional breakdown by local authority area |
| `get_similar_names` | Names with similar popularity trajectories |
| `health` | Diagnostic check |

## Deploy to Vercel

1. Fork or clone this repo
2. Import it in [Vercel](https://vercel.com/new)
3. Deploy — no build configuration needed

The MCP endpoint will be available at:
```
https://<your-vercel-url>/mcp
```

### Optional environment variable

| Variable | Default | Description |
|---|---|---|
| `BABY_NAMES_BASE_URL` | `https://baby-names-api.netlify.app` | Override the upstream API base URL |

## Connect to Claude

In Claude's settings, add a new MCP server with the URL:
```
https://<your-vercel-url>/mcp
```

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

The server will start on `http://localhost:8000/mcp`.

## Data source

Data is served from [ons-baby-names-api.netlify.app](https://ons-baby-names-api.netlify.app/), generated from ONS birth registration statistics for England & Wales. Source code: [henryjameslau/baby-names-api](https://github.com/henryjameslau/baby-names-api).
