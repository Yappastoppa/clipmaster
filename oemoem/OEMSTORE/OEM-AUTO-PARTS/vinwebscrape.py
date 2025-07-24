import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import os

# Load VINs and part numbers from CSV
input_csv = "grouped_by_vin.csv"
output_csv = "donor_car.csv"

df = pd.read_csv(input_csv)

results = []


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


for index, row in df.iterrows():
    vin = row["VIN Number"]
    part_numbers = row.get("Part Numbers", "")

    print(f"\n🔍 Scraping data for VIN: {vin}...")
    car_data = scrape_car_data(vin)

    if car_data:
        car_data["Parts Available"] = part_numbers
        results.append(car_data)

    time.sleep(1)

pd.DataFrame(results).to_csv(output_csv, index=False)
print(f"\n✅ Scraping complete! Saved {len(results)} donor cars to {output_csv}.")
