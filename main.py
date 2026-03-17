import os
import csv
import asyncio
import datetime as dt
import sqlite3
import schedule
import time
from playwright.async_api import async_playwright
from main_scraper import get_all_companies, scrape_worker, COMPANIES_DIR, GLOBAL_DIR
from SQL_engine import csv_to_sql_db

HEADLESS = False
CONCURRENT_WORKERS = 4

async def main():
    date = dt.datetime.now().strftime("%Y-%m-%d")
    os.makedirs(COMPANIES_DIR, exist_ok=True)
    os.makedirs(GLOBAL_DIR, exist_ok=True)

    headers = ["Company", "Séance", "Instrument", "Ticker", "Ouverture", "Dernier_Cours", 
                "+haut_du_jour", "+bas_du_jour", "Nombre_de_titres_échangés", 
                "Volume_des_échanges", "Nombre_de_transactions", "Capitalisation"]

    stats = {'success': [], 'failed': []}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS)
        setup_page = await browser.new_page()
        companies = await get_all_companies(setup_page)
        await setup_page.close()

        queue = asyncio.Queue()
        for c in companies: await queue.put(c)

        global_path = os.path.join(GLOBAL_DIR, f"global_update_{date}.csv")
        with open(global_path, "a", newline="", encoding="utf-8") as g_file:
            g_writer = csv.writer(g_file)
            if os.path.getsize(global_path) == 0:
                g_writer.writerow(headers)

            workers = [scrape_worker(browser, queue, g_writer, date, headers, stats) 
                        for _ in range(CONCURRENT_WORKERS)]
            await asyncio.gather(*workers)

        await browser.close()

    print(f"Scraping completed. Success: {len(stats['success'])}, Failed: {len(stats['failed'])}")
    csv_to_sql_db(COMPANIES_DIR)
    print("SQL database updated with new data.")

def start_daily_schedule():
    target_time = "19:00" 
    schedule.every().day.at(target_time).do(lambda: asyncio.run(main()))
    print(f"Scheduler started. Will run every day at {target_time}. Keep this terminal open.")
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
    start_daily_schedule()