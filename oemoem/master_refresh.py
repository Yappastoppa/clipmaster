import requests
import json
import re
import csv
import pandas as pd
from bs4 import BeautifulSoup
import time
import random
import logging
import os
import shutil
import subprocess
from collections import defaultdict
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class InventoryRefresher:
    def __init__(self):
        self.base_path = "OEMSTORE/OEM-AUTO-PARTS"
        self.all_parts_data = []
        self.inventory_data = {}

    def backup_existing_files(self):
        """Backup existing files before overwriting"""
        logging.info("💾 Backing up existing files...")

        files_to_backup = [
            "combined_listing.csv",
            "grouped_by_vin.csv",
            "donor_car.csv",
            "inventory.json",
        ]

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for filename in files_to_backup:
            file_path = f"{self.base_path}/{filename}"
            if os.path.exists(file_path):
                backup_path = f"{self.base_path}/{filename}_backup_{timestamp}"
                try:
                    shutil.copy2(file_path, backup_path)
                    logging.info(f"✅ {filename} backed up to: {backup_path}")
                except Exception as e:
                    logging.error(f"❌ Failed to backup {filename}: {e}")
            else:
                logging.info(f"ℹ️ No existing {filename} to backup")

        return True

    def extract_car_info(self, title):
        """Extract car brand, model, and year from title"""
        brands = [
            "FISKER",
            "BMW",
            "MERCEDES-BENZ",
            "MERCEDES",
            "AUDI",
            "FORD",
            "CHEVROLET",
            "TOYOTA",
            "HONDA",
            "NISSAN",
            "HYUNDAI",
            "KIA",
            "VOLKSWAGEN",
            "LEXUS",
            "ACURA",
            "INFINITI",
            "CADILLAC",
            "LINCOLN",
            "BUICK",
            "GMC",
            "JEEP",
            "CHRYSLER",
            "DODGE",
            "RAM",
            "SUBARU",
            "MAZDA",
            "MITSUBISHI",
            "VOLVO",
            "JAGUAR",
            "LAND ROVER",
            "PORSCHE",
            "TESLA",
            "FERRARI",
            "LAMBORGHINI",
            "MASERATI",
            "BENTLEY",
            "ROLLS-ROYCE",
        ]

        try:
            title_upper = title.upper()

            # Extract years
            year_patterns = [
                r"\b(19|20)\d{2}\s*[-–]\s*(19|20)\d{2}\b",  # Year ranges like 2018-2021
                r"\b(19|20)\d{2}\b",  # Single years
            ]

            year = "Unknown"
            for pattern in year_patterns:
                year_match = re.search(pattern, title)
                if year_match:
                    year_str = year_match.group()
                    if "-" in year_str or "–" in year_str:
                        year = re.search(r"\b(19|20)\d{2}\b", year_str).group()
                    else:
                        year = year_str
                    break

            # Extract brand
            brand = "Unknown Make"
            if "MERCEDES-BENZ" in title_upper:
                brand = "MERCEDES-BENZ"
            else:
                for b in brands:
                    if b in title_upper:
                        brand = b
                        break

            # Extract model
            model = "UNKNOWN"
            if brand != "Unknown Make":
                brand_index = title_upper.find(brand)
                after_brand = title[brand_index + len(brand) :].strip()
                after_brand = re.sub(r"^\s*[-–]\s*", "", after_brand)
                after_brand = re.sub(
                    r"^\s*(OEM|ORIGINAL|GENUINE)\s+",
                    "",
                    after_brand,
                    flags=re.IGNORECASE,
                )
                words = after_brand.split()
                model_words = []

                for word in words[:4]:
                    word = word.strip("(),.-")
                    if (
                        not re.match(r"\b(19|20)\d{2}\b", word)
                        and word.upper()
                        not in ["OEM", "ORIGINAL", "GENUINE", "USED", "NEW"]
                        and len(word) > 1
                        and not word.isdigit()
                    ):
                        model_words.append(word)

                if model_words:
                    model = " ".join(model_words[:2])

                # Special handling for common models
                model_upper = model.upper()
                if brand == "FORD":
                    if "F150" in model_upper or "F-150" in model_upper:
                        model = "F150"
                    elif "F250" in model_upper or "F-250" in model_upper:
                        model = "F250"
                    elif "F350" in model_upper or "F-350" in model_upper:
                        model = "F350"
                elif brand == "BMW":
                    bmw_model = re.search(r"\b([XM]?\d{3,4}[A-Z]*)\b", model_upper)
                    if bmw_model:
                        model = bmw_model.group(1)

            return brand, model.upper(), year
        except Exception as e:
            logging.error(f"Error extracting car info from '{title}': {e}")
            return "Unknown Make", "UNKNOWN", "Unknown"

    def parse_price(self, price_str):
        """Convert price string to float"""
        try:
            if not price_str or price_str == "N/A":
                return 0.0
            price_clean = re.sub(r"[^\d.]", "", price_str)
            return float(price_clean) if price_clean else 0.0
        except Exception as e:
            logging.error(f"Error parsing price '{price_str}': {e}")
            return 0.0

    def extract_item_details(self, article, headers):
        """Extract detailed item information including all images and VIN from item specifics"""
        try:
            # Get the item link for detailed scraping
            link_element = article.find(
                "a", class_="str-item-card__property-title-link"
            ) or article.find("a", href=True)

            if link_element:
                item_url = link_element.get("href", "")
            else:
                item_url = ""

            if not item_url:
                # Fallback: attempt to extract itemId from data attributes
                data_view = article.get("data-view", "")
                match = re.search(r'"itemId":"(\d+)"', data_view)
                if match:
                    item_url = f"https://www.ebay.com/itm/{match.group(1)}"

            if not item_url:
                return None, []

            # Get detailed item page
            detail_response = requests.get(item_url, headers=headers, timeout=10)
            if detail_response.status_code != 200:
                return None, []

            detail_soup = BeautifulSoup(detail_response.content, "html.parser")

            # Extract all images
            all_images = []

            # Gather all <img> tags and capture full resolution URLs
            for img in detail_soup.find_all("img"):
                src = img.get("src") or img.get("data-src") or ""
                if src and "ebayimg.com" in src:
                    high_res = (
                        src.replace("s-l64.", "s-l1600.")
                        .replace("s-l225.", "s-l1600.")
                        .replace("s-l300.", "s-l1600.")
                    )
                    all_images.append(high_res)

            # Fallback: search HTML text for any s-l1600 images
            regex_images = re.findall(
                r'https://i\.ebayimg\.com/[^"\s>]+s-l1600\.(?:jpg|jpeg|png|webp)',
                detail_response.text,
            )
            all_images.extend(regex_images)

            # Remove duplicates and filter out known stock images
            stock_patterns = ["hVAAAOSwxiRnx4LA"]

            unique_images = []
            seen = set()
            for img in all_images:
                clean_img = img.split("?")[0]
                if any(pat in clean_img for pat in stock_patterns):
                    continue
                if clean_img not in seen:
                    unique_images.append(clean_img)
                    seen.add(clean_img)

            # Extract VIN from item specifics
            vin_number = "Not found"
            text_content = ""
            specifics_section = detail_soup.find("div", class_="u-flL condText")
            if not specifics_section:
                specifics_section = detail_soup.find("div", {"id": "viTabs_0_is"})

            if specifics_section:
                text_content = specifics_section.get_text().upper()

            if not text_content:
                text_content = detail_soup.get_text().upper()

            vin_patterns = [
                r"VIN[:\s]*([A-HJ-NPR-Z0-9]{17})",
                r"VEHICLE\s+IDENTIFICATION\s+NUMBER[:\s]*([A-HJ-NPR-Z0-9]{17})",
                r"\b([A-HJ-NPR-Z0-9]{17})\b",
            ]

            for pattern in vin_patterns:
                vin_match = re.search(pattern, text_content)
                if vin_match:
                    potential_vin = vin_match.group(1)
                    if len(potential_vin) == 17 and potential_vin.isalnum():
                        vin_number = potential_vin
                        break

            return vin_number, unique_images

        except Exception as e:
            logging.error(f"Error extracting item details: {e}")
            return None, []

    def is_valid_part_title(self, title):
        """Check if title represents an actual part, not just a brand name"""
        title_upper = title.upper()

        # Filter out brand-only entries
        brand_only_patterns = [
            r"^(FORD|BMW|MERCEDES|AUDI|TOYOTA|HONDA|NISSAN|HYUNDAI|KIA|VOLKSWAGEN)(\s+.*)?$",
            r"^[A-Z]+\s*$",  # Just letters
            r"^[A-Z]+\s+[A-Z]+\s*$",  # Two words, all caps (likely brand/model only)
        ]

        for pattern in brand_only_patterns:
            if re.match(pattern, title_upper) and len(title.split()) <= 2:
                return False

        # Must contain part-related keywords
        part_keywords = [
            "OEM",
            "PART",
            "ASSEMBLY",
            "MODULE",
            "SENSOR",
            "PUMP",
            "FILTER",
            "BRAKE",
            "ENGINE",
            "TRANSMISSION",
            "WHEEL",
            "RIM",
            "HEADLIGHT",
            "TAILLIGHT",
            "MIRROR",
            "DOOR",
            "BUMPER",
            "FENDER",
            "HOOD",
            "TRUNK",
            "SEAT",
            "DASHBOARD",
            "STEERING",
            "SUSPENSION",
            "EXHAUST",
            "RADIATOR",
            "ALTERNATOR",
            "STARTER",
            "BATTERY",
            "WIRE",
            "HARNESS",
            "ECU",
            "ECM",
        ]

        return any(keyword in title_upper for keyword in part_keywords)

    def scrape_single_page(self, page_url, headers, current_page):
        """Scrape a single page of eBay parts"""
        try:
            response = requests.get(page_url, headers=headers, timeout=15)
            logging.info(
                f"📡 Page {current_page} response status: {response.status_code}"
            )

            if response.status_code != 200:
                logging.error(
                    f"Failed to retrieve page {current_page}: {response.status_code}"
                )
                return False, []

            soup = BeautifulSoup(response.content, "html.parser")
            articles = soup.find_all("article", {"class": "str-item-card"})

            if not articles:
                logging.info(f"No articles found on page {current_page}")
                return False, []

            page_parts = []
            for i, article in enumerate(articles):
                try:
                    title_element = (
                        article.find("span", {"class": "str-item-card__property-title"})
                        or article.find("h3", class_="s-item__title")
                        or article.find("a", class_="s-item__link")
                    )

                    price_element = (
                        article.find(
                            "span", {"class": "str-item-card__property-displayPrice"}
                        )
                        or article.find("span", class_="s-item__price")
                        or article.find("span", class_="notranslate")
                    )

                    title = title_element.text.strip() if title_element else "N/A"

                    # Skip if not a valid part
                    if not self.is_valid_part_title(title):
                        logging.info(f"Skipping brand-only entry: {title}")
                        continue

                    price_str = price_element.text.strip() if price_element else "N/A"
                    price = self.parse_price(price_str)

                    # Extract detailed information including all images and VIN
                    vin_number, all_images = self.extract_item_details(article, headers)
                    if vin_number is None:
                        vin_number = "Not found"
                    if not all_images:
                        # Fallback to basic image extraction
                        image_element = article.find("img")
                        if image_element:
                            basic_image = image_element.get("src", "")
                            if basic_image:
                                all_images = [basic_image]

                    # Join all images with pipe separator
                    image_urls = " | ".join(all_images) if all_images else ""

                    brand, model, year = self.extract_car_info(title)

                    part_data = {
                        "title": title,
                        "price": price,
                        "image": image_urls,  # All images separated by pipes
                        "description": f"OEM part from {brand} {model} {year}",
                        "part_number": f"{brand}_{current_page}_{i}_{int(time.time())}",
                        "brand": brand,
                        "model": model,
                        "year": year,
                        "vin_number": vin_number,
                        "scraped_price": f"${price:.2f}",
                        "original_price": f"${price:.2f}",
                        "pic_url": image_urls,
                        "category": "Auto Parts",
                        "condition_id": "Used",
                        "format": "FixedPrice",
                        "duration": "GTC",
                        "start_price": f"${price:.2f}",
                        "location": "US",
                        "shipping_type": "Flat",
                        "shipping_service_1_option": "USPSFirstClass",
                        "shipping_service_1_cost": "29.98",
                        "dispatch_time_max": "3",
                        "returns_accepted_option": "ReturnsAccepted",
                        "compatibilities": f"{brand} {model} {year}",
                    }

                    page_parts.append(part_data)

                    # Small delay between detailed requests
                    time.sleep(0.5)

                except Exception as e:
                    logging.error(
                        f"Error processing article {i} on page {current_page}: {e}"
                    )
                    continue

            logging.info(
                f"✅ Scraped {len(page_parts)} valid items from page {current_page}"
            )

            # Better pagination detection
            has_next_page = False
            if len(page_parts) > 0:
                next_page_indicators = [
                    soup.find("a", {"aria-label": f"Page {current_page + 1}"}),
                    soup.find("a", class_="pagination__next"),
                    soup.find("a", string="Next"),
                    soup.find("a", attrs={"title": "Next page"}),
                    soup.find("a", attrs={"aria-label": "Next page"}),
                ]

                pagination_links = soup.find_all(
                    "a", {"aria-label": re.compile(r"Page \d+")}
                )
                max_page_found = current_page
                for link in pagination_links:
                    try:
                        page_match = re.search(
                            r"Page (\d+)", link.get("aria-label", "")
                        )
                        if page_match:
                            page_num = int(page_match.group(1))
                            max_page_found = max(max_page_found, page_num)
                    except:
                        pass

                has_next_page = (
                    any(indicator for indicator in next_page_indicators)
                    or current_page < max_page_found
                )

            return has_next_page, page_parts

        except requests.RequestException as e:
            logging.error(f"Request failed for page {current_page}: {e}")
            return False, []
        except Exception as e:
            logging.error(f"Unexpected error on page {current_page}: {e}")
            return False, []

    def scrape_ebay_parts(self, max_pages: int = 20):
        """Scrape parts from eBay store

        Parameters
        ----------
        max_pages: int, optional
            Maximum number of pages to scrape. Defaults to 20 for a full
            refresh but can be lowered for quicker testing.
        """
        logging.info("🔄 Starting eBay parts scraping...")

        base_url = "https://www.ebay.com/str/partsboxbelton?_ipg=72&_pgn="
        headers = {
            "User-Agent": random.choice(
                [
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
                    "Mozilla/5.0 (Linux; Android 10; Pixel 3 XL) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Mobile Safari/537.36",
                ]
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
        }

        self.all_parts_data = []

        try:
            test_url = f"{base_url}1"
            logging.info(f"🧪 Testing eBay access: {test_url}")

            response = requests.get(test_url, headers=headers, timeout=15)
            logging.info(f"📡 Response status: {response.status_code}")

            if response.status_code != 200:
                logging.error(
                    f"❌ Cannot access eBay store. Status: {response.status_code}"
                )
                return False

            soup = BeautifulSoup(response.content, "html.parser")
            articles = soup.find_all("article", {"class": "str-item-card"})
            logging.info(f"🔍 Found {len(articles)} items on first page")

            if not articles:
                logging.error(
                    "❌ No items found on eBay page. Structure may have changed."
                )
                return False

            # Start scraping all pages
            page = 1
            total_parts = 0

            while page <= max_pages:
                url = f"{base_url}{page}"
                logging.info(f"🔄 Scraping page {page}...")

                has_next_page, page_parts = self.scrape_single_page(url, headers, page)

                if page_parts:
                    self.all_parts_data.extend(page_parts)
                    total_parts += len(page_parts)
                    logging.info(f"📊 Total parts scraped so far: {total_parts}")

                if not page_parts:
                    logging.info(f"🏁 No more items found. Last page scraped: {page}")
                    break

                page += 1

                delay = random.uniform(
                    3, 6
                )  # Slightly longer delay for detailed scraping
                logging.info(f"⏳ Waiting {delay:.1f}s before next page...")
                time.sleep(delay)

            if page > max_pages:
                logging.info(f"⚠️ Reached maximum page limit of {max_pages}")

            logging.info(
                f"✅ eBay scraping completed! Total parts: {len(self.all_parts_data)}"
            )
            return len(self.all_parts_data) > 0

        except Exception as e:
            logging.error(f"❌ Error during eBay scraping: {e}")
            return False

    def save_combined_listing_csv(self):
        """Save scraped data to combined_listing.csv in the format expected by the website"""
        logging.info("💾 Saving combined_listing.csv...")

        if not self.all_parts_data:
            logging.error("No parts data to save")
            return False

        output_path = f"{self.base_path}/combined_listing.csv"

        try:
            # Define CSV headers to match your website's expectations
            headers = [
                "*Title",
                "Scraped Price",
                "Original Price",
                "PicURL",
                "*Description",
                "Part Number",
                "Car Brand",
                "Manufacturer Part Number",
                "Year",
                "Car Model",
                "Stock Number",
                "VIN Number",
                "NumbeVINr",
                "*Category",
                "*ConditionID",
                "*Format",
                "*Duration",
                "*StartPrice",
                "*Location",
                "ShippingType",
                "ShippingService-1:Option",
                "ShippingService-1:Cost",
                "*DispatchTimeMax",
                "*ReturnsAcceptedOption",
                "Compatibilities",
            ]

            with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile, delimiter="\t")
                writer.writerow(headers)

                for part in self.all_parts_data:
                    row = [
                        part.get("title", ""),  # *Title
                        part.get("scraped_price", ""),  # Scraped Price
                        part.get("original_price", ""),  # Original Price
                        part.get("pic_url", ""),  # PicURL
                        part.get("description", ""),  # *Description
                        part.get("part_number", ""),  # Part Number
                        part.get("brand", ""),  # Car Brand
                        part.get("part_number", ""),  # Manufacturer Part Number
                        part.get("year", ""),  # Year
                        part.get("model", ""),  # Car Model
                        part.get("part_number", ""),  # Stock Number
                        part.get("vin_number", "Not found"),  # VIN Number
                        part.get("vin_number", "Not found"),  # NumbeVINr
                        part.get("category", ""),  # *Category
                        part.get("condition_id", ""),  # *ConditionID
                        part.get("format", ""),  # *Format
                        part.get("duration", ""),  # *Duration
                        part.get("start_price", ""),  # *StartPrice
                        part.get("location", ""),  # *Location
                        part.get("shipping_type", ""),  # ShippingType
                        part.get(
                            "shipping_service_1_option", ""
                        ),  # ShippingService-1:Option
                        part.get(
                            "shipping_service_1_cost", ""
                        ),  # ShippingService-1:Cost
                        part.get("dispatch_time_max", ""),  # *DispatchTimeMax
                        part.get(
                            "returns_accepted_option", ""
                        ),  # *ReturnsAcceptedOption
                        part.get("compatibilities", ""),  # Compatibilities
                    ]
                    writer.writerow(row)

            logging.info(
                f"✅ Combined listing CSV saved with {len(self.all_parts_data)} parts"
            )
            return True

        except Exception as e:
            logging.error(f"Error saving combined_listing.csv: {e}")
            return False

    def organize_inventory_data(self):
        """Organize parts data into inventory.json format"""
        logging.info("📦 Organizing inventory data...")

        if not self.all_parts_data:
            logging.error("No parts data to organize")
            return False

        inventory = {}
        for part in self.all_parts_data:
            try:
                brand = part.get("brand", "Unknown Make")
                model = part.get("model", "UNKNOWN")
                year = part.get("year", "Unknown")

                if brand not in inventory:
                    inventory[brand] = {}
                if model not in inventory[brand]:
                    inventory[brand][model] = {}
                if year not in inventory[brand][model]:
                    inventory[brand][model][year] = []

                part_entry = {
                    "title": part.get("title", ""),
                    "price": part.get("price", 0),
                    "image": part.get("image", ""),
                    "description": part.get("description", ""),
                    "shipping_option": part.get(
                        "shipping_service_1_option", "USPSFirstClass"
                    ),
                    "shipping_cost": float(
                        part.get("shipping_service_1_cost", "29.98")
                    ),
                }

                inventory[brand][model][year].append(part_entry)

            except Exception as e:
                logging.error(
                    f"Error organizing part '{part.get('title', 'Unknown')}': {e}"
                )
                continue

        self.inventory_data = inventory
        logging.info(
            f"✅ Organized {len(inventory)} brands with {len(self.all_parts_data)} total parts"
        )
        return True

    def save_inventory_json(self):
        """Save organized inventory to JSON file"""
        logging.info("💾 Saving inventory.json...")

        if not self.inventory_data:
            logging.error("No inventory data to save")
            return False

        output_path = f"{self.base_path}/inventory.json"

        try:
            with open(output_path, "w", encoding="utf-8") as json_file:
                json.dump(self.inventory_data, json_file, ensure_ascii=False, indent=4)

            logging.info(f"✅ Inventory JSON saved: {len(self.inventory_data)} brands")
            return True

        except Exception as e:
            logging.error(f"Error saving inventory.json: {e}")
            return False

    def process_vin_matching(self):
        """Process VIN matching and donor car data"""
        logging.info("🔄 Processing VIN matching and donor car data...")

        try:
            # Run VIN matching script
            logging.info("📋 Running VIN matching...")
            vin_match_path = os.path.join(self.base_path, "vin match.py")
            if os.path.exists(vin_match_path):
                result = subprocess.run(
                    ["python", "vin match.py"],
                    cwd=self.base_path,
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    logging.info("✅ VIN matching completed successfully")
                    logging.info(f"VIN matching output: {result.stdout}")
                else:
                    logging.warning(f"⚠️ VIN matching had issues: {result.stderr}")
            else:
                logging.warning("⚠️ VIN match script not found, skipping VIN matching")

            # Run VIN web scraping
            logging.info("🌐 Running VIN web scraping...")
            vinwebscrape_path = os.path.join(self.base_path, "vinwebscrape.py")
            if os.path.exists(vinwebscrape_path):
                result = subprocess.run(
                    ["python", "vinwebscrape.py"],
                    cwd=self.base_path,
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    logging.info("✅ VIN web scraping completed successfully")
                    logging.info(f"VIN scraping output: {result.stdout}")
                else:
                    logging.warning(f"⚠️ VIN web scraping had issues: {result.stderr}")
            else:
                logging.warning(
                    "⚠️ VIN web scrape script not found, skipping VIN scraping"
                )

            return True

        except Exception as e:
            logging.error(f"❌ VIN processing failed: {e}")
            return False

    def run_full_refresh(self):
        """Execute complete inventory refresh process"""
        logging.info("🚀 Starting FULL INVENTORY REFRESH...")

        # Ensure output directory exists
        try:
            os.makedirs(self.base_path, exist_ok=True)
        except Exception as e:
            logging.error(f"Failed to create output directory: {e}")
            return False

        # Step 1: Backup existing files
        if not self.backup_existing_files():
            logging.warning("⚠️ Backup failed but continuing with refresh...")

        steps = [
            ("Scraping eBay Parts", self.scrape_ebay_parts),
            ("Saving Combined Listing CSV", self.save_combined_listing_csv),
            ("Processing VIN Matching", self.process_vin_matching),
            ("Organizing Inventory Data", self.organize_inventory_data),
            ("Saving Inventory JSON", self.save_inventory_json),
        ]

        for step_name, step_function in steps:
            logging.info(f"⏳ {step_name}...")
            try:
                success = step_function()
                if success:
                    logging.info(f"✅ {step_name} completed successfully")
                else:
                    logging.error(f"❌ {step_name} failed")
                    logging.info("🛑 Stopping refresh due to failure")
                    return False
            except Exception as e:
                logging.error(f"❌ {step_name} failed with error: {e}")
                logging.info("🛑 Stopping refresh due to unexpected error")
                return False

        logging.info("🎉 FULL INVENTORY REFRESH COMPLETED SUCCESSFULLY!")
        logging.info(f"📊 Final Summary:")
        logging.info(f"   • Total parts scraped: {len(self.all_parts_data)}")
        logging.info(f"   • Brands organized: {len(self.inventory_data)}")
        logging.info(
            f"   • Files updated: combined_listing.csv, grouped_by_vin.csv, donor_car.csv, inventory.json"
        )
        logging.info("🔄 Your website is now fully updated!")

        return True


def main():
    refresher = InventoryRefresher()
    success = refresher.run_full_refresh()

    if not success:
        logging.error("❌ INVENTORY REFRESH FAILED!")
        exit(1)


if __name__ == "__main__":
    main()
