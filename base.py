import csv
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver():
    """Configure and initialize the Selenium driver."""
    options = Options()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--log-level=3")  # Reduce unnecessary logs

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def scrape_details(url, driver):
    """Access a car listing page and scrape additional details."""
    driver.get(url)
    time.sleep(3)  # Allow the page to load

    try:
        # ✅ Scroll down to load all content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        # ✅ Click on "Show more details" if available
        try:
            show_more_button = driver.find_element(By.XPATH, "//button[contains(., 'Afficher plus de détails')]")
            show_more_button.click()
            time.sleep(2)  # Wait for additional details to load
        except:
            pass  # If the button is not found, continue normally

        # ✅ Ensure details section is present
        try:
            details_section = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//div[@class='sc-qmn92k-0 cjptpz']"))
            )
        except:
            print(f"⚠️ Could not find details section for {url}")
            return ["N/A"] * 12  # Return empty values if details not found

        # ✅ Extract details into a dictionary
        details = {}
        details_list = details_section.find_elements(By.XPATH, ".//li")

        for item in details_list:
            try:
                key_element = item.find_element(By.XPATH, ".//span[@class='sc-1x0vz2r-0 jZyObG']")
                value_element = item.find_element(By.XPATH, ".//span[@class='sc-1x0vz2r-0 gSLYtF']")
                
                key = key_element.text.strip()
                value = value_element.text.strip()
                details[key] = value
            except:
                continue  # Skip items that cause issues

        # ✅ Extract specific values in English
        car_type = details.get("Type", "N/A")
        location = details.get("Secteur", "N/A")
        mileage = details.get("Kilométrage", "N/A")
        brand = details.get("Marque", "N/A")
        model = details.get("Modèle", "N/A")
        doors = details.get("Nombre de portes", "N/A")
        origin = details.get("Origine", "N/A")
        first_hand = details.get("Première main", "N/A")
        fiscal_power = details.get("Puissance fiscale", "N/A")
        condition = details.get("État", "N/A")

        # ✅ Extract Equipment List
        try:
            equipment_section = driver.find_element(By.XPATH, "//div[@class='sc-1g3sn3w-15 evEiLa']")
            equipment_list = equipment_section.find_elements(By.XPATH, ".//span[@class='sc-1x0vz2r-0 bXFCIH']")
            equipments = [eq.text.strip() for eq in equipment_list]
        except:
            equipments = ["N/A"]  # If no equipment is found

        equipment_text = ", ".join(equipments)

        # ✅ Extract Seller's City
        try:
            city_section = driver.find_element(By.XPATH, "//div[@class='sc-1g3sn3w-7 bNWHpB']")
            city_element = city_section.find_element(By.XPATH, ".//span[@class='sc-1x0vz2r-0 iotEHk']")
            seller_city = city_element.text.strip()
        except:
            seller_city = "N/A"  # If city is not found

        return [car_type, location, mileage, brand, model, doors, origin, first_hand, fiscal_power, condition, equipment_text, seller_city]

    except Exception as e:
        print(f"❌ Error scraping {url}: {e}")
        return ["N/A"] * 12  # Return empty values on error



def process_csv(input_csv, output_csv):
    """Read the main CSV file and scrape additional details for each listing."""
    driver = setup_driver()

    # ✅ Read URLs from the CSV file
    with open(input_csv, "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        headers = next(reader)  # Read header row
        listings = [row for row in reader]

    # ✅ New headers: Merge old headers + new details (without URL)
    new_headers = [
        "ID", "Title", "Price", "Publication Date", "Year", "Fuel Type", "Transmission", "Seller",
        "Car Type", "Location", "Mileage", "Brand", "Model", "Doors", "Origin", "First Hand", "Fiscal Power", "Condition", "Equipment", "Seller City"
    ]


    detailed_data = [new_headers]

    for idx, row in enumerate(listings, start=1):
        url = row[-1]  # The last column contains the URL
        print(f"🔎 Scraping listing {idx}/{len(listings)} : {url}")

        details = scrape_details(url, driver)
        combined_data = row[:-1] + details  # Merge old data + new details (exclude URL)
        detailed_data.append(combined_data)

    driver.quit()

    # ✅ Save the extracted details
    os.makedirs("data", exist_ok=True)
    with open(output_csv, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerows(detailed_data)

    print(f"✅ Details saved in {output_csv}")

if __name__ == "__main__":
    process_csv("data/avito_listings.csv", "data/avito_details.csv")