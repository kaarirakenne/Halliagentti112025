import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timezone
import requests


def fetch_news(api_key: str, query: str) -> list:
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
    data = resp.json()
    return data.get("articles", [])


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


def send_email(
    smtp_server: str,
    smtp_port: int,
    username: str,
    password: str,
    email_from: str,
    email_to: str,
    subject: str,
    body: str,
):
    msg = MIMEText(body, _charset="utf-8")
    msg["From"] = email_from
    msg["To"] = email_to
    msg["Subject"] = subject

    with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
        server.starttls()
        server.login(username, password)
        server.send_message(msg)


def main():
    api_key = os.environ.get("NEWS_API_KEY")
    query = os.environ.get("SEARCH_QUERY", "akkuenergian varastointihanke halli")
    email_from = os.environ.get("EMAIL_FROM")
    email_to = os.environ.get("EMAIL_TO")
    email_subject = os.environ.get(
        "EMAIL_SUBJECT", "Aamuraportti: halli- ja akkuhankkeet"
    )
    smtp_server = os.environ.get("SMTP_SERVER")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_username = os.environ.get("SMTP_USERNAME")
    smtp_password = os.environ.get("SMTP_PASSWORD")

    missing = []
    for name, value in [
        ("NEWS_API_KEY", api_key),
        ("EMAIL_FROM", email_from),
        ("EMAIL_TO", email_to),
        ("SMTP_SERVER", smtp_server),
        ("SMTP_USERNAME", smtp_username),
        ("SMTP_PASSWORD", smtp_password),
    ]:
        if not value:
            missing.append(name)

    if missing:
        raise RuntimeError(
            f"Puuttuvia ympäristömuuttujia: {', '.join(missing)}. "
            "Tarkista GitHub Secrets."
        )

    print(f"Haetaan uutisia hakusanalla: {query!r}")
    articles = fetch_news(api_key, query)
    print(f"Löytyi {len(articles)} artikkelia.")

    report = format_report(articles, query)
    print("Lähetetään sähköposti...")
    send_email(
        smtp_server=smtp_server,
        smtp_port=smtp_port,
        username=smtp_username,
        password=smtp_password,
        email_from=email_from,
        email_to=email_to,
        subject=email_subject,
        body=report,
    )
    print("Valmis.")


if __name__ == "__main__":
    main()
