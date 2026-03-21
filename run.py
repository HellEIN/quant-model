import os
import csv
import asyncio
import datetime as dt
import schedule
import time
from playwright.async_api import async_playwright
from scraper import (
    get_all_companies, scrape_worker,
    COMPANIES_DIR, GLOBAL_DIR, HEADERS,
    HEADLESS, CONCURRENT_WORKERS,
    DataStore
)
from SQL_engine import csv_to_sql_db


async def main():
    date = dt.datetime.now().strftime("%Y-%m-%d")
    os.makedirs(COMPANIES_DIR, exist_ok=True)
    os.makedirs(GLOBAL_DIR, exist_ok=True)

    store = DataStore()
    stats = {'success': [], 'failed': []}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS)

        print("Fetching company list...")
        companies = await get_all_companies(browser)
        print(f"Found {len(companies)} companies.")

        queue = asyncio.Queue()
        for c in companies:
            await queue.put(c)

        global_path = os.path.join(GLOBAL_DIR, f"global_update_{date}.csv")
        with open(global_path, "a", newline="", encoding="utf-8") as g_file:
            g_writer = csv.writer(g_file)
            if os.path.getsize(global_path) == 0:
                g_writer.writerow(HEADERS)

            workers = []
            for i in range(CONCURRENT_WORKERS):
                await asyncio.sleep(i * 2)
                workers.append(
                    scrape_worker(browser, queue, g_writer, store, stats)
                )
            await asyncio.gather(*workers)

        await browser.close()

    df = store.to_dataframe()
    print(f"\nScraping complete. {len(df)} rows across {df['Company'].nunique()} companies.")
    print(f"Success: {len(stats['success'])} | Failed: {len(stats['failed'])}")
    if stats['failed']:
        print(f"Failed: {stats['failed']}")

    csv_to_sql_db(COMPANIES_DIR)
    print("SQL database updated.")

    return df, stats


def start_daily_schedule(target_time: str = "18:10"):
    schedule.every().day.at(target_time).do(lambda: asyncio.run(main()))
    print(f"Scheduler started. Will run every day at {target_time}. Keep this terminal open.")
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
    start_daily_schedule()
