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
            "phone_number": None,
            "website": None
        }
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = await context.new_page()
            
            encoded_query = urllib.parse.quote(query)
            search_url = f"https://www.google.com/maps/search/{encoded_query}"
            
            try:
                await page.goto(search_url, wait_until="domcontentloaded", timeout=15000)
                await page.wait_for_timeout(3000) # Let the network settle

                # If we are on a search results page (not a specific place), click the first result
                if "/place/" not in page.url and "/maps/dir/" not in page.url:
                    try:
                        first_result = await page.wait_for_selector('a.hfpxzc', timeout=5000)
                        if first_result:
                            await first_result.click()
                            # Wait for the place details panel title to appear
                            await page.wait_for_selector('h1.DUwDvf', timeout=5000)
                            await page.wait_for_timeout(1000)
                    except Exception:
                        pass # Might already be on a place page with a weird URL, or no results

                # Now attempt extraction if the place details panel is visible
                try:
                    # Verify the details panel is open by looking for the main title
                    title_element = await page.query_selector('h1.DUwDvf')
                    if title_element:
                        result_data["google_maps_url"] = page.url
                        
                        # Extract Address
                        addr_btn = await page.query_selector('button[data-item-id="address"]')
                        if addr_btn:
                            aria = await addr_btn.get_attribute("aria-label")
                            if aria:
                                result_data["address"] = aria.replace("Address: ", "").strip()
                                
                        # Extract Phone Number
                        phone_btn = await page.query_selector('button[data-item-id^="phone:tel:"]')
                        if phone_btn:
                            aria = await phone_btn.get_attribute("aria-label")
                            if aria:
                                result_data["phone_number"] = aria.replace("Phone: ", "").strip()
                                
                        # Extract Website
                        web_btn = await page.query_selector('a[data-item-id="authority"]')
                        if web_btn:
                            href = await web_btn.get_attribute("href")
                            if href:
                                result_data["website"] = href.strip()

                        # Extract Rating and Reviews
                        rating_div = await page.query_selector('div.F7nice')
                        if rating_div:
                            text = await rating_div.inner_text()
                            parts = text.split('\n')
                            if len(parts) >= 2:
                                try:
                                    result_data["rating"] = float(parts[0].strip())
                                    result_data["reviews_count"] = int(parts[1].replace('(', '').replace(')', '').replace(',', '').strip())
                                except ValueError:
                                    pass
                except Exception as e:
                    print(f"  -> Error extracting details: {e}")

            except Exception as e:
                print(f"  -> Error loading page {query}: {e}")
            finally:
                await browser.close()
                
        return result_data

async def test_scraper():
    scraper = GoogleMapsScraper(headless=True)
    res = await scraper.scrape_shop("Pazhauchakada Toddy Shop, Thirupuram, Thiruvananthapuram")
    print(res)

if __name__ == "__main__":
    asyncio.run(test_scraper())
