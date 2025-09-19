from typing import List, Dict, Optional
import datetime
import requests
from bs4 import BeautifulSoup

from ddgs import DDGS


def web_search(query: str, max_results: int = 5, region: str = "wt-wt") -> List[Dict[str, str]]:
    """
    Perform a web search and return a list of {title, url, snippet}.
    Requires duckduckgo_search. If unavailable, returns an empty list.
    """
    results: List[Dict[str, str]] = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, region=region, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href") or r.get("url", ""),
                    "snippet": r.get("body", "")
                })
                if len(results) >= max_results:
                    break
    except Exception:
        return []
    return results


def get_current_time() -> str:
    """
    当用户问到模糊时间的时候，通过此工具获取当前时间来判断用户所问的具体时间是什么时候
    """
    return str(datetime.datetime.now())


def fetch_page(url: str, timeout: int = 15, max_chars: int = 20000) -> Dict[str, Optional[str]]:
    """
    Fetch a web page and extract readable text.
    Returns {url, title, text}. Truncates to max_chars.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        )
    }
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        html = resp.text
        soup = BeautifulSoup(html, "html.parser")
        # Remove scripts/styles
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        title = (soup.title.string.strip() if soup.title and soup.title.string else "")
        text = " ".join(chunk.strip() for chunk in soup.stripped_strings)
        text = text[:max_chars]
        return {"url": url, "title": title, "text": text}
    except Exception:
        return {"url": url, "title": None, "text": None}


