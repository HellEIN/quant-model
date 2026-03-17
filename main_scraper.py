import asyncio
import csv
import os
import datetime as dt
from playwright.async_api import async_playwright
import schedule
import time

# --- CONFIGURATION ---
CONCURRENT_WORKERS = 4 
HEADLESS = True         
MAX_RETRIES = 10       
# ---------------------

# --- PATHS ---
COMPANIES_DIR = "data/companies"
GLOBAL_DIR = "data/global"
# -------------

def format_value(val):
    if not val: return val
    cleaned = val.strip().replace(" ", "").replace(",", ".")
    try:
        if cleaned.isdigit(): return int(cleaned)
        return float(cleaned)
    except ValueError: return val.strip()

def get_last_scraped_row(file_path):
    """Reads the local CSV and returns the first data row (most recent)."""
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            reader = list(csv.reader(f))
            if len(reader) > 1: # Index 0 is header, Index 1 is most recent data
                return reader[1] 
    except Exception:
        return None
    return None

async def get_all_companies(page):
    await page.goto("https://www.casablanca-bourse.com/fr/instruments", wait_until="networkidle", timeout=10000)
    await page.click('input[role="combobox"]')
    await page.wait_for_selector('ul[role="listbox"]', state="visible")
    options = await page.locator('ul[role="listbox"] li span').all_inner_texts()
    return [name.strip() for name in options if name.strip() != "Tous les instruments"]

async def scrape_worker(browser, company_queue, global_writer, date, headers, stats):
    context = await browser.new_context()
    await context.route("**/*.{png,jpg,jpeg,gif,css,svg,woff,woff2}", lambda route: route.abort())
    page = await context.new_page()
    page.set_default_timeout(60000)

    while not company_queue.empty():
        company = await company_queue.get()
        success = False

        # Define file path to check for existing data
        company_file_path = os.path.join(COMPANIES_DIR, f"{company.replace(' ', '_')}.csv")
        last_local_row = get_last_scraped_row(company_file_path)

        for attempt in range(MAX_RETRIES):
            try:
                await page.goto("https://www.casablanca-bourse.com/fr/instruments", wait_until="domcontentloaded")
                await page.fill("input[placeholder='Séance']", '')
                await page.fill("input[placeholder='Date fin']", '')

                # Autocomplete Logic
                combo_input = page.locator('input[role="combobox"]')
                await combo_input.click()
                await page.wait_for_timeout(400)
                await page.keyboard.press("Control+A")
                await page.wait_for_timeout(400)
                await page.keyboard.press("Backspace")
                await combo_input.type(company, delay=100)

                target_item = page.locator('ul[role="listbox"] li').filter(has_text=company).first
                await target_item.wait_for(state="visible", timeout=10000)
                await target_item.click()
                await page.click('button:has-text("Appliquer")')
                
                # Check if we actually need to scrape
                rows_locator = page.locator("table tbody.whitespace-nowrap tr")
                await rows_locator.first.wait_for(state="attached", timeout=10000)
                
                # Compare latest web row with latest local row
                first_web_row_raw = await rows_locator.first.locator("td").all_inner_texts()
                first_web_row = [str(format_value(c)) for c in first_web_row_raw]

                if last_local_row and first_web_row == last_local_row:
                    print(f"[Worker] {company} is already up to date. Skipping...")
                    success = True
                    break

                # If different, append new data
                file_exists = os.path.exists(company_file_path)
                with open(company_file_path, "a", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    if not file_exists:
                        writer.writerow(headers[1:])

                    current_page = 1
                    new_rows_count = 0
                    while True:
                        rows = await rows_locator.all()
                        stop_pagination = False
                        
                        for row in rows:
                            cells_raw = await row.locator("td").all_inner_texts()
                            processed = [format_value(c) for c in cells_raw]
                            
                            # If we hit the row we already have, stop scraping for this company
                            if last_local_row and [str(i) for i in processed] == last_local_row:
                                stop_pagination = True
                                break
                            
                            writer.writerow(processed)
                            global_writer.writerow([company] + processed)
                            new_rows_count += 1

                        if stop_pagination: break

                        next_btn = page.get_by_role("button", name=str(current_page + 1), exact=True)
                        if await next_btn.is_visible():
                            await next_btn.click()
                            await page.wait_for_load_state("networkidle", timeout=10000)
                            current_page += 1
                        else: break
                
                print(f"[Worker] {company} updated with {new_rows_count} new entries.")
                success = True
                stats['success'].append(company)
                break

            except Exception as e:
                print(f"   [Error] {company} attempt {attempt+1}: {str(e)[:50]}")
                await asyncio.sleep(2)

        if not success: stats['failed'].append(company)
        company_queue.task_done()
    
    await context.close()

