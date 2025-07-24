import requests
import pandas as pd
import time
import logging
import re

# Input and output CSV paths
INPUT_CSV = "grouped_by_vin.csv"
OUTPUT_CSV = "donor_car.csv"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

df = pd.read_csv(INPUT_CSV)
results = []


def decode_vin(vin: str) -> dict:
    """Query the NHTSA API for VIN details."""
    url = (
        f"https://vpic.nhtsa.dot.gov/api/vehicles/"
        f"decodevinextended/{vin}?format=json"
    )
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            logging.warning(f"Failed VIN lookup {vin}: {resp.status_code}")
            return {}
        data = resp.json()
        parsed = {
            item["Variable"]: item["Value"]
            for item in data.get("Results", [])
            if item.get("Variable") and item.get("Value")
        }
        return parsed
    except Exception as e:
        logging.error(f"Error fetching VIN {vin}: {e}")
        return {}


def scrape_donor_images(vin: str) -> list:
    """Retrieve donor car images for the given VIN."""
    try:
        # Placeholder scraping logic - this would normally fetch from an auction site
        images = []
        search_url = f"https://www.google.com/search?tbm=isch&q={vin}"
        resp = requests.get(search_url, timeout=10)
        if resp.status_code == 200:
            # Very naive extraction of image URLs
            matches = re.findall(r'https?://[^\s"]+\.(?:jpg|jpeg|png)', resp.text)
            images.extend(matches)

        if not images:
            logging.warning(f"No images found for VIN {vin}, using placeholder")
            return ["https://via.placeholder.com/600x400?text=Car+Image+Not+Available"]

        return images[:5]
    except Exception as e:
        logging.error(f"VIN {vin} image scraping failed: {e}")
        return []


for _, row in df.iterrows():
    vin = row["VIN Number"]
    part_numbers = row.get("Part Numbers", "")
    logging.info(f"Scraping {vin}...")

    decoded = decode_vin(vin)
    if not decoded:
        continue

    images = scrape_donor_images(vin)

    car_data = {
        "VIN Number": vin,
        "Make": decoded.get("Make", ""),
        "Model": decoded.get("Model", ""),
        "Model Year": decoded.get("Model Year", ""),
        "Vehicle Type": decoded.get("Vehicle Type", ""),
        "Body Class": decoded.get("Body Class", ""),
        "Engine Model": decoded.get("Engine Model", ""),
        "Fuel Type": decoded.get("Fuel Type - Primary", ""),
        "Parts Available": part_numbers,
        "Images": " | ".join(images),
    }

    results.append(car_data)
    time.sleep(0.2)

pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
logging.info(f"Saved {len(results)} donor cars to {OUTPUT_CSV}")

