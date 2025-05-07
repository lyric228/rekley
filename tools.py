import httpx
from typing import List, Dict

import httpx
from bs4 import BeautifulSoup
import json
from typing import List, Dict
import urllib.parse

async def search_pinterest(query: str) -> List[Dict[str, str]]:
    """
    Ищет на Pinterest путем ручного парсинга страницы результатов поиска (через ru.pinterest.com)
    и возвращает пины с заголовками и URL-адресами.

    Args:
        query: Поисковый запрос.

    Returns:
        Список пинов, где каждый пин представлен словарем с ключами "title" и "url".
        Возвращает пустой список в случае ошибки.
    """
    encoded_query = urllib.parse.quote(query)
    search_url = f"https://ru.pinterest.com/search/pins/?q={encoded_query}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    results: List[Dict[str, str]] = []

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(search_url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            json_script_tag = soup.find("script", {"id": "__PWS_INITIAL_PROPS__", "type": "application/json"})
            if not json_script_tag:
                json_script_tag = soup.find("script", {"id": "initial-state", "type": "application/json"})
            
            if json_script_tag:
                try:
                    raw_json_data = json.loads(json_script_tag.string)
                    initial_redux_state = raw_json_data.get("props", {}).get("initialReduxState", {})
                    
                    search_results_list = initial_redux_state.get("results", [])
                    pins_details_map = initial_redux_state.get("pins", {})

                    pin_ids_in_order = []
                    for item in search_results_list:
                        if isinstance(item, dict) and item.get("type") == "pin" and "id" in item:
                            pin_ids_in_order.append(str(item["id"]))
                        elif isinstance(item, str):
                            pin_ids_in_order.append(item)
                        elif isinstance(item, dict) and "grid_title" in item and "id" in item:
                            pin_id = str(item.get("id"))
                            title = item.get("grid_title") or item.get("description", "No title")
                            link_path = item.get("link")
                            if not link_path:
                                link_path = f"/pin/{pin_id}/"
                            
                            if title and link_path and link_path.startswith("/pin/"):
                                pin_full_url = f"https://ru.pinterest.com{link_path}"
                                if not any(p["url"] == pin_full_url for p in results):
                                    results.append({"title": title.strip(), "url": pin_full_url})
                                if len(results) >= 10: break

                    if len(results) < 10:
                        for pin_id in pin_ids_in_order:
                            pin_data = pins_details_map.get(pin_id)
                            if not pin_data and not pin_id.startswith("pin_"):
                                pin_data = pins_details_map.get(f"pin_{pin_id}")
                            elif not pin_data and pin_id.startswith("pin_"):
                                 pass
                            
                            if pin_data:
                                title = pin_data.get("grid_title") or pin_data.get("description", "No title")
                                link_path = pin_data.get("link")
                                
                                if not link_path and "id" in pin_data:
                                     link_path = f"/pin/{pin_data['id']}/"

                                if title and link_path and link_path.startswith("/pin/"):
                                    pin_full_url = f"https://ru.pinterest.com{link_path}"
                                    if not any(p["url"] == pin_full_url for p in results):
                                        results.append({"title": title.strip(), "url": pin_full_url})
                                    if len(results) >= 10:
                                        break

                    if not results and pins_details_map:
                        for pin_id, pin_data in pins_details_map.items():
                            title = pin_data.get("grid_title") or pin_data.get("description", "No title")
                            link_path = pin_data.get("link")
                            if not link_path and "id" in pin_data:
                                link_path = f"/pin/{pin_data['id']}/"

                            if title and link_path and link_path.startswith("/pin/"):
                                pin_full_url = f"https://ru.pinterest.com{link_path}"
                                if not any(p["url"] == pin_full_url for p in results):
                                    results.append({"title": title.strip(), "url": pin_full_url})
                                if len(results) >= 10:
                                    break
                except Exception:
                    pass
            if not results:
                for img_tag in soup.find_all("img", alt=True, limit=30):
                    alt_text = img_tag.get("alt", "").strip()
                    if not alt_text or alt_text.lower() in ["изображение пина", "pin image"]: 
                        continue

                    parent_link = img_tag.find_parent("a", href=lambda href: href and href.startswith("/pin/"))
                    
                    if parent_link:
                        pin_url_path = parent_link.get("href")
                        if pin_url_path:
                            pin_full_url = f"https://ru.pinterest.com{pin_url_path}"
                            if not any(p["url"] == pin_full_url for p in results): # Дедупликация
                                results.append({"title": alt_text, "url": pin_full_url})
                                if len(results) >= 10:
                                    break


    except httpx.HTTPStatusError as e:
        print(f"Произошла ошибка HTTP: {e.response.status_code} - {e.request.url}")
        return []
    except httpx.RequestError as e:
        print(f"Произошла ошибка запроса: {e.request.url} - {e}")
        return []
    except Exception as e:
        print(f"Произошла непредвиденная ошибка: {e}")
        return []

    return results[:5]

PINTEREST_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_pinterest",
        "description": "Search Pinterest using official API and return list of pins with titles and URLs",
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
