import json
import re
from datetime import datetime
from email.utils import format_datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom
import requests
from bs4 import BeautifulSoup


def parse_ist_date(date_str):
    """Parses Punjabi Jagran date format like: 'Sat, 05 Sep 2026 09:04 AM (IST)'

    and converts it to RFC-822 standard format for valid RSS.
    """
    if not date_str:
        return format_datetime(datetime.now())
    try:
        # Remove '(IST)' wrapper if present
        cleaned_str = re.sub(r"\s*\(IST\)", "", date_str).strip()
        # Parse: Sat, 05 Sep 2026 09:04 AM
        dt = datetime.strptime(cleaned_str, "%a, %d %b %Y %I:%M %p")
        return format_datetime(dt)
    except Exception:
        return format_datetime(datetime.now())


def generate_rss_feed():
    source_url = "https://www.punjabijagran.com/latest-news-punjabi.html"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    response = requests.get(source_url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch page: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    script_tag = soup.find("script", id="__NEXT_DATA__")
    if not script_tag:
        print("Error: __NEXT_DATA__ tag not found.")
        return

    json_data = json.loads(script_tag.string)
    articles = (
        json_data.get("props", {})
        .get("pageProps", {})
        .get("CATEGORYP1", [])
    )

    # 1. Build RSS 2.0 XML Tree
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = "Punjabi Jagran - Latest News"
    ET.SubElement(channel, "link").text = source_url
    ET.SubElement(channel, "description").text = (
        "Latest Punjabi news feed generated directly from Punjabi Jagran."
    )
    ET.SubElement(channel, "language").text = "pa-IN"
    ET.SubElement(channel, "lastBuildDate").text = format_datetime(
        datetime.now()
    )

    # 2. Populate Channel Items
    for news in articles:
        item = ET.SubElement(channel, "item")

        # Title
        title = news.get("headline", "No Title")
        ET.SubElement(item, "title").text = title

        # Construct Article Link
        category_url = news.get("categoryURL", "punjab")
        web_title_url = news.get("webTitleUrl", "")
        news_id = news.get("id", "")
        article_link = f"https://www.punjabijagran.com/{category_url}/{web_title_url}-{news_id}.html"

        ET.SubElement(item, "link").text = article_link

        guid = ET.SubElement(item, "guid", isPermaLink="true")
        guid.text = article_link

        # Description / Summary
        summary = news.get("summary", "")
        ET.SubElement(item, "description").text = summary

        # Category
        cat_name = news.get("categoryPb") or news.get("category", "")
        if cat_name:
            ET.SubElement(item, "category").text = cat_name

        # Publication Date (RFC 822 format)
        pub_date = news.get("pubDate", "")
        ET.SubElement(item, "pubDate").text = parse_ist_date(pub_date)

        # Image Enclosure
        img_name = news.get("imgName", "")
        if img_name:
            img_url = f"https://img.punjabijagran.com/punjabi/{img_name}"
            ET.SubElement(
                item,
                "enclosure",
                url=img_url,
                type="image/jpeg",
                length="0",
            )

    # 3. Format and Write XML to File
    xml_str = ET.tostring(rss, encoding="utf-8")
    pretty_xml = minidom.parseString(xml_str).toprettyxml(
        indent="  ", encoding="utf-8"
    )

    output_filename = "punjabi_jagran_feed.xml"
    with open(output_filename, "wb") as f:
        f.write(pretty_xml)

    print(
        f"RSS Feed successfully created: {output_filename} ({len(articles)}"
        " items included)"
    )


if __name__ == "__main__":
    generate_rss_feed()