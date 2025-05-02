import logging
import csv
import json
import httpx
import time
from bs4 import BeautifulSoup as bs
import asyncio

BASE_URL = "http://books.toscrape.com/"
NUMBER_OF_PAGE = 50

semaphore = asyncio.Semaphore(100)

def save_to_file(output:str, filename:str , data:list[dict]) -> None:
    # print(f"output: {output}, filename: {filename}, data: {len(data)}")
    if output == "json":
        with open(f"{filename}.{output}", "w", encoding="utf-8") as f:
            json.dump(data, f,ensure_ascii=False, indent=4)
    elif output == "csv":
        with open(f"{filename}.{output}", "w") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
    else:
        logging.error("error invalid output file format")
        return

    logging.info("succes save to file")
    
async def fetch_page(url:str, client:httpx.AsyncClient) -> str:
    # Simulate fetching a page
    async with semaphore:
        logging.info(f"Fetching {url}")
    
        result = ""
        try:
            response = await client.get(url)
            response.raise_for_status()  # Raise an error for bad responses
            result =  response.text
            return result
        except httpx.HTTPStatusError as e:
            logging.error(f"Error fetching {url}: {e}")
            return result
        except Exception as e:
            logging.error(f"Error fetching {url}: {e}")
            return result

async def parse_page(page:str) -> list[dict]:
    # Simulate parsing a page
    async with semaphore:
        logging.info("Parsing page")
        
        data = []
        try:
            soup = bs(page, "html.parser")
            books = soup.find_all('article', class_='product_pod')

            for book in books:
                title = book.h3.a.get_text()
                price = book.find('p', class_='price_color').get_text()
                book_url = book.h3.a['href']
                book_url = f"{BASE_URL}catalogue/{book_url}"
                
                data_founded = {
                    'title': title,
                    'price': price,
                    'book_url': book_url,
                    'cover_image_url': None,
                    'product_description':None,
                    'upc': None,
                    'product_type': None,
                    'price_before_tax': None,
                    'price_after_tax': None,
                    'tax': None,
                    'stock': None,
                    'number_of_reviews': None
                }

                data.append(data_founded)

                logging.info(f"TITLE: {title}, PRICE: {price}, BOOK URL: {book_url}")
        except Exception as e:
            logging.error(f"Error: {e}")
            
        return data

async def get_books_detail(book:dict, client:httpx.AsyncClient) -> dict:
    async with semaphore:
        try:
            logging.info(f'get detail book {book.get('title')}')
            response = await client.get(book.get('book_url'))
            response.raise_for_status()

            soup = bs(response.text, "html.parser")

            p_tag = soup.find_all('p')
            product_description = p_tag[3].get_text()

            img_url = soup.find('img')['src'].replace('../..', BASE_URL)

            table = soup.find('table', class_='table table-striped')
            td_data = table.find_all('td') 

            book['product_description'] = product_description
            book['cover_image_url'] = img_url
            book['upc'] = td_data[0].get_text()
            book['product_type'] = td_data[1].get_text()
            book['price_before_tax'] = td_data[2].get_text()
            book['price_after_tax'] = td_data[3].get_text()
            book['tax'] = td_data[4].get_text()
            book['stock'] = td_data[5].get_text().replace('In stock (','').replace(' available)','')
            book['number_of_reviews'] = td_data[6].get_text()
        except httpx.HTTPStatusError as e:
            logging.info(f'failed get detail book {book.get('title')}')
            logging.error(f"Error: {e}")
        except Exception as e:
            logging.info(f'failed get detail book {book.get('title')}')
            logging.error(f"Error: {e}")
        
        return book




async def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    start_time = time.time()
    
    urls = [f"{BASE_URL}catalogue/page-{i}.html" for i in range(1, NUMBER_OF_PAGE+1)]

    async with httpx.AsyncClient() as client:
        fetch_page_tasks = [asyncio.create_task(fetch_page(url, client)) for url in urls]
        pages = await asyncio.gather(*fetch_page_tasks)


    parse_page_tasks = [asyncio.create_task(parse_page(page)) for page in pages]
    data = await asyncio.gather(*parse_page_tasks)

    data = [item for sublist in data for item in sublist]


    async with httpx.AsyncClient() as client:
        get_books_detail_tasks = [asyncio.create_task(get_books_detail(book, client)) for book in data]
        result = await asyncio.gather(*get_books_detail_tasks)

    print("pages len: ", len(pages))
    print("data len: ", len(data))
    print("result len: ", len(result))


    # pages = None
    # async with httpx.AsyncClient() as client:
    #     fetch_page_tasks = [asyncio.create_task(fetch_page(url, client)) for url in urls]
    #     # pages = await asyncio.gather(*fetch_page_tasks)
    #     for completed_task in asyncio.as_completed(fetch_page_tasks):
    #         pages = await completed_task


    # data = None
    # parse_page_tasks = [asyncio.create_task(parse_page(page)) for page in pages]
    # # data = await asyncio.gather(*parse_page_tasks)
    # for completed_task in asyncio.as_completed(parse_page_tasks):
    #     data = await completed_task

    # data = [item for sublist in data for item in sublist]


    # result = None
    # async with httpx.AsyncClient() as client:
    #     get_books_detail_tasks = [asyncio.create_task(get_books_detail(book, client)) for book in data]
    #     # result = await asyncio.gather(*get_books_detail_tasks)
    #     for completed_task in asyncio.as_completed(get_books_detail_tasks):
    #         result = await completed_task

    # print("pages len: ", len(pages))
    # print("data len: ", len(data))
    # print("result len: ", len(result))

    save_to_file('csv', 'books', result)
    end_time = time.time()
    logging.info(f"Execution time: {end_time - start_time} seconds")
    logging.info("Finished scraping books.toscrape.com")

if __name__ == "__main__":
    asyncio.run(main())