import asyncio
from playwright.async_api import async_playwright
import urllib.parse

class GoogleMapsScraper:
    def __init__(self, headless=True):
        self.headless = headless

    async def scrape_shop(self, query):
        print(f"Scraping Google Maps for: {query}")
        result_data = {
            "google_maps_url": None,
            "address": None,
            "rating": None,
            "reviews_count": None,
            "phone_number": None
        }
        
        async with async_playwright() as p:
            # Use Chromium with stealth-like settings
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = await context.new_page()
            
            # Construct Google Maps search URL
            encoded_query = urllib.parse.quote(query)
            search_url = f"https://www.google.com/maps/search/{encoded_query}"
            
            try:
                await page.goto(search_url, wait_until="domcontentloaded", timeout=15000)
                
                # Wait a bit for dynamic content or redirects to settle
                await page.wait_for_timeout(3000)
                
                # Check if we landed on a specific place page or a search results list
                current_url = page.url
                if "/place/" not in current_url:
                    # We are on a list of results, click the first one
                    try:
                        # Google Maps uses 'a.hfpxzc' for place links in the side panel
                        first_result = await page.wait_for_selector('a.hfpxzc', timeout=5000)
                        if first_result:
                            await first_result.click()
                            await page.wait_for_timeout(3000)
                            current_url = page.url
                    except Exception as e:
                        print(f"  -> No specific results found or failed to click first result.")

                if "/place/" in current_url:
                    # We are on the exact place page
                    result_data["google_maps_url"] = current_url
                    
                    # Extract Address (Usually the first button with an aria-label starting with "Address: ")
                    try:
                        address_element = await page.query_selector('button[data-item-id="address"]')
                        if address_element:
                            aria_label = await address_element.get_attribute("aria-label")
                            if aria_label:
                                result_data["address"] = aria_label.replace("Address: ", "").strip()
                    except Exception as e:
                        pass
                        
                    # Extract Rating and Reviews
                    try:
                        rating_element = await page.query_selector('div.F7nice')
                        if rating_element:
                            text_content = await rating_element.inner_text()
                            parts = text_content.split('\n')
                            if len(parts) >= 2:
                                result_data["rating"] = float(parts[0].strip())
                                result_data["reviews_count"] = int(parts[1].replace('(', '').replace(')', '').replace(',', '').strip())
                    except Exception as e:
                        pass
                        
            except Exception as e:
                print(f"  -> Error scraping {query}: {e}")
            finally:
                await browser.close()
                
        return result_data

async def test_scraper():
    scraper = GoogleMapsScraper(headless=True)
    res = await scraper.scrape_shop("Pazhauchakada Toddy Shop, Thirupuram, Thiruvananthapuram")
    print(res)

if __name__ == "__main__":
    asyncio.run(test_scraper())
