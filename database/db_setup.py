from sqlalchemy import Column, Integer, String, Float, Text, Boolean, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from config import DB_URI

Base = declarative_base()

class ShopRecord(Base):
    __tablename__ = 'shops'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    shop_no = Column(String(50))
    original_name = Column(String(255))
    clean_name = Column(String(255))
    district = Column(String(100))
    excise_range = Column(String(100))
    
    # Enrichment Data
    search_query = Column(String(500))
    google_maps_url = Column(String(500))
    address = Column(Text)
    latitude = Column(Float)
    longitude = Column(Float)
    rating = Column(Float)
    reviews_count = Column(Integer)
    timings = Column(Text)
    phone_number = Column(String(50))
    website = Column(String(500))
    
    # Vibe & Menu
    signature_dishes = Column(Text)
    vibe_summary = Column(Text)
    
    # Process Status
    geocoded = Column(Boolean, default=False)
    menu_extracted = Column(Boolean, default=False)
    verified = Column(Boolean, default=False)

def init_db():
    engine = create_engine(DB_URI)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
