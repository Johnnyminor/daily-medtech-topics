import os
import re
import html
from datetime import datetime
from email.utils import parsedate_to_datetime

import feedparser
import requests
from openai import OpenAI

# FDA RSS feeds
FEEDS = [
    "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/medwatch/rss.xml",
    "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/press-releases/rss.xml",
    "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/recalls/rss.xml",
]

INCLUDE_KEYWORDS = [
    "medical device", "surgical", "heart pump", "insulin pump", "catheter", "cryoprobe",
    "infusion pump", "stent", "wound dressing", "implant", "diagnostic", "device safety",
    "electrophysiology", "ultrasound catheter", "dialysis", "insufflation", "heating pad",
    "alcohol prep pad", "surgical stapler", "omnipod", "impella", "cryoprobe",
]

EXCLUDE_KEYWORDS = [
    "food", "beverage", "dietary supplement", "drug approval", "pharmaceutical",
    "cosmetics", "supplement", "capsule", "tablet", "injection", "pharmacy",
]

MODEL = "gpt-5.4-mini"


def clean_text(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def fetch_feed(url: str):
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        return feedparser.parse(response.content)
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None


def parse_item_date(item) -> datetime:
    date_str = item.get("published") or item.get("pubDate") or ""
    if not date_str:
        return datetime.min
    try:
        return parsedate_to_datetime(date_str).replace(tzinfo=None)
    except Exception:
        return datetime.min


def is_relevant_item(item) -> bool:
    title = clean_text(item.get("title", "")).lower()
    description = clean_text(item.get("description", "")).lower()
    combined = f"{title} {description}"

    has_include = any(keyword in combined for keyword in INCLUDE_KEYWORDS)
    has_exclude = any(keyword in combined for keyword in EXCLUDE_KEYWORDS)

    return has_include and not has_exclude


def ask_openai(client: OpenAI, prompt: str) -> str:
    response = client.responses.create(
        model=MODEL,
        input=prompt,
    )
    return response.output_text.strip()


def summarize_item(client: OpenAI, item) -> str:
    prompt = f"""
Summarize this FDA RSS item for medical device marketing purposes.

Title: {clean_text(item.get('title', ''))}
Description: {clean_text(item.get('description', ''))}
Date: {item.get('published', '') or item.get('pubDate', '')}
Link: {item.get('link', '')}

Provide:
- Key issue
- Device risk
- Marketing/clinical insight
- Relevance to medical device content

Be concise and practical.
""".strip()

    try:
        return ask_openai(client, prompt)
    except Exception as e:
        return f"Error summarizing: {e}"


def evaluate_topics(client: OpenAI, summaries: str) -> str:
    prompt = f"""
Evaluate these medical device summaries for content potential.

For each one, provide:
- Content format (blog, video, campaign)
- Target audience
- Topic idea/hook
- Priority (high, medium, or low)

Summaries:
{summaries}
""".strip()

    try:
        return ask_openai(client, prompt)
    except Exception as e:
        return f"Error evaluating: {e}"


def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")

    client = OpenAI(api_key=api_key)

    all_items = []
    seen = set()

    for feed_url in FEEDS:
        feed = fetch_feed(feed_url)
        if feed and getattr(feed, "entries", None):
            for item in feed.entries:
                unique_id = item.get("id") or item.get("guid") or item.get("link") or item.get("title")
                if unique_id in seen:
                    continue
                seen.add(unique_id)

                if is_relevant_item(item):
                    all_items.append(item)

    all_items.sort(key=parse_item_date, reverse=True)

    if not all_items:
        topics_content = "# No relevant medical device topics found today\n"
    else:
        summaries = []
        for item in all_items[:10]:
            summary = summarize_item(client, item)
            summaries.append(
                f"## {clean_text(item.get('title', ''))}\n"
                f"- Date: {item.get('published', '') or item.get('pubDate', '')}\n"
                f"- Link: {item.get('link', '')}\n\n"
                f"{summary}\n"
            )

        summaries_text = "\n\n".join(summaries)
        evaluation = evaluate_topics(client, summaries_text)

        topics_content = f"""# Daily MedTech Content Topics - {datetime.utcnow().strftime('%Y-%m-%d')}

## Relevant FDA Items Found: {len(all_items)}

## Summaries
{summaries_text}

## Content Topic Evaluations
{evaluation}

## Next Steps
- Review the high-priority topics
- Choose 1 to 3 for blog, video, or campaign development
- Copy this report into your content planning workflow
"""

    with open("daily_topics.md", "w", encoding="utf-8") as f:
        f.write(topics_content)


if __name__ == "__main__":
    main()
