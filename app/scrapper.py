import os                             
import asyncio                        
from datetime import datetime         
from urllib.parse import urljoin     
import aiohttp
from aiohttp import ClientResponseError
from datetime import datetime
from bs4 import BeautifulSoup
import re
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException
)

# Basic url
START_URL = os.getenv("START_URL")

# Http requests limits
_HTTP_SEM   = asyncio.Semaphore(5)

# cards parsers limits
_DETAIL_SEM = asyncio.Semaphore(5)

# lock for the single driver
_PHONE_LOCK = asyncio.Lock()


# Make the single driver
def _create_driver():

    """
        Function create a driver.
    """

    # Set up options
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.page_load_strategy = "eager"
    opts.add_experimental_option("prefs", {
        "profile.managed_default_content_settings.images": 2,
        "profile.managed_default_content_settings.stylesheets": 2,
        "profile.managed_default_content_settings.fonts": 2
    })

    service = Service(ChromeDriverManager().install())

    driver = webdriver.Chrome(service=service, options=opts)

    driver.set_page_load_timeout(15)

    return driver

_DRIVER = _create_driver()


async def fetch_html(session: aiohttp.ClientSession, url: str, retries=3):
    """
        Fetch a html file using timeouts and retries
    """
    for i in range(retries):
        async with _HTTP_SEM:
            try:
                async with session.get(url, timeout=10) as r:
                    r.raise_for_status()
                    return await r.text()
            except ClientResponseError as e:
                if e.status == 429 and i < retries-1:
                    await asyncio.sleep(1 + 2**i * random.random())
                    continue
                raise
            except asyncio.TimeoutError:
                if i < retries-1:
                    await asyncio.sleep(1 + random.random())
                    continue
                raise
    raise RuntimeError("fetch_html failed")


def parse_links(html: str) -> list[str]:
    """
        Fetch data-link-to-view and return absolute URL.
    """
    bs = BeautifulSoup(html, "lxml")

    cards = bs.find_all("div", class_="hide", attrs={"data-link-to-view": True})
    
    links = []

    for card in cards:
        rel = card["data-link-to-view"].strip()

        if not rel:
            continue
        # make full path
        full_path = urljoin(START_URL, rel)
        links.append(full_path)

    return links


def get_reference_on_next_page(html:str) -> str | None:
    """
        Method finds <a class="page-link active">.
        Use its next selcetor<a class="page-link"> and
        returns its href. 
        Otherwise return None.
    """

    bs = BeautifulSoup(html, "lxml")

    # Find the <nav> element that contains pagination
    #  links (has class "pager")
    nav = bs.select_one("nav.pager")
    if not nav:
        return None

    # Inside the nav find the active page <a> tag (class="page-link active")
    active_a = nav.find("a", class_="page-link active")

    if not active_a:
        return None

    # Find its parent container
    page_item = active_a.find_parent("span")

    if not page_item:
        return None

    # Find the next sibling <span> element (the link to the next page)
    next_item = page_item.find_next_sibling("span")

    if not next_item:
        return None

    # Inside that <span>, find the <a class="page-link"> tag
    next_a = next_item.find("a", class_="page-link")
    
    if not next_a or not next_a.has_attr("href"):
        return None

    href = next_a["href"].strip()
    # Ignore"javascript:void(0)"
    if not href or href.startswith("javascript"):
        return None

    return urljoin(START_URL, href)


# Fields parsers
def parse_title(bs: BeautifulSoup) -> str | None:
    """
        Method parses a title of the car page
        and returns it as a string. If it fails,
        then method returns None.
    """

    # Title uses h1.head selector
    title = bs.select_one("h1.head")

    return title.get_text(strip=True) if title else None


def parse_price_usd(soup: BeautifulSoup) -> int | None:
    """
        Method parses a price field of the car page
        and returns it as an integer. If it fails,
        then method returns None.
    """
    price = soup.select_one("div.price_value")
    
    if not price:
        return None
    
    # Clean price string and get a pure integer
    # Replace spaces and $ with ""
    clean_price = price.get_text(strip=True).replace(" ", "").replace("$", "")

    return int(clean_price) if clean_price.isdigit() else None


def parse_odometer(soup: BeautifulSoup) -> int | None:
    """
        Method parses an odometer field of the car page
        and returns it as an integer. If it fails,
        then method returns None.
    """

    # Get an odometer value via span.size18 selector
    odometer = soup.select_one("span.size18")
    
    if not odometer:
        return None
    
    result = odometer.get_text(strip=True)
    
    try:
        # Convert value (Example: 95 -> 95000)
        return int(float(result) * 1000)
    
    except ValueError:
        return None
    

def parse_username(soup: BeautifulSoup) -> str | None:
    """
        Method parses a user name field of the car page
        and returns it as string. If it fails,
        then method returns None.
    """
    name = soup.select_one("#userInfoBlock .seller_info_name.bold a.sellerPro")

    return name.get_text(strip=True) if name else None


# Phone parser
def fetch_phone(detail_url: str, page_timeout: float = 15.0,
                      wait_timeout: float = 10.0, poll: float = 0.2) -> str | None:
    """
        Try to fetch a phone number from car page.
        If something goes wrong (timeout, no button, no number) just return None
        Note: using Selenium!
    """

    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.page_load_strategy = "eager"
    opts.add_experimental_option("prefs", {
        "profile.managed_default_content_settings.images": 2,
        "profile.managed_default_content_settings.stylesheets": 2,
    })

    service = Service(ChromeDriverManager().install())
    driver  = webdriver.Chrome(service=service, options=opts)
    driver.set_page_load_timeout(page_timeout)

    try:
        # Loading
        try:
            driver.get(detail_url)
            
        except TimeoutException:
            print("fetch_phone: page load timeout")
            return None

        wait = WebDriverWait(driver, wait_timeout, poll_frequency=poll)

        # If thereis is an overlay, then close it.
        try:
            btn_close = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".c-notifier-close"))
            )

            btn_close.click()

            wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".c-notifier-container")))
        except TimeoutException:
            # There is no overlay, do nothing
            pass

        # Check if there is a button with name “показати”
        elems = driver.find_elements(By.CSS_SELECTOR, "a.phone_show_link")

        if not elems:
            # No button on the page or a number loads too long
            print("fetch_phone: no phone_show_link on page")
            return None

        btn = elems[0]
        # scroll + click
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        try:
            btn.click()
        except WebDriverException:
            # execute via JS
            driver.execute_script("arguments[0].click();", btn)

        # Waiting a phone number shows up
        try:
            phone_el = wait.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "span.phone.bold"))
            )
        except TimeoutException:
            print("fetch_phone: timeout waiting for span.phone.bold")
            return None

        raw = phone_el.text or ""
        digits = re.sub(r"\D", "", raw)
        return digits or None

    except WebDriverException as e:
        # if unfirtunately fall down into WebDriverException
        print(f"fetch_phone: unexpected error {e.__class__.__name__}: {e!r}")
        return None

    finally:
        driver.quit()



# Image info
def parse_image_info(bs: BeautifulSoup) -> tuple[str|None, int]:

    """
        Method fetches an url of the main image and counts total images
        of the car on the page.
    """

    # Find and fetch main image url
    meta = bs.select_one("meta[property='og:image']")

    main_url = meta["content"] if meta and meta.has_attr("content") else None

    # Find all images
    all_imgs = bs.find_all("img", src=True)

    # Filter images which locate in the gallery
    thumbs = set()
    for img in all_imgs:
        url = img["src"]
        # Select only with '30__' or 'gallery'
        if "30__" in url or "/gallery/" in url:
            thumbs.add(url)

    return main_url, len(thumbs)


# Parser for car number and car vin
def parse_identifiers(bs: BeautifulSoup):
    """
        Find and fetch car number and vin. Return it as tuple.
    """

    # number in <span class="state-num ua">
    plate = None

    plate_el = bs.select_one("span.state-num.ua")

    if plate_el:

        # First part of text before nested tags
        raw = plate_el.find(text=True, recursive=False)

        if raw:
            # Fetch format «XX 1234 XX» via re
            m = re.search(r"[A-ZА-Я]{1,3}\s*\d{1,4}\s*[A-ZА-Я]{1,3}", raw)

            plate = m.group(0).strip() if m else raw.strip()

    # All text inside <span class="label-vin">
    vin = None

    vin_el = bs.select_one("span.label-vin")

    if vin_el:

        raw_vin = vin_el.get_text(strip=True)

        # Leave only letters and digits
        m2 = re.search(r"[A-HJ-NPR-Z0-9]{10,17}", raw_vin)

        vin = m2.group(0) if m2 else raw_vin

    return plate, vin


# The main parser
async def parse_detail(session: aiohttp.ClientSession, url: str) -> dict:
    
    """
        The main parser wich uses all above parsers to fetch the content
        from AUTORIA web-site.
    """

    async with _DETAIL_SEM:
        html = await fetch_html(session, url)
        soup = BeautifulSoup(html, "lxml")

        # Parse all excludong Selenium tasks
        title, price, odo = parse_title(soup), parse_price_usd(soup), parse_odometer(soup)
        
        user = parse_username(soup)
        
        img_url, img_cnt = parse_image_info(soup)
        
        plate, vin = parse_identifiers(soup)

        # And now parse a phone number using lock 
        async with _PHONE_LOCK:
            phone = await asyncio.to_thread(fetch_phone, url)

        # a small pause
        await asyncio.sleep(random.uniform(0.1,0.3))

        return {
            "url":url,
            "title":title,
            "price_usd":price,
            "odometer":odo,
            "username":user,
            "phone_number":phone,
            "image_url":img_url,
            "images_count":img_cnt,
            "car_number":plate,
            "car_vin":vin,
            "datetime_found": datetime.now(),
        }
