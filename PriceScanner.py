import json
import platform
import traceback

from devtools.logger import set_log_level, log
from selenium import webdriver
from selenium.common import WebDriverException
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import random
from bs4 import BeautifulSoup

from ProxyScraper import get_working_proxies

def load_proxies():
    with open("proxies.json", "r") as file:
        proxies = json.loads(file.read())
        proxies = proxies["Proxies"]
        cleaned_proxies = []
        for prox in proxies:
            cleaned_proxies.append(prox.replace("\n", ""))
        proxies = cleaned_proxies
    if len(proxies) == 0:
        get_working_proxies()
        proxies = load_proxies()
    return proxies


def load_driver(proxy=None):
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--window-position=-10000,0")  # Open off the screen
    chrome_options.add_argument("--headless")  # Prevent stealing focus


    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ]
    chrome_options.add_argument(f"user-agent={random.choice(user_agents)}")
    chrome_options.add_argument("user-data-dir=C:\\Users\\Jeremy\\AppData\\Local\\Google\\Chrome\\User Data")
    chrome_options.add_argument("profile-directory=Default")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    if proxy:
        log(f"Using proxy: {proxy}")
        chrome_options.add_argument(f'--proxy-server={proxy}')

    if platform.system() == "Windows":
        service = Service(ChromeDriverManager().install())
    else:
        service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Set custom headers
    driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {
        'headers': {
            'User-Agent': random.choice(user_agents),
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        }
    })
    # Set timeouts
    driver.set_page_load_timeout(30)  # Set page load timeout to 30 seconds
    driver.set_script_timeout(30)     # Set script timeout to 30 seconds

    return driver


def close_driver(driver):
    driver.quit()

def bad_proxy(proxies):
    proxies.pop(0)

    with open("proxies.json", "w") as f:
        f.write(json.dumps({"Proxies": proxies}, indent=4))

    if len(proxies) == 0:
        log("No more proxies available. Fetching new proxies...")
        get_working_proxies()
        proxies = load_proxies()
        log("finished fetching new proxies")
    return proxies


def scrape_coles(page_source):


    time.sleep(random.uniform(2, 5))

    soup = BeautifulSoup(page_source, 'html.parser')
    products = []

    for presentation_div in soup.find_all('div', role='presentation'):
        full_title = presentation_div.find("a", class_="product__link product__image")
        title_tag = presentation_div.find('h2', class_='product__title')
        price_tag = presentation_div.find('span', {'data-testid': 'product-pricing'})

        full_product_title = None
        product_url = None
        if title_tag and price_tag:
            product_title = title_tag.get_text(strip=True)
            try:
                full_product_title = full_title.get('aria-label', '').strip()
                product_url = full_title.get('href', '').strip()
            except Exception as e:
                log(f"Error: {e} While title tag is {title_tag}")

            if full_product_title:
                product_title = full_product_title
            product_price = price_tag.get_text(strip=True) if price_tag else None
            products.append((product_title, product_url, product_price))

    for presentation_div in soup.find_all('section', {'data-testid': 'product-tile'}):
        title_tag = presentation_div.find('h2', class_='product__title')
        price_tag = presentation_div.find('span', {'data-testid': 'product-pricing'})
        full_title = presentation_div.find("a", class_="product__link product__image")
        full_product_title = None
        product_url = None
        if title_tag and price_tag:
            product_title = title_tag.get_text(strip=True)
            try:
                full_product_title = full_title.get('aria-label', '').strip()
                product_url = full_title.get('href', '').strip()
            except Exception as e:
                log(e)

        if title_tag:
            product_title = title_tag.get_text(strip=True)
            product_price = price_tag.get_text(strip=True) if price_tag else None
            if full_product_title:
                product_title = full_product_title
            products.append((product_title, product_url, product_price))

    return products, True

def check_source_errors(page_source, proxies):
    success = True
    skip_page = False
    bot = "As you were browsing something about your browser made us think you were a bot" in page_source
    if bot:
        success = False
        log(f"Detected as bot. Trying again with proxy {proxies[0]}")
        log(f"Success is {success}")

    if r'ERR_TIMED_OUT' in page_source or "ERR_CONNECTION_RESET" in page_source:
        log("Timed out")
        success = False

    if "Sorry, we ran into an issue" in page_source and "We're working as fast as we can to fix the problem. Please come back later." in page_source:
        success = False
        skip_page = True

    if r'"hostName":"www.coles.com.au","msg":"This site can’t be reached"' in page_source:
        log("Site can't be reached")
        success = False

    return success, skip_page


def human_like_scroll(driver):
    # Get the maximum scroll height
    max_scroll_height = driver.execute_script("return document.body.scrollHeight")

    # Calculate a random scroll position within the bounds
    scroll_position = random.randint(0, max_scroll_height)

    # Scroll to the calculated position
    driver.execute_script(f"window.scrollTo(0, {scroll_position});")
    time.sleep(random.uniform(1, 3))


from selenium.common.exceptions import MoveTargetOutOfBoundsException

def human_like_mouse_movements(driver):
    # Move the mouse to a random position within the viewport
    action = ActionChains(driver)

    for _ in range(2):
        x_offset = random.randint(-0, 900)
        y_offset = random.randint(0, 500)
        try:
            action.move_by_offset(x_offset, y_offset).perform()
        except MoveTargetOutOfBoundsException as e:
            pass
        time.sleep(random.uniform(0.2, 0.5))

def get_source(driver, url):
    # Ensure the URL uses http instead of https
    url = url.replace("https://", "http://")

    try:
        driver.delete_all_cookies()
        driver.get(url)
        human_like_scroll(driver)
        human_like_mouse_movements(driver)
    except Exception as e:
        if "net::ERR_PROXY_CONNECTION_FAILED" in str(e):
            log("Proxy connection failed")
            return "", False
        elif "HTTPConnectionPool" in str(e) or r"Message: timeout: Timed out receiving message from renderer" in str(e) or "Read timed out." in str(e):
            log("Read timed out")
            return "", False
        elif "net::ERR_CONNECTION_CLOSED" in str(e):
            log("Connection closed")
            return "", False
        else:
            traceback.print_exc()
            log(e)
        return "", False

    time.sleep(random.uniform(2, 5))

    page_source = driver.page_source
    with open("page_source.html", "wb") as f:
        f.write(page_source.encode('utf-8', 'ignore'))
        log("Writing page source to page_source.html")

    # Check for <meta name="ROBOTS" content="NOINDEX, NOFOLLOW">
    if '<meta name="ROBOTS" content="NOINDEX, NOFOLLOW">' in page_source:
        log("Page contains <meta name=\"ROBOTS\" content=\"NOINDEX, NOFOLLOW\">")
        return page_source, False
    if "ERR_PROXY_CONNECTION_FAILED" in page_source:
        log("Proxy connection failed")
        return page_source, False
    return page_source, True


def scrape_coles_page_numbers(page_source):


    soup = BeautifulSoup(page_source, 'html.parser')
    page_info = soup.find('span', {'role': 'status', 'class': 'sr-only'})
    log(f"Page info is {page_info}")
    if page_info:
        page_text = page_info.get_text(strip=True)
        if "Page" in page_text and "of" in page_text:
            parts = page_text.split()
            current_page = int(parts[1])
            total_pages = int(parts[3])
            return total_pages, True

    return -1, False  # Return 0 if the page information could not be found


def scrape_with_proxies(driver, url, proxies, page_number, max_page_number):
    products = []

    log(f"Scraping {url}")

    while True:
        if max_page_number == -1:
            attempts = 6
        else:
            attempts = 2
        success = False
        skip_page = False

        page_source = ""
        try:
            page_source, success = get_source(driver, url)
            if success:
                success, skip_page = check_source_errors(page_source, proxies)

            if not success and skip_page:
                return [], driver, proxies, max_page_number
        except Exception as e:
            log(f"Error occurred while getting source {e}")
        try:
            if success:
                if max_page_number == -1:
                    max_page_number, success = scrape_coles_page_numbers(page_source)
                    if max_page_number == -1:
                        attempts -= 1
                        success = False
                    if attempts == 0:
                        log("Max page number could not be found within  attempts. Skipping page")
                        break
                    log(f"Max page number is {max_page_number}")
        except Exception as e:
            log(f"Error occurred while scraping page numbers {e}")

        try:
            if success:
                products, success = scrape_coles(page_source)
                if len(products) == 0 and page_number < max_page_number:
                    log(f"Page {page_number} is empty")
                    with open(f"empty_page_{page_number}.html", "wb") as f:
                        f.write(page_source.encode('utf-8', 'ignore'))
                    attempts -= 1
                    success = False
                    if attempts == 0:
                        log("Page could not be scraped within 2 attempts. Skipping page")
                        break
        except Exception as e:
            log(f"Error occurred while scraping products {e}")
            success = False
            traceback.print_exc()

        if success:
            break

        if not skip_page:
            proxies = bad_proxy(proxies)
        close_driver(driver)
        new_proxy = proxies[0]
        log(f"Trying with proxy: {new_proxy}")
        driver = load_driver(proxy=new_proxy)


    return products, driver, proxies, max_page_number


import sqlite3
from datetime import datetime


def init_db():
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            price TEXT,
            current_date TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS unique_product_date
        BEFORE INSERT ON products
        FOR EACH ROW
        BEGIN
            DELETE FROM products WHERE title = NEW.title AND current_date = NEW.current_date;
        END;
    ''')
    conn.commit()
    conn.close()




def insert_product(title, url, price):
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    current_date = datetime.now().strftime('%Y-%m-%d')
    try:
        cursor.execute('''
            INSERT INTO products (title, url, price, current_date)
            VALUES (?, ?, ?, ?)
        ''', (title, url, price, current_date))
        conn.commit()

    except sqlite3.IntegrityError:
        log(f"Failed constraints with values {title}, {url}, {price}, {current_date}")
    conn.close()


def main():
    set_log_level('DEBUG', False, False, True)
    # Initialize the database
    init_db()
    proxies = load_proxies()
    # Existing code to scrape products

    driver = load_driver(proxy=proxies[0])
    root_urls = [
        ("https://www.coles.com.au/browse/meat-seafood?page=", -1),
        ("https://www.coles.com.au/browse/fruit-vegetables?page=", -1),
        ("https://www.coles.com.au/browse/dairy-eggs-fridge?page=", -1),
        ("https://www.coles.com.au/browse/bakery?page=", -1),
        ("https://www.coles.com.au/browse/deli?page=", -1),
        ("https://www.coles.com.au/browse/pantry?page=", -1),
        ("https://www.coles.com.au/browse/drinks?page=", -1),
        ("https://www.coles.com.au/browse/frozen?page=", -1),
        ("https://www.coles.com.au/browse/household?page=", -1),
        ("https://www.coles.com.au/browse/health-beauty?page=", -1),
        ("https://www.coles.com.au/browse/baby?page=", -1),
        ("https://www.coles.com.au/browse/pet?page=", -1),
        ("https://www.coles.com.au/browse/liquor?page=", -1),

    ]

    for root_url_index in range(0, len(root_urls)):
        max_page = root_urls[root_url_index][1]
        root_url = root_urls[root_url_index][0]
        log(f"Searching {root_url}")
        page = 1
        while True:
            log(f"Searching page {page}")

            products, driver, proxies, max_page = scrape_with_proxies(driver, f"{root_url}{page}", proxies, page, max_page)
            log(products)
            root_urls[root_url_index] = (root_urls[root_url_index], max_page)
            for title, url, price in products:
                insert_product(title, url, price)
            page += 1
            if page > max_page:
                break

    close_driver(driver)

main()