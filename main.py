from flask import Flask
from threading import Thread
import os
import requests
import time
import feedparser  # pip install feedparser

import html
import re
from urllib.parse import urlparse

POSTED_LINKS_FILE = 'posted_links.txt'


def load_posted_links():
    if not os.path.exists(POSTED_LINKS_FILE):
        return set()
    with open(POSTED_LINKS_FILE, 'r') as f:
        return set(line.strip() for line in f if line.strip())


def save_posted_link(link):
    with open(POSTED_LINKS_FILE, 'a') as f:
        f.write(link + '\n')


TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
TELEGRAM_CHANNEL_ID = '@pythonjobss'
# GOOGLE_ALERT_RSS_LIST = [
#     'https://www.google.com/alerts/feeds/00162670221367133570/3582827356212725062',
#     'https://www.google.com/alerts/feeds/00162670221367133570/12668502865782775102',
#     'https://www.google.com/alerts/feeds/00162670221367133570/7974111972648286337',
#     'https://www.google.com/alerts/feeds/00162670221367133570/17831604783258834712',
#     'https://www.google.com/alerts/feeds/00162670221367133570/3974079240828377224',
#     'https://www.google.com/alerts/feeds/00162670221367133570/6357045272730944519',
#     'https://www.google.com/alerts/feeds/00162670221367133570/270535950260598864',
#     'https://www.google.com/alerts/feeds/00162670221367133570/739455206598212500',
#     'https://www.google.com/alerts/feeds/00162670221367133570/17174574135221950586',
#     'https://www.google.com/alerts/feeds/00162670221367133570/4758562162378622981',
#     'https://www.google.com/alerts/feeds/00162670221367133570/39049550568899184',
#     'https://www.google.com/alerts/feeds/00162670221367133570/48433340344712748'
# ]
# Replace with your alert RSS

RSS_FEEDS_FILE = 'rss_feeds.txt'


def load_rss_feed_urls():
    if not os.path.exists(RSS_FEEDS_FILE):
        print("⚠️ rss_feeds.txt not found.")
        return []
    with open(RSS_FEEDS_FILE, 'r') as f:
        return [
            line.strip() for line in f
            if line.strip() and not line.strip().startswith('#')
        ]


def get_google_alerts():
    print("🔍 Fetching from multiple Google Alert RSS feeds...")
    jobs = []
    rss_urls = load_rss_feed_urls()

    for rss_url in rss_urls:
        print(f"📡 Fetching: {rss_url}")
        feed = feedparser.parse(rss_url)
        for entry in feed.entries:
            jobs.append({
                'title':
                entry.title,
                'link':
                entry.link,
                'summary':
                entry.summary if hasattr(entry, 'summary') else ''
            })

    print(f"✅ Total job alerts collected: {len(jobs)}")
    return jobs


# def post_to_telegram(job):
#     text = f"📢 *{job['title']}*\n[Read More]({job['link']})"
#     url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
#     payload = {
#         'chat_id': TELEGRAM_CHANNEL_ID,
#         'text': text,
#         'parse_mode': 'Markdown'
#     }

#     try:
#         resp = requests.post(url, data=payload)
#         if resp.status_code != 200:
#             print(f"❌ Telegram error: {resp.status_code} - {resp.text}")
#         else:
#             print(f"✅ Posted: {job['title']}")
#     except Exception as e:
#         print(f"⚠️ Error: {e}")

def strip_html_tags(text):
    return re.sub(r'<[^>]+>', '', text)

def escape_markdown(text):
    """
    Escapes special characters for Telegram MarkdownV2.
    """
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return ''.join('\\' + c if c in escape_chars else c for c in text)

def post_to_telegram(job):
    # Clean and escape job title
    clean_title = strip_html_tags(job['title'])
    clean_title = escape_markdown(clean_title)

    # Extract and escape domain from link
    domain = urlparse(job['link']).netloc.replace('www.', '')
    source = escape_markdown(domain)

    # Escape the footer and link (yes, link needs escaping too)
    footer = escape_markdown("✅ Stay tuned for more job updates!")
    safe_link = escape_markdown(job['link'])

    # Build fancy MarkdownV2-safe message
    message = f"""🚀 *New Job Opportunity!*

💼 *Title:* `{clean_title}`
🗂️ *Summary:* _Tap below to view full details_
🌍 *Source:* `{source}`

🔗 [👉 View & Apply Now]({safe_link})

{footer}
"""

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHANNEL_ID,
        'text': message,
        'parse_mode': 'MarkdownV2'
    }

    try:
        resp = requests.post(url, data=payload)
        if resp.status_code != 200:
            print(f"❌ Telegram error: {resp.status_code} - {resp.text}")
        else:
            print(f"✅ Posted: {clean_title}")
    except Exception as e:
        print(f"⚠️ Error: {e}")




def main():
    posted_links = load_posted_links()
    while True:
        jobs = get_google_alerts()
        for job in jobs:
            if job['link'] not in posted_links:
                post_to_telegram(job)
                posted_links.add(job['link'])
                save_posted_link(job['link'])
                time.sleep(2)
        print("⏳ Sleeping")
        time.sleep(1)


# Flask app to keep Replit alive
app = Flask('')


@app.route('/')
def home():
    return "✅ Telegram Job Bot is running!"


def run_web():
    app.run(host='0.0.0.0', port=8080)


def keep_alive():
    t = Thread(target=run_web)
    t.start()


# Start keep-alive server + main loop
if __name__ == "__main__":
    keep_alive()
    main()
