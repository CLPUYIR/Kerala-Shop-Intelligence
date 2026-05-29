import os
import sys
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import asyncio

# Ensure project root is in PYTHONPATH
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

from config import INPUT_CSV
from database.db_setup import init_db, ShopRecord
from scraper.playwright_engine import GoogleMapsScraper
from ai.query_builder import QueryBuilder

def load_initial_data(session):
    """Load data from CSV into SQLite if the database is empty."""
    if session.query(ShopRecord).count() > 0:
        print("Database already populated. Skipping initial load.")
        return

    print(f"Loading data from {INPUT_CSV}...")
    if not os.path.exists(INPUT_CSV):
        print(f"Error: {INPUT_CSV} not found.")
        return
        
    df = pd.read_csv(INPUT_CSV)
    
    records_to_add = []
    for _, row in tqdm(df.iterrows(), total=len(df)):
        record = ShopRecord(
            shop_no=str(row.get('Shop_No', '')),
            original_name=str(row.get('Shop_Name', '')),
            clean_name=str(row.get('Shop_Name', '')).strip(), # AI cleanup happens later
            district=str(row.get('District', '')),
            excise_range=str(row.get('Range', '')),
            search_query=str(row.get('Search_Query', ''))
        )
        records_to_add.append(record)
        
        # Batch insert for performance
        if len(records_to_add) >= 500:
            session.bulk_save_objects(records_to_add)
            session.commit()
            records_to_add = []
            
    if records_to_add:
        session.bulk_save_objects(records_to_add)
        session.commit()
        
    print(f"Successfully loaded {session.query(ShopRecord).count()} shops into the database.")

async def process_batch(session, batch_size=10):
    """Process a batch of un-geocoded shops using Playwright."""
    shops_to_process = session.query(ShopRecord).filter_by(geocoded=False).limit(batch_size).all()
    
    if not shops_to_process:
        print("No un-geocoded shops found.")
        return
        
    print(f"Processing batch of {len(shops_to_process)} shops...")
    scraper = GoogleMapsScraper(headless=True)
    query_builder = QueryBuilder()
    
    for shop in shops_to_process:
        print(f"\nAnalyzing: {shop.original_name}")
        
        # 1. AI Name Cleanup (if not already done)
        if shop.clean_name == shop.original_name or not shop.clean_name:
            shop.clean_name = await query_builder.clean_shop_name(shop.original_name)
            
        # 2. AI Query Generation (if not already done)
        if not shop.search_query or len(shop.search_query) < 5 or "Toddy Shop" not in shop.search_query:
            shop.search_query = await query_builder.build_search_query(shop.clean_name, shop.district, shop.excise_range)
            
        print(f"  -> Generated Query: {shop.search_query}")
        
        # 3. Playwright Scraping
        result = await scraper.scrape_shop(shop.search_query)
        
        # Update record
        shop.google_maps_url = result.get('google_maps_url')
        shop.address = result.get('address')
        shop.rating = result.get('rating')
        shop.reviews_count = result.get('reviews_count')
        shop.phone_number = result.get('phone_number')
        shop.geocoded = True
        
        # Save to DB
        session.commit()
        print(f"  -> Saved {shop.clean_name}")
        
        # Respectful delay between requests
        await asyncio.sleep(2)

def main():
    print("--- Kerala Shop Intelligence Pipeline ---")
    session = init_db()
    
    # 1. Load Data
    load_initial_data(session)
    
    # 2. Scrape Batch
    asyncio.run(process_batch(session, batch_size=5))
    
    print("Batch processing complete.")

if __name__ == "__main__":
    main()
