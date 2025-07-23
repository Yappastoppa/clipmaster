import csv
from collections import defaultdict

INPUT_CSV = "combined_listing.csv"
OUTPUT_CSV = "grouped_by_vin.csv"

def group_parts_by_vin(input_file):
    groups = defaultdict(list)
    total_rows = 0
    valid_vin_count = 0

    with open(input_file, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter="\t")
        # Clean header names by stripping whitespace
        reader.fieldnames = [field.strip() for field in reader.fieldnames]
        print("CSV header:", reader.fieldnames)
        for row in reader:
            total_rows += 1
            # Use the actual header key from your CSV
            vin = row.get("NumbeVINr", "").strip()
            part_number = row.get("Part Number", "").strip()
            # Only group rows if VIN exists and is not "Not found"
            if vin and vin.lower() != "not found":
                valid_vin_count += 1
                groups[vin].append(part_number)
    return groups, total_rows, valid_vin_count

def write_grouped_csv(groups, output_file):
    with open(output_file, mode="w", newline='', encoding='utf-8') as csvfile:
        fieldnames = ["VIN Number", "Part Numbers"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for vin, part_list in groups.items():
            writer.writerow({
                "VIN Number": vin,
                "Part Numbers": ", ".join(part_list)
            })

if __name__ == "__main__":
    groups, total_rows, valid_vin_count = group_parts_by_vin(INPUT_CSV)
    print(f"Total rows read: {total_rows}")
    print(f"Rows with valid VINs: {valid_vin_count}")
    print(f"Total unique VIN groups: {len(groups)}")
    
    if not groups:
        print("No groups found. Please verify that your CSV file contains data and the header names are correct.")
    else:
        write_grouped_csv(groups, OUTPUT_CSV)
        print(f"Output written to {OUTPUT_CSV}")
