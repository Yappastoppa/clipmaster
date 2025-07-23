import csv
import random
from tqdm import tqdm

def truncate_title(title, length=80):
    """Truncate title to a specified length and strip white spaces."""
    return title.strip()[:length]

def clean_text(text):
    """Remove 'Unknown Make Unknown Year' from the given text."""
    return text.replace("Unknown Make Unknown Year", "").strip()

def filter_listings(keyword, original_csv):
    filtered_parts = []
    keywords = keyword.lower().split()  # Split the input into separate words

    # Read the original CSV file
    with open(original_csv, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter='\t')
        for row in reader:
            title = row['*Title'].strip()
            # Check if all keywords are in the title
            if all(word in title.lower() for word in keywords):
                # Clean the title and description
                row['*Title'] = clean_text(truncate_title(title))  # Clean and truncate the title
                row['*Description'] = clean_text(row['*Description'])  # Clean the description
                row['Price'] = float(row['*StartPrice'])  # Convert price to float for sorting
                filtered_parts.append(row)

    return filtered_parts

def sort_listings(filtered_parts, count, sort_option):
    # Define price ranges
    price_ranges = {
        4: (1, 50),
        5: (100, 250),
        6: (250, 400),
        7: (400, 650),
        8: (650, 800),
        9: (800, 1500),
        10: (1500, 3000),
        11: (3000, float('inf'))  # 3000 and up
    }

    # Sorting or filtering based on user choice
    if sort_option in range(4, 12):
        lower_bound, upper_bound = price_ranges[sort_option]
        filtered_parts = [part for part in filtered_parts if lower_bound <= part['Price'] <= upper_bound]
    elif sort_option == 2:
        filtered_parts.sort(key=lambda x: x['Price'])  # Low-to-high
    elif sort_option == 3:
        filtered_parts.sort(key=lambda x: x['Price'], reverse=True)  # High-to-low
    elif sort_option == 1:
        random.shuffle(filtered_parts)  # Random

    # Remove the extra 'Price' field before returning
    for part in filtered_parts:
        part.pop('Price', None)

    return filtered_parts[:count]  # Return the specified number of listings

def create_csv_from_listings(listings, new_csv, fieldnames):
    # Write to a new CSV file
    with open(new_csv, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter='\t')
        writer.writeheader()

        # Iterate with a tqdm progress bar
        for part in tqdm(listings, desc="Writing items"):
            # Ensure the title and description are clean and properly truncated
            part['*Title'] = truncate_title(part['*Title'])
            part['*Description'] = clean_text(part['*Description'])
            assert len(part['*Title']) <= 80, f"Title exceeds 80 characters: {part['*Title']}"
            writer.writerow(part)

    print(f"CSV file '{new_csv}' has been created.")

# User input for filtering
keyword = input("Enter the keyword to filter (e.g., Dodge Charger): ").strip()
original_csv = 'ebay_listing.csv'
new_csv = f"{keyword.replace(' ', '_').lower()}_listings.csv"

# Filter listings
filtered_results = filter_listings(keyword, original_csv)
print(f"Total listings found: {len(filtered_results)}")

# User input for number of listings and sorting
number_of_listings = int(input("How many of these listings do you want to include? "))
sort_option = int(input("Select the sorting option (1: Random, 2: Price Low-High, 3: Price High-Low, 4: $1-$50, 5: $100-$250, 6: $250-$400, 7: $400-$650, 8: $650-$800, 9: $800-$1500, 10: $1500-$3000, 11: $3000 and up): "))

# Sort and create CSV
sorted_listings = sort_listings(filtered_results, number_of_listings, sort_option)
create_csv_from_listings(sorted_listings, new_csv, fieldnames=["Action(SiteID=US|Country=US|Currency=USD|Version=1193|CC=UTF-8)", "CustomLabel", "*Category", "*Title", "*ConditionID", "PicURL", "*Description", "*Format", "*Duration", "*StartPrice", "*Location", "ShippingType", "ShippingService-1:Option", "ShippingService-1:Cost", "*DispatchTimeMax", "*ReturnsAcceptedOption"])
