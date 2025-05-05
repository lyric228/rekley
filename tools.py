import urllib.parse

async def search_pinterest(query: str) -> str:
    """
    Constructs a Pinterest search URL for the given query.

    Args:
        query: The search term for Pinterest.

    Returns:
        The URL to the Pinterest search results page.
    """
    encoded_query = urllib.parse.quote_plus(query)
    url = f"https://ru.pinterest.com/search/pins/?q={encoded_query}"
    print(f"Generated Pinterest URL: {url}")
    # ^^^ for logging/debugging
    return url

PINTEREST_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_pinterest",
        "description": "Search for pins on Pinterest based on a query and return the search results page URL.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search term for Pinterest, e.g., \'cute cat pictures\', \'modern kitchen ideas\'"
                }
            },
            "required": ["query"]
        }
    }
}
