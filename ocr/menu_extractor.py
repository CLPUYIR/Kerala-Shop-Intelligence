import os
import sys
import httpx
import pytesseract
from PIL import Image
from io import BytesIO
from pathlib import Path

# Ensure project root is in PYTHONPATH
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from ai.query_builder import QueryBuilder

# Configure Tesseract path for Windows if it's installed in the default location
TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
if os.path.exists(TESSERACT_CMD):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

class MenuExtractor:
    def __init__(self):
        self.ai = QueryBuilder() # Reuse our local LLM wrapper

    async def download_image(self, url: str) -> Image.Image:
        """Downloads an image from a URL and returns a PIL Image."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=15.0)
                response.raise_for_status()
                return Image.open(BytesIO(response.content))
        except Exception as e:
            print(f"Failed to download image from {url}: {e}")
            return None

    def extract_text_from_image(self, image: Image.Image) -> str:
        """Runs Tesseract OCR on the image to extract raw text (Malayalam & English)."""
        if not image:
            return ""
            
        try:
            # We try to use Malayalam ('mal') and English ('eng') language models if installed.
            # Fallback to just English if 'mal' is not available.
            try:
                text = pytesseract.image_to_string(image, lang='mal+eng')
            except pytesseract.TesseractError:
                text = pytesseract.image_to_string(image)
            return text.strip()
        except (FileNotFoundError, pytesseract.TesseractNotFoundError):
            print("\n[WARNING] Tesseract OCR is not installed or not in PATH.")
            print("Please install Tesseract OCR for Windows to enable menu extraction:")
            print("Download: https://github.com/UB-Mannheim/tesseract/wiki")
            print(f"Install it to the default path: {TESSERACT_CMD}\n")
            return ""
        except Exception as e:
            print(f"OCR Error: {e}")
            return ""

    async def parse_menu_with_ai(self, raw_text: str) -> dict:
        """Uses local LLM to extract signature dishes and vibe from raw OCR text."""
        if not raw_text or len(raw_text) < 10:
            return {"signature_dishes": None, "vibe_summary": None}
            
        prompt = f"""
        You are an AI extracting data from a Kerala Toddy Shop menu.
        Here is the raw, messy OCR text extracted from an image of their menu/signboard.
        
        Raw Text:
        "{raw_text}"
        
        Task 1: Identify "Signature Dishes" (e.g., Karimeen, Pork, Duck, Beef, Kappa, Fish Curry). Return them as a comma-separated list.
        Task 2: Summarize the "Vibe" or shop characteristics based on the text (e.g., "Riverside", "Family AC", "Authentic"). Return a short sentence.
        
        Output strictly in this JSON format, nothing else:
        {{"signature_dishes": "dish1, dish2", "vibe_summary": "vibe details"}}
        """
        
        json_str = await self.ai._call_ollama(prompt)
        
        # Simple cleanup if the LLM added markdown formatting
        json_str = json_str.replace("```json", "").replace("```", "").strip()
        
        try:
            import json
            data = json.loads(json_str)
            return {
                "signature_dishes": data.get("signature_dishes"),
                "vibe_summary": data.get("vibe_summary")
            }
        except Exception as e:
            print(f"Failed to parse LLM JSON: {e}")
            return {"signature_dishes": None, "vibe_summary": None}

    async def process_menu_image(self, image_url_or_path: str):
        """End-to-end pipeline: Download -> OCR -> AI Parse"""
        print(f"Processing menu image: {image_url_or_path}")
        
        if image_url_or_path.startswith("http"):
            image = await self.download_image(image_url_or_path)
        else:
            try:
                image = Image.open(image_url_or_path)
            except Exception as e:
                print(f"Failed to open local image: {e}")
                image = None
                
        raw_text = self.extract_text_from_image(image)
        
        if raw_text:
            print(f"OCR Extracted {len(raw_text)} characters.")
            data = await self.parse_menu_with_ai(raw_text)
            return data
        else:
            return {"signature_dishes": None, "vibe_summary": None}

async def test():
    extractor = MenuExtractor()
    # Mocking OCR with direct raw text for testing the AI part
    raw_text = "TODDY SHOP NO 12 MENU: Karimeen Pollichathu 250, Beef Fry 120, Kappa 50. Family AC Hall Available."
    print("Testing AI Parser with mock OCR text...")
    result = await extractor.parse_menu_with_ai(raw_text)
    print(f"AI Extraction Result: {result}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test())
