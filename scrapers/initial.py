import time
import csv
import os
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import re

def setup_driver():
    """Configure et initialise le driver Selenium."""
    options = Options()
    options.add_argument("--headless")  # Exécuter sans interface graphique
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--log-level=3")  # Réduire les logs inutiles

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver



def convert_relative_date(relative_date):
    """Convertit une date relative en date exacte.
    
    - Stocke l’heure uniquement pour minutes et heures
    - Ne garde que la date pour jours, mois, et années
    """
    now = datetime.now()

    # ✅ Cas "il y a quelques instants" → prendre l'heure actuelle
    if "quelques instants" in relative_date.lower():
        return now.strftime("%Y-%m-%d %H:%M:%S")  # Date et heure actuelles

    # ✅ Extraction du nombre (ex: "5" dans "il y a 5 minutes")
    match = re.search(r'(\d+)', relative_date)
    if match:
        num = int(match.group(1))  # Convertir en entier
    else:
        return "Date inconnue"  # Aucun nombre trouvé

    # ✅ Gestion des cas spécifiques
    if "minute" in relative_date:
        exact_date = now - timedelta(minutes=num)
        return exact_date.strftime("%Y-%m-%d %H:%M:%S")  # Garde l'heure

    elif "heure" in relative_date:
        exact_date = now - timedelta(hours=num)
        return exact_date.strftime("%Y-%m-%d %H:%M:%S")  # Garde l'heure

    elif "jour" in relative_date:
        exact_date = now - timedelta(days=num)
        return exact_date.strftime("%Y-%m-%d")  # Supprime l'heure

    elif "mois" in relative_date:
        exact_date = now - timedelta(days=30 * num)  # Approximation
        return exact_date.strftime("%Y-%m-%d")  # Supprime l'heure

    elif "an" in relative_date:
        exact_date = now - timedelta(days=365 * num)  # Approximation
        return exact_date.strftime("%Y-%m-%d")  # Supprime l'heure

    else:
        return "Date inconnue"  # Cas non prévu







def scrape_avito():
    """Scrape les annonces de voitures sur Avito avec conversion des dates."""
    url = "https://www.avito.ma/fr/maroc/voitures_d'occasion-à_vendre"
    driver = setup_driver()
    driver.get(url)

    # ✅ Attendre que la page se charge correctement
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "sc-1nre5ec-1")))
    except Exception as e:
        print(f"❌ Timeout: Impossible de charger la page ({e})")
        driver.quit()
        return

    data = []
    
    try:
        # **Trouver le conteneur principal**
        main_container = driver.find_element(By.CLASS_NAME, "sc-1nre5ec-1")

        # **Récupérer toutes les annonces**
        listings = main_container.find_elements(By.CSS_SELECTOR, "a.sc-1jge648-0.jZXrfL")

        if not listings:
            print("❌ Aucune annonce trouvée ! Vérifie si le site a changé.")
            return

        print(f"✅ {len(listings)} annonces trouvées !")

        # **Parcourir les annonces**
        for idx, listing in enumerate(listings, start=1):
            try:
                # **Titre**
                title = listing.find_element(By.CSS_SELECTOR, "p.sc-1x0vz2r-0.iHApav").text.strip() if listing.find_elements(By.CSS_SELECTOR, "p.sc-1x0vz2r-0.iHApav") else "N/A"

                # **Prix**
                price = listing.find_element(By.CSS_SELECTOR, "p.sc-1x0vz2r-0.dJAfqm").text.strip() if listing.find_elements(By.CSS_SELECTOR, "p.sc-1x0vz2r-0.dJAfqm") else "Prix non spécifié"

                # **Date de publication**
                pub_date_raw = listing.find_element(By.CSS_SELECTOR, "p.sc-1x0vz2r-0.layWaX").text.strip() if listing.find_elements(By.CSS_SELECTOR, "p.sc-1x0vz2r-0.layWaX") else "N/A"
                pub_date = convert_relative_date(pub_date_raw)  # Convertir en date exacte

                # **Année**
                year = listing.find_element(By.XPATH, ".//span[contains(text(),'20')]").text.strip() if listing.find_elements(By.XPATH, ".//span[contains(text(),'20')]") else "N/A"

                # **Type de carburant**
                fuel_type = listing.find_element(By.XPATH, ".//span[contains(text(),'Essence') or contains(text(),'Diesel') or contains(text(),'Hybride') or contains(text(),'Électrique')]").text.strip() if listing.find_elements(By.XPATH, ".//span[contains(text(),'Essence') or contains(text(),'Diesel') or contains(text(),'Hybride') or contains(text(),'Électrique')]") else "N/A"

                # **Transmission**
                transmission = listing.find_element(By.XPATH, ".//span[contains(text(),'Automatique') or contains(text(),'Manuelle')]").text.strip() if listing.find_elements(By.XPATH, ".//span[contains(text(),'Automatique') or contains(text(),'Manuelle')]") else "N/A"

                # **Lien de l'annonce**
                link = listing.get_attribute("href") if listing.get_attribute("href") else "N/A"

                # **Nom du créateur**
                creator = "Particulier"
                try:
                    creator_element = listing.find_element(By.CSS_SELECTOR, "p.sc-1x0vz2r-0.hNCqYw.sc-1wnmz4-5.dXzQnB")
                    creator = creator_element.text.strip() if creator_element else "Particulier"
                except:
                    pass  # Si aucun nom trouvé, on met "Particulier" par défaut

                # **Sauvegarde des données**
                data.append([idx, title, price, pub_date, year, fuel_type, transmission, creator, link])

            except Exception as e:
                print(f"⚠️ Erreur avec l'annonce {idx}: {e}")

    except Exception as e:
        print(f"❌ Erreur lors de l'extraction: {e}")

    driver.quit()

    # **Enregistrement CSV**
    save_to_csv(data)

def save_to_csv(data):
    """Sauvegarde les données dans un fichier CSV."""
    output_folder = "data"
    os.makedirs(output_folder, exist_ok=True)
    output_file = os.path.join(output_folder, "avito_listings.csv")

    with open(output_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["ID", "Titre", "Prix", "Date de publication", "Année", "Type de carburant", "Transmission", "Créateur", "URL de l'annonce"])
        writer.writerows(data)

    print(f"✅ Données sauvegardées dans {output_file}")

if __name__ == "__main__":
    scrape_avito()
