# app/main.py

import asyncio
import aiohttp

from db import engine, SessionLocal
from models import Base, Car, AdsListing
import scrapper

# -----------------------------------------------------------------------------
# Инициализируем схему (таблицы cars и listings) один раз при старте приложения
# -----------------------------------------------------------------------------
Base.metadata.create_all(bind=engine)


def save_all(items: list[dict]) -> None:
    """
    Сохраняет список результатов парсинга в базу.
    Вызываем после обработки каждой страницы.
    """
    session = SessionLocal()
    try:
        for item in items:
            # 1) Найти существующий Car по URL
            car = session.query(Car).filter_by(url=item["url"]).first()
            if not car:
                # если не найден — создаём новую запись
                car = Car(
                    url=item["url"],
                    title=item["title"],
                    username=item["username"],
                    image_url=item["image_url"]
                )
                session.add(car)
                session.flush()  # нужно, чтобы car.id появился до коммита

            # 2) Создать запись о парсинге (Listing)
            listing = AdsListing(
                car_id=car.id,
                datetime_found=item["datetime_found"],
                price_usd=item["price_usd"],
                odometer=item["odometer"],
                phone_number=item["phone_number"],
                car_number=item["car_number"],
                car_vin=item["car_vin"]
            )
            session.add(listing)

        session.commit()  # один коммит на всю страницу
    except:
        session.rollback()
        raise
    finally:
        session.close()


async def main():
    print(">>> Запуск main.py")
    async with aiohttp.ClientSession() as session:
        url, page = scrapper.START_URL, 1
        total_saved = 0

        while url:
            print(f"Page {page}: {url}")

            # получаем HTML и ссылки на детали
            html = await scrapper.fetch_html(session, url)
            links = scrapper.parse_links(html)

            # парсим детали параллельно
            tasks = [scrapper.parse_detail(session, link) for link in links]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # разделяем успешные парсы и ошибки
            page_data = []
            for r in results:
                if isinstance(r, dict):
                    page_data.append(r)
                else:
                    print("Error:", r)

            # сохраняем результаты по этой странице
            if page_data:
                save_all(page_data)
                print(f"  Сохранено записей: {len(page_data)}")
                total_saved += len(page_data)

            # готовимся к следующей странице
            url = scrapper.get_reference_on_next_page(html)
            page += 1

    # закрываем драйвер Chrome в конце
    scrapper._DRIVER.quit()

    print(f"Done, total saved: {total_saved}")


if __name__ == "__main__":
    asyncio.run(main())
