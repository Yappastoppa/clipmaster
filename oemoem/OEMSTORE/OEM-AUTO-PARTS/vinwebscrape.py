import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
from tqdm import tqdm  # Progress bar
import os

# Load VINs and part numbers from CSV
input_csv = "grouped_by_vin.csv"
output_csv = "donor_car.csv"

df = pd.read_csv(input_csv)

# Check if output CSV exists, and load existing data
if os.path.exists(output_csv):
    existing_df = pd.read_csv(output_csv)
    processed_vins = set(existing_df["VIN Number"].tolist())  # Track already scraped VINs
else:
    existing_df = pd.DataFrame()
    processed_vins = set()


# Function to scrape car data
def scrape_car_data(vin):
    url = f"https://carcheck.by/en/auto/{vin}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"⚠️ Failed to fetch data for VIN {vin}. Status code: {response.status_code}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # Extract vehicle details dynamically
    vehicle_info = {"VIN Number": vin}
    info_blocks = soup.find_all("div", class_="block")

    for block in info_blocks:
        key_span = block.find("span")
        if key_span and key_span.text.strip():  # Ensure it's valid
            key = block.text.replace(key_span.text, "").strip()
            value = key_span.text.strip()
            vehicle_info[key] = value

    # Extract images from "owl_big" carousel
    owl_big = soup.find("div", id="owl_big")
    image_urls = []

    if owl_big:
        image_tags = owl_big.find_all("img", src=True)  # Find all image tags
        image_urls = [img["src"] for img in image_tags]

    # Store extracted images
    vehicle_info["Images"] = ", ".join(image_urls) if image_urls else "No Images Found"

    return vehicle_info


# Open the CSV in append mode to write data live
with tqdm(total=len(df), desc="Scraping VINs", unit="VIN") as pbar:
    for index, row in df.iterrows():
        vin = row["VIN Number"]
        part_numbers = row["Part Numbers"] if "Part Numbers" in row else ""

        # Skip already processed VINs
        if vin in processed_vins:
            print(f"⏭️ Skipping already processed VIN: {vin}")
            pbar.update(1)
            continue

        print(f"\n🔍 Scraping data for VIN: {vin}...")
        car_data = scrape_car_data(vin)

        if car_data:
            car_data["Parts Available"] = part_numbers

            # Convert to DataFrame and append live
            new_entry_df = pd.DataFrame([car_data])
            new_entry_df.to_csv(output_csv, mode="a", header=not os.path.exists(output_csv), index=False)

            print(f"✅ Successfully saved data for VIN: {vin}")

        # Sleep to avoid getting blocked
        time.sleep(1)  

        # Update progress bar
        pbar.update(1)

print(f"\n✅ Scraping complete! Data saved live in {output_csv}.")
