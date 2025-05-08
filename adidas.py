"""
Objective: Web scraping Adidas (using Firefox)
"""

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd

# Setup Firefox options
options = Options()
options.add_argument('--headless')  # Headless Firefox
options.add_argument('--disable-gpu')  # Optional

# Initialize WebDriver (Firefox)
driver = webdriver.Firefox(options=options)

driver.get("https://www.adidas.com/us/")

try:
    # Tunggu hingga produk dimuat
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='product-card-main']"))
    )

    products = driver.find_elements(By.CSS_SELECTOR, "[data-testid='product-card-main']")

    data_products = [
        [
            "Name",
            "Price",
            "Image",
            "Link"
        ]
    ]

    for product in products:
        # Ambil nama produk
        product_name = product.find_element(By.CLASS_NAME, "_product-card-content-main__name_36dpn_83").text
        # Ambil harga produk
        product_price = product.find_element(By.CSS_SELECTOR, "[data-testid='main-price']").find_elements(By.TAG_NAME, "span")
        product_price = product_price[1].text if len(product_price) > 1 else product_price[0].text

        # Ambil gambar produk
        product_image = product.find_element(By.CSS_SELECTOR, "[data-testid='product-card-assets']").find_element(By.TAG_NAME, "img").get_attribute("src")
        
        # Ambil link produk
        product_link = product.find_element(By.TAG_NAME, "a").get_attribute("href")

        product_detail = [
            product_name,
            product_price,
            product_image,
            product_link
        ]

        data_products.append(product_detail)

        

except Exception as e:
    print("Error during scraping:", e)

finally:
    driver.quit()


# Save to CSV
df = pd.DataFrame(data_products[1:], columns=data_products[0])
df.to_csv("adidas_products.csv", index=False)
print("Scraping completed. Data saved to adidas_products.csv")