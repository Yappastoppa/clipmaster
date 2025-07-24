
#!/usr/bin/env python3
"""
Test script to verify the complete data workflow after master_refresh.py runs
"""

import os
import csv
import json
import pandas as pd
from datetime import datetime

def check_file_exists(filepath, description):
    """Check if a file exists and print status"""
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        mod_time = datetime.fromtimestamp(os.path.getmtime(filepath))
        print(f"✅ {description}: EXISTS ({size:,} bytes, modified: {mod_time})")
        return True
    else:
        print(f"❌ {description}: MISSING")
        return False

def test_csv_structure(filepath, expected_headers, description):
    """Test CSV file structure"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            if filepath.endswith('combined_listing.csv'):
                reader = csv.reader(f, delimiter='\t')
            else:
                reader = csv.reader(f)
            
            headers = next(reader)
            row_count = sum(1 for _ in reader)
            
        print(f"📊 {description}: {row_count} rows, {len(headers)} columns")
        
        # Check for expected headers
        missing_headers = [h for h in expected_headers if h not in headers]
        if missing_headers:
            print(f"⚠️  Missing headers: {missing_headers}")
        else:
            print(f"✅ All expected headers present")
            
        return True
    except Exception as e:
        print(f"❌ Error reading {description}: {e}")
        return False

def test_json_structure(filepath, description):
    """Test JSON file structure"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, dict):
            brands = len(data.keys())
            total_parts = 0
            for brand in data:
                for model in data[brand]:
                    for year in data[brand][model]:
                        total_parts += len(data[brand][model][year])
            
            print(f"📊 {description}: {brands} brands, {total_parts} total parts")
        else:
            print(f"📊 {description}: {len(data)} items")
            
        return True
    except Exception as e:
        print(f"❌ Error reading {description}: {e}")
        return False

def main():
    print("🧪 TESTING COMPLETE DATA WORKFLOW")
    print("=" * 50)
    
    # Resolve data directory relative to this script so it works
    # regardless of the current working directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_path = os.path.join(script_dir, "OEMSTORE", "OEM-AUTO-PARTS")
    
    # Check all required files
    files_to_check = [
        (f"{base_path}/combined_listing.csv", "Combined Listing CSV"),
        (f"{base_path}/grouped_by_vin.csv", "Grouped by VIN CSV"),
        (f"{base_path}/donor_car.csv", "Donor Car CSV"),
        (f"{base_path}/inventory.json", "Inventory JSON")
    ]
    
    print("\n📁 FILE EXISTENCE CHECK:")
    all_files_exist = True
    for filepath, description in files_to_check:
        exists = check_file_exists(filepath, description)
        all_files_exist = all_files_exist and exists
    
    if not all_files_exist:
        print("\n❌ Some files are missing. Run master_refresh.py first!")
        return
    
    print("\n📋 STRUCTURE VALIDATION:")
    
    # Test combined_listing.csv structure
    combined_headers = ['*Title', 'Part Number', 'Car Brand', 'Year', 'PicURL']
    test_csv_structure(f"{base_path}/combined_listing.csv", combined_headers, "Combined Listing")
    
    # Test grouped_by_vin.csv structure
    vin_headers = ['VIN Number', 'Part Numbers']
    test_csv_structure(f"{base_path}/grouped_by_vin.csv", vin_headers, "VIN Groups")
    
    # Test donor_car.csv structure
    donor_headers = ['VIN Number', 'Year', 'Make', 'Model', 'Images']
    test_csv_structure(f"{base_path}/donor_car.csv", donor_headers, "Donor Cars")
    
    # Test inventory.json structure
    test_json_structure(f"{base_path}/inventory.json", "Inventory JSON")
    
    print("\n🔗 DATA RELATIONSHIP CHECK:")
    
    # Check if VIN numbers from grouped_by_vin exist in donor_car
    try:
        # Load VIN groups
        vin_groups = {}
        with open(f"{base_path}/grouped_by_vin.csv", 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                vin_groups[row['VIN Number']] = row['Part Numbers']
        
        # Load donor cars
        donor_vins = set()
        with open(f"{base_path}/donor_car.csv", 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                donor_vins.add(row['VIN Number'])
        
        # Check relationships
        matched_vins = set(vin_groups.keys()) & donor_vins
        print(f"📊 VIN Relationships: {len(matched_vins)} VINs have both parts and donor car data")
        print(f"📊 Total VINs with parts: {len(vin_groups)}")
        print(f"📊 Total donor cars: {len(donor_vins)}")
        
    except Exception as e:
        print(f"❌ Error checking VIN relationships: {e}")
    
    print("\n🎉 WORKFLOW TEST COMPLETE!")
    print("If all checks passed, your website should work properly.")

if __name__ == "__main__":
    main()
