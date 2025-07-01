import os                             
import asyncio                        
from datetime import datetime         
from urllib.parse import urljoin     
import aiohttp
from bs4 import BeautifulSoup  



# import re
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service as ChromeService
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.common.exceptions import TimeoutException
# from webdriver_manager.chrome import ChromeDriverManager

import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager


# Basic urls
START_URL = os.getenv("START_URL")


async def fetch_html(session: aiohttp.ClientSession, url: str) -> str:
    """
        Method sends a get-request using url argument,
        then checks resonse status and if it's not 200
        it raises exception.
        If everything is ok, it returns string (html) and
        this string is ready for parsing.
    """
    async with session.get(url) as resp:

        # Rise the exception if fail
        resp.raise_for_status()

        return await resp.text()
    


def parse_links(html: str) -> list[str]:
    """
        Method parses and saves all links on cards
        and returns as list of strings.
    """
    bs = BeautifulSoup(html, "lxml")
    
    # Find all div.hide, which have data-link-to-view
    all_cards = bs.find_all("div", class_="hide",
                          attrs={"data-link-to-view": True})
    
    # Here we will store all references to cards
    all_links = []

    for card in all_cards:
        # Read a path from the attribute
        current_path = card["data-link-to-view"]

        # Skip if there is no path to card
        if not current_path:
            continue
        
        # Make URL
        url = urljoin(START_URL, current_path)

        # Add to the list
        all_links.append(url)
    
    return all_links


def get_reference_on_next_page(html:str) ->str | None:
    """
    Method finds <a class="page-link active">.
    Use its next selcetor<a class="page-link"> and
    returns its href. 
    Otherwise return None.
    """

    soup = BeautifulSoup(html, "html.parser")

    # Find the <nav> element that contains pagination
    #  links (has class "pager")
    nav = soup.select_one("nav.pager")
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


#**************************************************************************
# def fetch_phone_with_chrome(detail_url: str, timeout: int = 10) -> str | None:
#     path = ChromeDriverManager().install()
#     options = webdriver.ChromeOptions()
#     options.add_argument("--headless=new")
#     options.add_argument("--disable-gpu")
#     driver = webdriver.Chrome(service=ChromeService(path), options=options)

#     try:
#         driver.set_page_load_timeout(timeout)
#         driver.get(detail_url)

#         wait = WebDriverWait(driver, timeout)

#         # 1) Закрываем возможный баннер/уведомление
#         try:
#             notif_close = WebDriverWait(driver, 3).until(
#                 EC.element_to_be_clickable((By.CSS_SELECTOR, ".c-notifier-close"))
#             )
#             notif_close.click()
#             wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".c-notifier-container")))
#         except TimeoutException:
#             pass

#         # 2) Скроллим и кликаем по кнопке «Показати»
#         btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.phone_show_link")))
#         driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
#         driver.execute_script("arguments[0].click();", btn)

#         # 3) Ждём появления номера
#         phone_el = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "span.phone.bold")))
#         raw = phone_el.text

#         # 4) Очищаем до цифр
#         return re.sub(r"\D", "", raw) or None

#     finally:
#         driver.quit()
#****************************************************************************


#========================================================================
# 1) Создаём и настраиваем единый драйвер
def create_driver() -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    # headless-режим
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    # отключаем картинки, стили, шрифты
    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.managed_default_content_settings.stylesheets": 2,
        "profile.managed_default_content_settings.fonts": 2,
    }
    options.add_experimental_option("prefs", prefs)
    # блокируем мультимедиа через CDP
    driver = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()),
        options=options
    )
    driver.execute_cdp_cmd("Network.enable", {})
    driver.execute_cdp_cmd("Network.setBlockedURLs", {
        "urls": ["*.png", "*.jpg", "*.jpeg", "*.gif", "*.css", "*.woff2", "*.ttf"]
    })
    return driver

# 2) Функция вытягивает телефон из одной страницы
def fetch_phone(driver: webdriver.Chrome,
                detail_url: str,
                timeout: float = 5.0,
                poll: float = 0.1) -> str | None:
    wait = WebDriverWait(driver, timeout, poll_frequency=poll)
    driver.set_page_load_timeout(timeout)
    driver.get(detail_url)

    # 2.1) Закрываем возможный оверлей (например c-notifier)
    try:
        btn_close = WebDriverWait(driver, 2, poll_frequency=poll).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".c-notifier-close"))
        )
        btn_close.click()
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".c-notifier-container")))
    except TimeoutException:
        pass  # оверлей не появился

    # 2.2) Находим и кликаем по кнопке «Показати»
    btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.phone_show_link")))
    # скролл и JS-клик
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
    driver.execute_script("arguments[0].click();", btn)

    # 2.3) Ждём появления элемента с номером
    phone_el = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "span.phone.bold")))
    raw = phone_el.text  # например "(067) 950 96 07"

    # 2.4) Очищаем до цифр
    digits = re.sub(r"\D", "", raw)
    return digits or None

#========================================================================

async def main():

    # url = "https://auto.ria.com/uk/auto_mazda_cx_30_38402227.html"
    # phone = fetch_phone_with_chrome(url)
    # print("RESULT →", phone)

    car_urls = [
        "https://auto.ria.com/uk/auto_mazda_cx_30_38402227.html",
        "https://auto.ria.com/auto_porsche_cayenne_38301045.html",
        # ... другие ссылки
    ]

    driver = create_driver()
    try:
        for link in car_urls:
            phone = fetch_phone(driver, link)
            print(link, "→", phone)
    finally:
        driver.quit()

    # Create a session and execute fetch_html
    async with aiohttp.ClientSession() as session:
        html = await fetch_html(session, START_URL)

    # Phone
    
    
    # Get all available links
    links = parse_links(html)
    
    # Print it
    for url in links:
        print(url)

    # Is here a reference on the next page?
    next_page = get_reference_on_next_page(html)
    if next_page:
        print(next_page)
    else:
        print("Couldn't fimd a reference on the next page.")

    # Test fields parsers**********************************************

    car_url = "https://auto.ria.com/uk/auto_mazda_cx_30_38402227.html"
    async with aiohttp.ClientSession() as session:
        html = await fetch_html(session, car_url)

    
    bs = BeautifulSoup(html, "lxml")

    # Title parser
    title = parse_title(bs)
    if title:
        print(title)
    else:
        print("Couldn't parse a title of the car page")

    # Price parser
    price  = parse_price_usd(bs)
    print(price) if price else print("Couldn't parse a price of the car page")

    # Odometer parser
    odometer_value = parse_odometer(bs)
    print(odometer_value) if odometer_value else print("Couldn't parse an odometer value of the car page")

    # Username parser
    username = parse_username(bs)
    print(username) if username else print("Couldn't parse an username value of the car page")

    # Phone parser

if __name__ == "__main__":
    asyncio.run(main())