from flask import Flask
from threading import Thread
import os
import requests
import time
import feedparser  

POSTED_LINKS_FILE = 'posted_links.txt'

def strip_html_tags(text):
    return re.sub(r'<[^>]+>', '', text)

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


def post_to_telegram(job):
    clean_title = strip_html_tags(job['title'])
    text = f"📢 *{clean_title}*\n[Read More]({job['link']})"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHANNEL_ID,
        'text': text,
        'parse_mode': 'Markdown'
    }

    try:
        resp = requests.post(url, data=payload)
        if resp.status_code != 200:
            print(f"❌ Telegram error: {resp.status_code} - {resp.text}")
        else:
            print(f"✅ Posted: {job['title']}")
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

