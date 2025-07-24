from master_refresh import InventoryRefresher

"""Quick refresh script that scrapes only the first page of the eBay store.
This is useful for testing scraping changes without waiting for the full
inventory refresh."""


def main():
    refresher = InventoryRefresher()
    refresher.scrape_ebay_parts(max_pages=1)
    refresher.save_combined_listing_csv()
    refresher.process_vin_matching()
    refresher.organize_inventory_data()
    refresher.save_inventory_json()


if __name__ == "__main__":
    main()
