from flask import Flask
from threading import Thread
import os
import time
import requests
import feedparser
import re

TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
TELEGRAM_CHANNEL_ID = '@pythonjobss'
RSS_FEEDS_FILE = 'rss_feeds.txt'
POSTED_LINKS_FILE = 'posted_links.txt'

def strip_html_tags(text):
    # removes anything between <...>
    return re.sub(r'<[^>]+>', '', text)

def load_posted_links():
    if not os.path.exists(POSTED_LINKS_FILE):
        return set()
    with open(POSTED_LINKS_FILE, 'r') as f:
        return set(line.strip() for line in f)

def save_posted_link(link):
    with open(POSTED_LINKS_FILE, 'a') as f:
        f.write(link + '\n')

def load_rss_feeds():
    if not os.path.exists(RSS_FEEDS_FILE):
        return []
    with open(RSS_FEEDS_FILE, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def fetch_jobs():
    jobs = []
    for url in load_rss_feeds():
        feed = feedparser.parse(url)
        for entry in feed.entries:
            jobs.append({
                'title': entry.title,
                'link': entry.link
            })
    return jobs

def post_to_telegram(job):
    clean_title = strip_html_tags(job['title'])
    link = job['link'].split('url=')[-1].split('&')[0]
    message = f"{clean_title}\n{link}"

    resp = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        data={'chat_id': TELEGRAM_CHANNEL_ID, 'text': message}
    )
    if resp.status_code == 200:
        print(f"✅ Posted: {job['title']}")
    else:
        print(f"❌ Error {resp.status_code}: {resp.text}")

def main():
    posted = load_posted_links()
    while True:
        new_count = 0
        for job in fetch_jobs():
            # ▶️ 1. Clean the Google redirect URL to get the real job link
            clean_link = job['link'].split('url=')[-1].split('&')[0]

            # ▶️ 2. Only post if we haven’t seen this clean_link before
            if clean_link not in posted:
                # your existing post logic
                post_to_telegram(job)

                # ▶️ 3. Save & remember the clean link, not the raw one
                save_posted_link(clean_link)
                posted.add(clean_link)

                new_count += 1
                time.sleep(2)

        print(f"✅ Posted {new_count} new jobs.")
        time.sleep(60)


app = Flask('')

@app.route('/')
def home():
    return "✅ Telegram Job Bot is running!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

if __name__ == "__main__":
    keep_alive()
    main()
