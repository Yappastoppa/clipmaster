import csv
import requests
from bs4 import BeautifulSoup
import time
import random
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to scrape a single page
def scrape_page(page_url, csv_writer, headers, current_page):
    try:
        response = requests.get(page_url, headers=headers)
        logging.info(f"Response status code: {response.status_code}")  # Log status code
        
        if response.status_code != 200:
            logging.error(f"Failed to retrieve page: {response.status_code}")
            return False
            
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = soup.find_all('article', {'class': 'str-item-card'})

        if not articles:  # Check if there are no articles found
            logging.info("No articles found on the page.")
            return False

        items_scraped = 0
        for article in articles:
            # Try different selectors for title and price
            title_element = (article.find('span', {'class': 'str-item-card__property-title'}) or 
                           article.find('h3', class_='s-item__title') or
                           article.find('a', class_='s-item__link'))
            
            price_element = (article.find('span', {'class': 'str-item-card__property-displayPrice'}) or
                           article.find('span', class_='s-item__price') or
                           article.find('span', class_='notranslate'))
            
            part_number = article.get('data-testid', f'PART_{current_page}_{items_scraped}')
            title = title_element.text.strip() if title_element else 'N/A'
            price = price_element.text.strip() if price_element else 'N/A'
            
            csv_writer.writerow([part_number, title, price])
            items_scraped += 1

        logging.info(f"Scraped {items_scraped} items from page {current_page}")

        # Check for next page with multiple possible selectors
        next_page_indicators = [
            soup.find('a', {'aria-label': f'Page {current_page + 1}'}),
            soup.find('a', class_='pagination__next'),
            soup.find('a', string='Next'),
            soup.find('a', attrs={'title': 'Next page'})
        ]
        
        has_next_page = any(indicator for indicator in next_page_indicators)
        
        # Also check if we have items - if no items, probably no more pages
        return has_next_page and items_scraped > 0

    except requests.RequestException as e:
        logging.error(f"Request failed: {e}")
        return False

# Main script
base_url = 'https://www.ebay.com/str/partsboxbelton?_ipg=72&_pgn='
headers = {
    'User-Agent': random.choice([
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
        'Mozilla/5.0 (Linux; Android 10; Pixel 3 XL) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Mobile Safari/537.36',
    ]),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive'
}

# Open CSV file for writing
with open('zz1ebay_parts.csv', mode='w', newline='', encoding='utf-8') as file:
    csv_writer = csv.writer(file)
    # Write the headers
    csv_writer.writerow(['Part Number', 'Title', 'Price'])

    page = 1
    max_pages = 50  # Safety limit to prevent infinite loops
    
    while page <= max_pages:
        url = f"{base_url}{page}"
        logging.info(f"Scraping page: {page}")

        next_page_exists = scrape_page(url, csv_writer, headers, page)
        if not next_page_exists:
            logging.info(f"No more pages found. Last page scraped: {page}")
            break

        page += 1
        time.sleep(random.uniform(2, 5))  # Random delay between 2 and 5 seconds
    
    if page > max_pages:
        logging.info(f"Reached maximum page limit of {max_pages}")
    
    logging.info(f"Scraping completed. Total pages processed: {page - 1}")
