import asyncio, aiohttp
import scrapper

async def main():

    print(">>> Запуск main.py")


    async with aiohttp.ClientSession() as session:

        url, page, all_data = scrapper.START_URL, 1, []

        while url:
            print(f"Page {page}: {url}")

            html = await scrapper.fetch_html(session, url)

            links = scrapper.parse_links(html)

            tasks = [scrapper.parse_detail(session, u) for u in links]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for r in results:
                if isinstance(r, dict):
                    all_data.append(r)
                else:
                    print("Error:", r)
                    
            url = scrapper.get_reference_on_next_page(html)
            page += 1

    # Close driver in the end
    scrapper._DRIVER.quit()
    print("Done, total:", len(all_data))

if __name__=="__main__":
    asyncio.run(main())
