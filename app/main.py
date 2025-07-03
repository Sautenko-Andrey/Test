import asyncio
import aiohttp

from db import engine, SessionLocal
from models import Base, Car, AdsListing
import scrapper
from sqlalchemy.exc import IntegrityError


# Initialize the schema of darabase(cars and listings) once at the start
Base.metadata.create_all(bind=engine)


def save_all(items: list[dict]) -> None:
    """
        Save a list of parsing results into database.
        Call it after every single page processing.
    """

    session = SessionLocal()
    try:
        for item in items:
            # Find an exsisitng car by url
            car = session.query(Car).filter_by(url=item["url"]).first()
            if not car:
                # If couldn't find create a new record (Car)
                car = Car(
                    url=item["url"],
                    title=item["title"],
                    username=item["username"],
                    image_url=item["image_url"]
                )
                session.add(car)
                # Car id has to show up before a commit
                session.flush()

            # Make a new record (Listing)
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

        # One commit per page
        session.commit()
    except IntegrityError:
        # Skip existing records
        session.rollback()
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

            # Get HTML
            html = await scrapper.fetch_html(session, url)
            links = scrapper.parse_links(html)

            # Parallel parsing
            tasks = [scrapper.parse_detail(session, link) for link in links]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Split succesfull and fails parsing ops
            page_data = []
            for r in results:
                if isinstance(r, dict):
                    page_data.append(r)
                else:
                    print("Error:", r)

            # Save results for the page
            if page_data:
                save_all(page_data)
                print(f"  Сохранено записей: {len(page_data)}")
                total_saved += len(page_data)

            # Prepeare for the next page
            url = scrapper.get_reference_on_next_page(html)
            page += 1

    # Close the driver
    scrapper._DRIVER.quit()

    print(f"Done, total saved: {total_saved}")


if __name__ == "__main__":
    asyncio.run(main())
