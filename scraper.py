import asyncio
import csv
import os
import random
import datetime as dt
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import pandas as pd
import schedule
import time

# --- CONFIGURATION ---
CONCURRENT_WORKERS = 2
HEADLESS = True
MAX_RETRIES = 10
# ---------------------

# --- PATHS ---
COMPANIES_DIR = "data/companies"
GLOBAL_DIR = "data/global"
# -------------

# --- HEADERS ---
HEADERS = [
    "Company", "Séance", "Instrument", "Ticker",
    "Ouverture", "Dernier_Cours", "haut_du_jour", "bas_du_jour",
    "Nombre_de_titres_échangés", "Volume_des_échanges",
    "Nombre_de_transactions", "Capitalisation"
]
# ---------------


# ── StoredObject ──────────────────────────────────────────────────────────────

class StoredObject:
    """One row of scraped market data. Knows how to save itself to CSV."""

    def __init__(self, company, Séance, Instrument, Ticker,
                Ouverture, Dernier_Cours, haut_du_jour, bas_du_jour,
                Nombre_de_titres_échangés, Volume_des_échanges,
                Nombre_de_transactions, Capitalisation):
        self.company = company
        self.Séance = Séance
        self.Instrument = Instrument
        self.Ticker = Ticker
        self.Ouverture = Ouverture
        self.Dernier_Cours = Dernier_Cours
        self.haut_du_jour = haut_du_jour
        self.bas_du_jour = bas_du_jour
        self.Nombre_de_titres_échangés = Nombre_de_titres_échangés
        self.Volume_des_échanges = Volume_des_échanges
        self.Nombre_de_transactions = Nombre_de_transactions
        self.Capitalisation = Capitalisation

    @classmethod
    def from_row(cls, company: str, cells: list) -> "StoredObject":
        """Build a StoredObject from a scraped list of cell values."""
        return cls(company, *cells)

    def to_row(self) -> list:
        return [
            self.company, self.Séance, self.Instrument, self.Ticker,
            self.Ouverture, self.Dernier_Cours, self.haut_du_jour, self.bas_du_jour,
            self.Nombre_de_titres_échangés, self.Volume_des_échanges,
            self.Nombre_de_transactions, self.Capitalisation
        ]

    async def save_self(self, file_path: str):
        """Append this row to its company CSV, writing the header if new."""
        file_exists = os.path.exists(file_path)
        with open(file_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(HEADERS[1:])   # no "Company" in per-company files
            writer.writerow(self.to_row()[1:]) # strip company from row too


# ── DataStore ─────────────────────────────────────────────────────────────────

class DataStore:
    """Async-safe in-memory store. Accumulates StoredObjects across all workers."""

    def __init__(self):
        self._objects: list[StoredObject] = []
        self._lock = asyncio.Lock()

    async def append(self, obj: StoredObject):
        async with self._lock:
            self._objects.append(obj)

    def to_dataframe(self) -> pd.DataFrame:
        df = pd.DataFrame([obj.to_row() for obj in self._objects], columns=HEADERS)
        df["Séance"] = pd.to_datetime(df["Séance"], dayfirst=True, errors="coerce")
        numeric_cols = [
            "Ouverture", "Dernier_Cours", "haut_du_jour", "bas_du_jour",
            "Nombre_de_titres_échangés", "Volume_des_échanges",
            "Nombre_de_transactions", "Capitalisation"
        ]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        return df

    def get_company(self, name: str) -> pd.DataFrame:
        """Return a DataFrame filtered to a single company."""
        return self.to_dataframe().query("Company == @name")

    def __len__(self):
        return len(self._objects)


# ── Helpers ───────────────────────────────────────────────────────────────────

def format_value(val):
    if not val:
        return val
    cleaned = val.strip().replace(" ", "").replace(",", ".")
    try:
        if cleaned.isdigit():
            return int(cleaned)
        return float(cleaned)
    except ValueError:
        return val.strip()

def get_last_scraped_row(file_path: str) -> list | None:
    """Return the most recent data row from a company CSV (row after header)."""
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            rows = list(csv.reader(f))
            if len(rows) > 1:
                return rows[1]
    except Exception:
        pass
    return None

async def human_delay(min_ms: int = 300, max_ms: int = 900):
    await asyncio.sleep(random.uniform(min_ms, max_ms) / 1000)


# ── Browser context factory ───────────────────────────────────────────────────

async def new_stealth_context(browser):
    context = await browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1280, "height": 800},
        locale="fr-FR",
        timezone_id="Africa/Casablanca",
    )
    # block heavy assets to speed up loads
    await context.route(
        "**/*.{png,jpg,jpeg,gif,css,svg,woff,woff2}",
        lambda route: route.abort()
    )
    return context


# ── Company list ──────────────────────────────────────────────────────────────

async def get_all_companies(browser) -> list[str]:
    context = await new_stealth_context(browser)
    page = await context.new_page()
    await Stealth().apply_stealth_async(page)

    await page.goto(
        "https://www.casablanca-bourse.com/fr/instruments",
        wait_until="networkidle",
        timeout=60000
    )
    combo = page.locator('input[role="combobox"]')
    await combo.wait_for(state="visible", timeout=15000)
    await combo.click()
    await page.wait_for_selector('ul[role="listbox"]', state="visible", timeout=15000)

    options = await page.locator('ul[role="listbox"] li span').all_inner_texts()
    await context.close()
    return [n.strip() for n in options if n.strip() != "Tous les instruments"]


# ── Worker ────────────────────────────────────────────────────────────────────

async def scrape_worker(browser, company_queue, global_writer, store: DataStore, stats: dict):
    context = await new_stealth_context(browser)
    page = await context.new_page()
    await Stealth().apply_stealth_async(page)
    page.set_default_timeout(60000)

    while not company_queue.empty():
        company = await company_queue.get()
        success = False

        company_file_path = os.path.join(COMPANIES_DIR, f"{company.replace(' ', '_')}.csv")
        last_local_row = get_last_scraped_row(company_file_path)

        for attempt in range(MAX_RETRIES):
            try:
                await page.goto(
                    "https://www.casablanca-bourse.com/fr/instruments",
                    wait_until="networkidle",
                    timeout=60000
                )

                await page.fill("input[placeholder='Séance']", '')
                await page.fill("input[placeholder='Date fin']", '')

                # --- autocomplete: fill() to handle company names with spaces ---
                combo = page.locator('input[role="combobox"]')
                await combo.wait_for(state="visible", timeout=15000)
                await combo.click()
                await human_delay(400, 700)
                await page.keyboard.press("Control+A")
                await page.keyboard.press("Backspace")

                await combo.fill(company)               # atomic — no keystroke-by-keystroke
                await combo.dispatch_event("input")     # trigger dropdown manually
                # -----------------------------------------------------------------

                target_item = page.locator('ul[role="listbox"] li').filter(has_text=company).first
                await target_item.wait_for(state="visible", timeout=10000)
                await target_item.click()

                await human_delay()
                await page.click('button:has-text("Appliquer")')

                rows_locator = page.locator("table tbody.whitespace-nowrap tr")
                await rows_locator.first.wait_for(state="attached", timeout=10000)

                # check if already up to date
                first_web_row_raw = await rows_locator.first.locator("td").all_inner_texts()
                first_web_row = [str(format_value(c)) for c in first_web_row_raw]

                if last_local_row and first_web_row == last_local_row:
                    print(f"[Worker] {company} already up to date. Skipping.")
                    success = True
                    break

                # collect new rows
                new_objects: list[StoredObject] = []
                current_page = 1

                while True:
                    rows = await rows_locator.all()
                    stop_pagination = False

                    for row in rows:
                        cells_raw = await row.locator("td").all_inner_texts()
                        processed = [format_value(c) for c in cells_raw]

                        if last_local_row and [str(i) for i in processed] == last_local_row:
                            stop_pagination = True
                            break

                        obj = StoredObject.from_row(company, processed)
                        new_objects.append(obj)

                    if stop_pagination:
                        break

                    next_btn = page.get_by_role("button", name=str(current_page + 1), exact=True)
                    if await next_btn.is_visible():
                        await next_btn.click()
                        await page.wait_for_load_state("networkidle", timeout=10000)
                        current_page += 1
                    else:
                        break

                # read existing rows from disk
                old_rows = []
                if os.path.exists(company_file_path):
                    with open(company_file_path, "r", newline="", encoding="utf-8") as f:
                        reader = csv.reader(f)
                        all_rows = list(reader)
                        # skip header row
                        old_rows = all_rows[1:] if len(all_rows) > 1 else []

                # rewrite company CSV: header + new rows first + old rows
                with open(company_file_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(HEADERS[1:])
                    for obj in new_objects:
                        writer.writerow(obj.to_row()[1:])
                    writer.writerows(old_rows)

                # write to global CSV and store
                for obj in new_objects:
                    global_writer.writerow(obj.to_row())
                    await store.append(obj)

                print(f"[Worker] {company} — {len(new_objects)} new rows added.")
                success = True
                stats['success'].append(company)
                break

            except Exception as e:
                print(f"[Error] {company} attempt {attempt + 1}: {str(e)[:80]}")
                await asyncio.sleep(2)

        if not success:
            stats['failed'].append(company)

        company_queue.task_done()

    await context.close()


# ── Main ──────────────────────────────────────────────────────────────────────

async def main() -> tuple[pd.DataFrame, dict]:
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

            # stagger worker starts to avoid simultaneous bursts
            workers = []
            for i in range(CONCURRENT_WORKERS):
                await asyncio.sleep(i * 2)
                workers.append(scrape_worker(browser, queue, g_writer, store, stats))

            await asyncio.gather(*workers)

        await browser.close()

    df = store.to_dataframe()
    print(f"\nDone. {len(df)} rows collected across {df['Company'].nunique()} companies.")
    print(f"Success: {len(stats['success'])} | Failed: {len(stats['failed'])}")
    if stats['failed']:
        print(f"Failed companies: {stats['failed']}")

    return df, stats


# ── Scheduler ─────────────────────────────────────────────────────────────────

async def run_task():
    print(f"\n[{dt.datetime.now()}] Starting scheduled scrape...")
    df, stats = await main()
    print(f"[{dt.datetime.now()}] Scrape complete.")
    return df, stats

def start_daily_schedule(target_time: str = "19:00"):
    schedule.every().day.at(target_time).do(lambda: asyncio.run(run_task()))
    print(f"Scheduler running. Next scrape at {target_time} daily.")
    print("Keep this terminal open.")
    while True:
        schedule.run_pending()
        time.sleep(60)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    df, stats = asyncio.run(main())
    start_daily_schedule()
