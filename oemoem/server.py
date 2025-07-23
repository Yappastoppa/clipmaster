
from flask import Flask, request, jsonify, render_template, send_from_directory
import json
import os
import csv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='OEMSTORE/OEM-AUTO-PARTS', template_folder='OEMSTORE/OEM-AUTO-PARTS')

# Route to serve the main index page
@app.route('/')
def index():
    return send_from_directory('OEMSTORE/OEM-AUTO-PARTS', 'index.html')

# Route to serve HTML files
@app.route('/<path:filename>')
def serve_files(filename):
    return send_from_directory('OEMSTORE/OEM-AUTO-PARTS', filename)

# API route for parts search
@app.route('/api/search', methods=['GET'])
def search_parts():
    query = request.args.get('q', '')
    logger.info(f"API search request for: {query}")
    
    try:
        # First try to load from combined_listing.csv
        parts = []
        csv_path = 'OEMSTORE/OEM-AUTO-PARTS/combined_listing.csv'
        
        if os.path.exists(csv_path):
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter='\t')
                for row in reader:
                    title = row.get('*Title', '') or row.get('Scraped Title', '') or row.get('Original Title', '')
                    part_number = row.get('Part Number', '')
                    
                    if query.lower() in title.lower() or query.lower() in part_number.lower():
                        parts.append({
                            'title': title,
                            'part_number': part_number,
                            'price': row.get('Scraped Price', '') or row.get('Original Price', ''),
                            'image': row.get('PicURL', ''),
                            'brand': row.get('Car Brand', ''),
                            'year': row.get('Year', ''),
                            'model': row.get('Car Model', '')
                        })
        
        # Fallback to inventory.json
        if not parts:
            inventory_path = 'OEMSTORE/OEM-AUTO-PARTS/inventory.json'
            if os.path.exists(inventory_path):
                with open(inventory_path, 'r') as f:
                    inventory = json.load(f)
                
                # Search through inventory structure
                for brand in inventory:
                    for model in inventory[brand]:
                        for year in inventory[brand][model]:
                            for part in inventory[brand][model][year]:
                                if query.lower() in part.get('title', '').lower():
                                    parts.append(part)
        
        logger.info(f"Found {len(parts)} results for query: {query}")
        return jsonify(parts[:50])  # Limit results
        
    except Exception as e:
        logger.error(f"Error in search_parts: {str(e)}")
        return jsonify([])

# API route for VIN lookup
@app.route('/api/vin-lookup', methods=['POST'])
def vin_lookup():
    data = request.json
    vin = data.get('vin', '')
    logger.info(f"VIN lookup request for: {vin}")
    
    try:
        parts = []
        grouped_vin_path = 'OEMSTORE/OEM-AUTO-PARTS/grouped_by_vin.csv'
        
        if os.path.exists(grouped_vin_path):
            with open(grouped_vin_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('VIN Number', '') == vin:
                        part_numbers = row.get('Part Numbers', '').split(', ')
                        parts.extend([p.strip() for p in part_numbers if p.strip()])
                        break
        
        logger.info(f"Found {len(parts)} parts for VIN: {vin}")
        return jsonify({'vin': vin, 'parts': parts})
        
    except Exception as e:
        logger.error(f"Error in vin_lookup: {str(e)}")
        return jsonify({'vin': vin, 'parts': []})

# API route for cart operations
@app.route('/api/cart', methods=['POST'])
def add_to_cart():
    data = request.json
    print(f"Item added to cart: {data}")
    return jsonify({'status': 'success', 'message': 'Item added to cart'})

# API route to check data status
@app.route('/api/status', methods=['GET'])
def data_status():
    """Check the status of data files and their last update times"""
    try:
        files_status = {}
        base_path = 'OEMSTORE/OEM-AUTO-PARTS'
        
        files_to_check = [
            'combined_listing.csv',
            'grouped_by_vin.csv', 
            'donor_car.csv',
            'inventory.json'
        ]
        
        for filename in files_to_check:
            filepath = os.path.join(base_path, filename)
            if os.path.exists(filepath):
                stat = os.stat(filepath)
                files_status[filename] = {
                    'exists': True,
                    'size': stat.st_size,
                    'last_modified': stat.st_mtime
                }
            else:
                files_status[filename] = {'exists': False}
        
        return jsonify({
            'status': 'success',
            'files': files_status,
            'message': 'Data status retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error in data_status: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Fern button endpoint (from your previous conversation)
@app.route('/fern-button', methods=['POST'])
def fern_button():
    data = request.json
    print("Fern button pressed with data:", data)
    response = {"message": "Fern button is successfully activated!"}
    return jsonify(response), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
