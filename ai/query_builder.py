import json
import httpx
import re
import sys
from pathlib import Path

# Ensure project root is in PYTHONPATH
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from config import OLLAMA_BASE_URL

# Best local model available on your machine
DEFAULT_MODEL = "llama3.1:8b"

class QueryBuilder:
    def __init__(self, model=DEFAULT_MODEL):
        self.model = model
        self.base_url = OLLAMA_BASE_URL

    async def _call_ollama(self, prompt: str) -> str:
        """Helper to call local Ollama instance asynchronously."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,  # Keep it deterministic
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.base_url, json=payload, timeout=30.0)
                response.raise_for_status()
                data = response.json()
                return data.get("response", "").strip()
        except Exception as e:
            print(f"Ollama Error: {e}")
            return ""

    async def clean_shop_name(self, raw_name: str) -> str:
        """Uses LLM to remove junk characters, numbers, and standardize the shop name."""
        prompt = f"""
        You are a data cleaning assistant specializing in Kerala business names.
        Extract only the core, meaningful name of the Toddy Shop from the given raw text.
        Remove all leading numbers, "Sl. No", "Name of Shop", "Annual", or Roman numerals (I, II, III).
        If the name is just a place name, keep it. Add "Toddy Shop" at the end if it's missing.
        
        Raw Text: "{raw_name}"
        
        Output ONLY the cleaned shop name, nothing else. No explanations.
        """
        cleaned = await self._call_ollama(prompt)
        
        # Fallback to regex cleaning if LLM fails or returns garbage
        if not cleaned or len(cleaned) > 100 or "{" in cleaned:
            cleaned = re.sub(r'^[0-9\.\s]+', '', raw_name)
            cleaned = re.sub(r'\b(Sl\.?|Name|Annual)\b', '', cleaned, flags=re.IGNORECASE).strip()
            
        if "Toddy Shop" not in cleaned and len(cleaned) > 2:
            cleaned = f"{cleaned} Toddy Shop"
            
        return cleaned

    async def build_search_query(self, clean_name: str, district: str, range_name: str) -> str:
        """Constructs an optimal Google Maps search query."""
        
        # Sometimes Range and District are the same or redundant
        # We want the most specific geographical string without being confusing
        prompt = f"""
        You are an expert at creating highly precise Google Maps search queries for businesses in Kerala, India.
        Given the Shop Name, the Excise Range (local area), and the District, construct the single best search string.
        
        Shop Name: {clean_name}
        Local Area (Range): {range_name}
        District: {district}
        
        Rules:
        - If the Shop Name already contains the Local Area, don't repeat the Local Area.
        - Ensure "Kerala" and "India" are at the end.
        - Format: [Precise Shop Name], [Local Area (if needed)], [District], Kerala, India.
        
        Output ONLY the final search string, nothing else.
        """
        
        query = await self._call_ollama(prompt)
        
        # Fallback logic
        if not query or len(query) > 150:
            query = f"{clean_name}, {range_name}, {district}, Kerala, India"
            # Clean up double commas if range was empty
            query = query.replace(" ,", ",").replace(",,", ",")
            
        return query.strip()

# Quick test
async def test():
    qb = QueryBuilder()
    print("Testing clean name...")
    clean = await qb.clean_shop_name("12 III Amaravila Toddy Shop")
    print(f"Cleaned: {clean}")
    
    print("\nTesting build query...")
    query = await qb.build_search_query(clean, "Thiruvananthapuram", "Amaravila")
    print(f"Query: {query}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test())
