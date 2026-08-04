"""
MCP server for the England & Wales Baby Names API.

Exposes tools that let an AI model answer questions like:
  - "What were the top baby names in 2024?"
  - "How has the popularity of Oliver changed over time?"
  - "What names are similar to Olivia for girls?"
  - "Which area in England had the most babies called Alfie in 2024?"

Data source: static JSON API generated from ONS birth registration data,
served from https://baby-names-api.netlify.app/api/

Deploy to Vercel: the ASGI app is exported in api/index.py, with all
requests routed there via vercel.json. The MCP endpoint will be available
at https://<your-vercel-url>/mcp
"""

import os
from typing import Literal, Optional

import requests
from mcp.server.fastmcp import FastMCP

BASE_URL = os.environ.get("BABY_NAMES_BASE_URL", "https://ons-baby-names-api.netlify.app")

mcp = FastMCP("baby-names", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))


def _get(path: str) -> dict | list:
    """Fetch a JSON endpoint and return the parsed response."""
    url = f"{BASE_URL.rstrip('/')}{path}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def get_meta() -> dict:
    """Return metadata about the dataset: which years are available and which
    years have geographic breakdowns.

    Use this first to discover what years of data exist before calling other
    tools. The dataset covers England & Wales and includes data from 1904 to
    the most recent year.

    Returns:
        {
            "years": [1904, 1914, ..., 2025],
            "geoYears": {"boys": [2022, 2023, 2024, 2025], "girls": [...]}
        }
    """
    return _get("/api/meta.json")


@mcp.tool()
def get_names(sex: Literal["all", "boys", "girls"] = "all") -> list[dict]:
    """Return the complete list of registered names with their URL slugs.

    Use this to discover names or to get the slug needed by get_name_data,
    get_similar_names, etc. Slugs are URL-encoded (e.g. "a%27isha" for A'Isha).

    Args:
        sex: Filter to "boys", "girls", or return "all" names (default).

    Returns:
        [{"name": "Oliver", "slug": "oliver"}, ...]
    """
    if sex not in ("all", "boys", "girls"):
        raise ValueError(f"sex must be 'all', 'boys', or 'girls', got {sex!r}")
    return _get(f"/api/names/{sex}.json")


@mcp.tool()
def search_names(query: str, sex: Literal["all", "boys", "girls"] = "all") -> list[dict]:
    """Search for names containing a given substring (case-insensitive).

    Use this to find a name's slug before calling get_name_data or
    get_similar_names when you're not sure of the exact spelling.

    Args:
        query: Substring to search for, e.g. "oli" returns Oliver, Olivia, etc.
        sex: Restrict results to "boys", "girls", or search "all" (default).

    Returns:
        [{"name": "Oliver", "slug": "oliver"}, ...]
    """
    names = _get(f"/api/names/{sex}.json")
    q = query.lower()
    return [n for n in names if q in n["name"].lower()]


@mcp.tool()
def get_year_data(year: int) -> dict:
    """Return every registered name and its count for a given year.

    Useful for exploring which names existed and how popular they were in a
    particular year. Historical decade entries (pre-1996) have count: null
    (rank-only data).

    Args:
        year: A year from get_meta()["years"], e.g. 2024.

    Returns:
        {
            "year": 2024,
            "boys": [{"name": "Muhammad", "count": 5721}, ...],
            "girls": [{"name": "Olivia", "count": 4170}, ...]
        }
    """
    return _get(f"/api/year/{year}.json")


@mcp.tool()
def get_top_names(year: int, sex: Optional[Literal["boys", "girls"]] = None, limit: int = 10) -> dict | list:
    """Return the ranked top names for a given year.

    Args:
        year: A year from get_meta()["years"], e.g. 2024.
        sex: Return only "boys" or "girls" rankings; omit to get both.
        limit: How many top names to return per sex (default 10).

    Returns when sex is None:
        {
            "year": 2024,
            "boys": [{"rank": 1, "name": "Muhammad", "count": 5721}, ...],
            "girls": [{"rank": 1, "name": "Olivia", "count": 4170}, ...]
        }
    Returns when sex is specified:
        [{"rank": 1, "name": "Muhammad", "count": 5721}, ...]
    """
    data = _get(f"/api/top/{year}.json")
    if sex is not None:
        if sex not in ("boys", "girls"):
            raise ValueError(f"sex must be 'boys' or 'girls', got {sex!r}")
        return data[sex][:limit]
    return {
        "year": data["year"],
        "boys": data["boys"][:limit],
        "girls": data["girls"][:limit],
    }


@mcp.tool()
def get_name_data(slug: str) -> dict:
    """Return the full time-series (count and rank per year) for a single name.

    Use search_names to find the correct slug if you're unsure. Data spans
    all available years for which the name was registered.

    Args:
        slug: URL slug for the name, e.g. "oliver". Use search_names to find
              this — do not guess it from the display name (some slugs are
              URL-encoded, e.g. "a%27isha").

    Returns:
        {
            "name": "Oliver",
            "slug": "oliver",
            "boys": [{"year": 1996, "count": 3655, "rank": 23}, ...],
            "girls": [{"year": 2001, "count": 12, "rank": 450}, ...]
        }
        count may be null for historical decade entries (rank only).
    """
    return _get(f"/api/name/{slug}.json")


@mcp.tool()
def get_geographic_data(year: int, sex: Literal["boys", "girls"]) -> dict:
    """Return the geographic breakdown of top names by local authority area
    for a given year and sex.

    Only available for recent years — check get_meta()["geoYears"] for the
    list of supported years.

    Args:
        year: A year from get_meta()["geoYears"][sex], e.g. 2024.
        sex: "boys" or "girls".

    Returns:
        {
            "year": 2024,
            "sex": "boys",
            "areas": [
                {
                    "code": "E06000001",
                    "areaName": "Hartlepool",
                    "geography": "Unitary Authority",
                    "topNames": ["Alfie"],
                    "count": 15
                },
                ...
            ]
        }
    """
    if sex not in ("boys", "girls"):
        raise ValueError(f"sex must be 'boys' or 'girls', got {sex!r}")
    return _get(f"/api/geo/{year}/{sex}.json")


@mcp.tool()
def get_similar_names(slug: str, sex: Literal["boys", "girls"]) -> dict:
    """Return precomputed names with similar popularity trajectories over time.

    Similarity is measured by sum of squared errors of rank over overlapping
    years, so names that rose and fell in tandem score lower (more similar).

    Args:
        slug: URL slug for the name (from search_names), e.g. "oliver".
        sex: "boys" or "girls" — must match the sex you're interested in.

    Returns:
        {
            "name": "Oliver",
            "slug": "oliver",
            "sex": "boys",
            "minYears": 10,
            "neighbors": [
                {"name": "Jack", "slug": "jack", "sse": 1234.5, "overlapYears": 28},
                ...
            ]
        }
    """
    if sex not in ("boys", "girls"):
        raise ValueError(f"sex must be 'boys' or 'girls', got {sex!r}")
    return _get(f"/api/similar/{sex}/{slug}.json")


@mcp.tool()
def health() -> dict:
    """Diagnostic tool confirming the MCP server is up and can reach the
    Baby Names API."""
    try:
        _get("/api/meta.json")
        api_reachable = True
    except Exception:  # noqa: BLE001
        api_reachable = False
    return {"status": "ok", "api_reachable": api_reachable, "tool_count": 9}


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
