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
    return re.sub(r'<[^>]+>', '', text)

def clean_google_link(link):
    if 'url=' in link:
        return link.split('url=')[1].split('&')[0]
    return link

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
            title = strip_html_tags(entry.title)
            link = clean_google_link(entry.link)
            jobs.append({'title': title, 'link': link})
    return jobs

def post_to_telegram(job):
    message = f"{job['title']}\n{job['link']}"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        'chat_id': TELEGRAM_CHANNEL_ID,
        'text': message
    }
    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            print(f"✅ Sent: {job['title']}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"⚠️ Exception: {e}")

def main():
    posted_links = load_posted_links()
    while True:
        print("🔍 Checking for new jobs...")
        jobs = get_google_alerts()
        new_count = 0

        for job in jobs:
            if job['link'] not in posted_links:
                post_to_telegram(job)
                posted_links.add(job['link'])
                save_posted_link(job['link'])
                new_count += 1
                time.sleep(2)  # Wait between posts to avoid spamming

        print(f"✅ Posted {new_count} new jobs.")
        
        sleep_seconds = 60  # ⏲️ Adjust sleep duration here
        print(f"😴 Sleeping for {sleep_seconds} seconds...\n")
        time.sleep(sleep_seconds)

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
