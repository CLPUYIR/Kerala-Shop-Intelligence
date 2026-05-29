import sqlite3
import pandas as pd
import os
import sys
from pathlib import Path
from datetime import datetime

# Ensure project root is in PYTHONPATH
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from config import DB_PATH, DATA_DIR

def export_database():
    print(f"Exporting database from: {DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        print("Error: Database file not found. Have you run the pipeline yet?")
        return

    try:
        # Connect to SQLite database
        conn = sqlite3.connect(DB_PATH)
        
        # Read the 'shops' table into a pandas DataFrame
        query = "SELECT * FROM shops"
        df = pd.read_sql_query(query, conn)
        
        conn.close()
        
        if df.empty:
            print("Database is empty. Nothing to export.")
            return

        # Generate timestamped filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_file = DATA_DIR / f"kerala_shops_export_{timestamp}.csv"
        # We can also output excel if openpyxl is installed, but we'll stick to CSV for now to avoid extra dependencies, 
        # or we can just try excel and fallback to CSV.
        
        # Export to CSV
        df.to_csv(csv_file, index=False, encoding='utf-8')
        print(f"Successfully exported {len(df)} rows to CSV:")
        print(f" -> {csv_file}")
        
        try:
            excel_file = DATA_DIR / f"kerala_shops_export_{timestamp}.xlsx"
            df.to_excel(excel_file, index=False)
            print(f"Successfully exported {len(df)} rows to Excel:")
            print(f" -> {excel_file}")
        except ModuleNotFoundError:
            print("\nNote: To export to Excel format as well, install openpyxl: pip install openpyxl")
            
    except Exception as e:
        print(f"An error occurred during export: {e}")

if __name__ == "__main__":
    export_database()
