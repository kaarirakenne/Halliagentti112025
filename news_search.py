import os
from datetime import datetime, timezone
import requests

def fetch_news(api_key: str, query: str) -> list:
    # Hakee uutisia NewsAPI:sta annetulla hakusanalla.
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": "fi",
        "sortBy": "publishedAt",
        "pageSize": 10,
    }
    headers = {"X-Api-Key": api_key}
    resp = requests.get(url, params=params, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json().get("articles", [])

def format_report(articles: list, query: str) -> str:
    now = datetime.now(timezone.utc).astimezone()
    header = f"Aamuraportti – {now.strftime('%d.%m.%Y %H:%M')} ({now.tzinfo})\n"
    header += f"Hakusanat: {query}\n"
    header += "=" * 60 + "\n\n"

    if not articles:
        return header + "Ei uutisia näillä hakusanoilla.\n"

    lines = [header]
    for i, art in enumerate(articles, start=1):
        title = art.get("title") or "(ei otsikkoa)"
        source = (art.get("source") or {}).get("name") or "tuntematon lähde"
        url = art.get("url") or ""
        published = art.get("publishedAt") or ""
        lines.append(f"{i}. {title}")
        lines.append(f"   Lähde: {source}")
        if published:
            lines.append(f"   Julkaistu: {published}")
        if url:
            lines.append(f"   Linkki: {url}")
        lines.append("")

    return "\n".join(lines)

def main():
    api_key = os.environ.get("NEWS_API_KEY")
    query = os.environ.get("SEARCH_QUERY", "akkuenergian varastointihanke halli")

    if not api_key:
        raise RuntimeError("NEWS_API_KEY puuttuu. Lisää se GitHub Secrets -kohtaan.")

    articles = fetch_news(api_key, query)
    report = format_report(articles, query)

    # Tulostetaan raportti lokiin
    print("\n===== AAMURAPORTTI =====\n")
    print(report)
    print("=========================\n")

    # Tallennetaan raportti tiedostoksi
    with open("aamuraportti.txt", "w", encoding="utf-8") as f:
        f.write(report)

if __name__ == "__main__":
    main()
