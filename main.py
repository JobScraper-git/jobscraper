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
        for job in fetch_jobs():
            if job['link'] not in posted_links:
                post_to_telegram(job)
                save_posted_link(job['link'])
                posted_links.add(job['link'])
                time.sleep(2)
        print("⏳ Waiting before next check...")
        time.sleep(60)

if __name__ == "__main__":
    main()
