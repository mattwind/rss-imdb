import sys
from apscheduler.schedulers.background import BackgroundScheduler
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from flask import Flask, Response

try:
    app = Flask(__name__)

    # Global variable to store the latest RSS feed
    latest_rss = ""

    def scrape_page(url):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch page: {response.status_code}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.find_all('article')

        feed_items = []
        for article in articles:
            title_tag = article.find('a')
            title = title_tag.text.strip() if title_tag else "No Title"
            link = title_tag['href'] if title_tag and title_tag.has_attr('href') else "#"
            description = article.find('span').text.strip() if article.find('span') else "No Description"
            
            image_tag = article.find('img')
            image_url = image_tag['src'] if image_tag and image_tag.has_attr('src') else ""

            feed_items.append({'title': title, 'link': link, 'description': description, 'image': image_url})

        return feed_items

    def generate_rss():
        global latest_rss
        url = "https://www.imdb.com/calendar/?region=US&type=MOVIE"  # Change to target page
        feed_items = scrape_page(url)

        rss = ET.Element("rss", version="2.0")
        channel = ET.SubElement(rss, "channel")
        ET.SubElement(channel, "title").text = "IMDB Movies"
        ET.SubElement(channel, "link").text = url
        ET.SubElement(channel, "description").text = "Upcoming releases."

        for item in feed_items:
            item_element = ET.SubElement(channel, "item")
            ET.SubElement(item_element, "title").text = item['title']
            ET.SubElement(item_element, "link").text = item['link']
            ET.SubElement(item_element, "description").text = item['description']

            if item['image']:
                ET.SubElement(item_element, "enclosure", url=item['image'], type="image/jpeg")

        latest_rss = ET.tostring(rss, encoding="utf-8", method="xml").decode("utf-8")

    # Flask endpoint to serve the RSS feed
    @app.route("/imdb")
    def rss_feed():
        return Response(latest_rss, mimetype='application/rss+xml')

    # Schedule the feed update every 24 hours
    scheduler = BackgroundScheduler()
    scheduler.add_job(generate_rss, 'interval', hours=24)
    scheduler.start()

    # Generate RSS feed once at startup
    generate_rss()

except Exception as e:
    print(f"Error occurred: {str(e)}", file=sys.stderr)
    sys.exit(1)  # Exit with a non-zero status to signal failure

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)  # Change port to 8080 for App Runner
