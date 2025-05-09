from typing import List, Dict
import asyncio
import aiohttp
from config import PINTEREST_API_KEY


async def search_pinterest(query: str) -> List[Dict[str, str]]:
    if not PINTEREST_API_KEY:
        return [{"error": "Pinterest API key not configured in config.py"}]

    headers = {
        "Authorization": f"Bearer {PINTEREST_API_KEY}",
        "Content-Type": "application/json"
    }
    params = {
        "query": query,
        "limit": 10 
    }
    
    pins_data = []

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.pinterest.com/v5/pins", headers=headers, params=params) as response:
                if response.status == 200:
                    response_json = await response.json()
                    items_to_process = response_json.get("items", [])
                    
                    for pin_item in items_to_process:
                        title = pin_item.get("title") or pin_item.get("note") or pin_item.get("description", "No Title")
                        link = pin_item.get("link")
                        
                        if link:
                            pins_data.append({title: link})
                    
                    if not pins_data and items_to_process:
                         return [{"info": "Found pins but could not extract title/link properly."}]
                    elif not pins_data:
                        return [{"info": "No pins found for the query."}]

                else:
                    error_details = await response.text()
                    return [{"error": f"Pinterest API error: {response.status} - {error_details}"}]
        
        return pins_data

    except aiohttp.ClientError as e:
        return [{"error": f"HTTP client error: {str(e)}"}]
    except Exception as e:
        return [{"error": f"An unexpected error occurred: {str(e)}"}]


PINTEREST_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_pinterest",
        "description": "Searches pins in Pinterest.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search term for Pinterest"
                }
            },
            "required": ["query"]
        }
    }
}

# Тест API пинтереста
async def main():
    print("Testing Pinterest search (direct API call)...")
    
    if not PINTEREST_API_KEY:
        print("PINTEREST_API_KEY is not set in config.py. Please set it to run the test.")
        print("Example format in config.py: PINTEREST_API_KEY = \"YOUR_PINTEREST_OAUTH_ACCESS_TOKEN\"")
        return

    test_query = "modern architecture"
    results = await search_pinterest(test_query)
    
    print(f"\nResults for '{test_query}':")
    if results:
        for i, result in enumerate(results):
            if "error" in result:
                print(f"  Error: {result['error']}")
            elif "info" in result:
                print(f"  Info: {result['info']}")
            else:
                for title, link in result.items():
                    print(f"  Pin {i+1}:")
                    print(f"    Title: {title}")
                    print(f"    Link: {link}")
    else:
        print("  No results structure returned or an unexpected issue occurred.")

if __name__ == "__main__":
    asyncio.run(main())
    