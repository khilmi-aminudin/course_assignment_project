import argparse
import logging
import csv
import json
import requests
import time
from bs4 import BeautifulSoup as bs
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "http://books.toscrape.com/"
NUMBER_OF_PAGE = 50

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
    
def fetch_page(url:str) -> str:
    # Simulate fetching a page
    logging.info(f"Fetching {url}")
    
    result = ""
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
        result =  response.text
        return result
    except requests.RequestException as e:
        logging.error(f"Error fetching {url}: {e}")
        return result

def parse_page(page:str) -> list[dict]:
    # Simulate parsing a page
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

            data.append({
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
            })

            logging.info(f"TITLE: {title}, PRICE: {price}, BOOK URL: {book_url}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error: {e}")
        
    return data

def get_books_detail(book:dict) -> dict:
    try:
        logging.info(f'get detail book {book.get('title')}')
        response = requests.get(book.get('book_url'))
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
    except requests.exceptions.RequestException as e:
        logging.info(f'failed get detail book {book.get('title')}')
        logging.error(f"Error: {e}")
    
    return book




def main():
    start_time = time.time()
    
    pages = ''

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(fetch_page, f"{BASE_URL}catalogue/page-{i+1}.html") for i in range(NUMBER_OF_PAGE)]
        pages = [future.result() for future in futures]

    data = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(parse_page, page) for page in pages]
        data = [item for future in futures for item in future.result()]
    
    result = []
    with ThreadPoolExecutor(max_workers=500) as executor:
        futures = [executor.submit(get_books_detail, d) for d in data]
        for future in futures:
            try:
                result.append(future.result())
            except Exception as e:
                logging.error(f"Error getting book details: {e}")

    save_to_file('csv', 'books', result)
    end_time = time.time()
    logging.info(f"Execution time: {end_time - start_time} seconds")
    logging.info("Finished scraping books.toscrape.com")

if __name__ == "__main__":
    main()