from flask import Flask
from threading import Thread
import os
import requests
import time
import feedparser
import re

POSTED_LINKS_FILE = 'posted_links.txt'
RSS_FEEDS_FILE = 'rss_feeds.txt'
TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
TELEGRAM_CHANNEL_ID = '@pythonjobss'

def load_posted_links():
    return set(open(POSTED_LINKS_FILE).read().splitlines()) if os.path.exists(POSTED_LINKS_FILE) else set()

def save_posted_link(link):
    with open(POSTED_LINKS_FILE, 'a') as f:
        f.write(link + '\n')

def load_rss_feed_urls():
    if not os.path.exists(RSS_FEEDS_FILE):
        print("⚠️ rss_feeds.txt not found.")
        return []
    return [line.strip() for line in open(RSS_FEEDS_FILE) if line.strip() and not line.startswith('#')]

def get_google_alerts():
    jobs = []
    for rss_url in load_rss_feed_urls():
        feed = feedparser.parse(rss_url)
        for entry in feed.entries:
            jobs.append({
                'title': entry.title,
                'link': entry.link,
                'summary': getattr(entry, 'summary', '')
            })
    print(f"✅ Total job alerts collected: {len(jobs)}")
    return jobs

def escape_markdown(text):
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return ''.join('\\' + c if c in escape_chars else c for c in text)

def post_to_telegram(job):
    source_link = job['link'].split('url=')[-1].split('&')[0]
    domain = source_link.split('/')[2].replace('www.', '')
    clean_title = escape_markdown(job['title'])

    message = f"""🚀 *New Job Opportunity!*
💼 *Title:* {clean_title}
🗂️ *Summary:* Tap below to view full details
🌍 *Source:* {escape_markdown(domain)}
🔗 👉 [View and Apply Now]({escape_markdown(source_link)})
✅ Stay tuned for more job updates
"""

    payload = {
        'chat_id': TELEGRAM_CHANNEL_ID,
        'text': message,
        'parse_mode': 'MarkdownV2'
    }

    try:
        resp = requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", data=payload)
        if resp.status_code == 200:
            print(f"✅ Posted: {clean_title}")
        else:
            print(f"❌ Telegram error: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"⚠️ Error: {e}")

def main():
    posted_links = load_posted_links()
    while True:
        for job in get_google_alerts():
            if job['link'] not in posted_links:
                post_to_telegram(job)
                save_posted_link(job['link'])
                posted_links.add(job['link'])
                time.sleep(2)
        print("⏳ Sleeping")
        time.sleep(1)

# Flask app for keep-alive
app = Flask('')

@app.route('/')
def home():
    return "✅ Telegram Job Bot is running!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run_web).start()

if __name__ == "__main__":
    keep_alive()
    main()
