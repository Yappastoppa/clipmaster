import requests
import pandas as pd
import time

# Input and output CSV paths
INPUT_CSV = "grouped_by_vin.csv"
OUTPUT_CSV = "donor_car.csv"

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
            print(f"Failed VIN lookup {vin}: {resp.status_code}")
            return {}
        data = resp.json()
        parsed = {
            item["Variable"]: item["Value"]
            for item in data.get("Results", [])
            if item.get("Variable") and item.get("Value")
        }
        return parsed
    except Exception as e:
        print(f"Error fetching VIN {vin}: {e}")
        return {}


for _, row in df.iterrows():
    vin = row["VIN Number"]
    part_numbers = row.get("Part Numbers", "")
    print(f"Scraping {vin}...")

    decoded = decode_vin(vin)
    if not decoded:
        continue

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
        "Images": "",
    }

    results.append(car_data)
    time.sleep(0.2)

pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
print(f"Saved {len(results)} donor cars to {OUTPUT_CSV}")

