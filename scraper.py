import requests
import json
import datetime
import os
import sys
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import time

# Configuration
OUTPUT_FILE = "data.js"  # Kept for legacy/fallback if needed

# VTEX API endpoints
VTEX_RETAILERS = [
    {
        "name": "Olímpica",
        "search_url": "https://www.olimpica.com/api/catalog_system/pub/products/search",
        "base_url": "https://www.olimpica.com"
    },
    {
        "name": "Éxito",
        "search_url": "https://www.exito.com/api/catalog_system/pub/products/search",
        "base_url": "https://www.exito.com"
    },
    {
        "name": "Carulla",
        "search_url": "https://www.carulla.com/api/catalog_system/pub/products/search",
        "base_url": "https://www.carulla.com"
    },
    {
        "name": "Jumbo",
        "search_url": "https://www.tiendasjumbo.co/api/catalog_system/pub/products/search",
        "base_url": "https://www.tiendasjumbo.co"
    },
    {
        "name": "Metro",
        "search_url": "https://www.tiendasmetro.co/api/catalog_system/pub/products/search",
        "base_url": "https://www.tiendasmetro.co"
    },
    {
        "name": "Makro",
        "search_url": "https://www.makro.com.co/api/catalog_system/pub/products/search",
        "base_url": "https://www.makro.com.co"
    }
]

def progress_update(retailer, status, message=""):
    """Emit progress update as JSON to stderr for server to capture"""
    update = {
        "type": "progress",
        "retailer": retailer,
        "status": status,  # "starting", "success", "error", "skipped"
        "message": message
    }
    sys.stderr.write(f"PROGRESS:{json.dumps(update)}\n")
    sys.stderr.flush()

def fetch_vtex_prices(search_term):
    """Fetch prices from VTEX-based retailers"""
    all_data = []
    sys.stderr.write(f"[VTEX] Buscando en tiendas VTEX...\n")

    for retailer in VTEX_RETAILERS:
        try:
            progress_update(retailer['name'], "starting", f"Consultando {retailer['name']}...")
            sys.stderr.write(f"  Consultando {retailer['name']}...\n")
            params = {"ft": search_term}
            response = requests.get(retailer['search_url'], params=params, timeout=12)
            response.raise_for_status()
            products = response.json()

            count = 0
            for p in products:
                p_name = p.get("productName", "").lower()
                if any(word in p_name for word in search_term.lower().split()):
                    try:
                        sku = p['items'][0]
                        seller = sku['sellers'][0]
                        price = seller['commertialOffer']['Price']
                        product_url = p.get("link", "")
                        
                        if product_url and not product_url.startswith("http"):
                            product_url = retailer['base_url'] + product_url

                        if price > 0:
                            all_data.append({
                                "brand": search_term.capitalize(),
                                "name": p.get("productName", ""),
                                "size": sku.get("nameComplete", "").split(" ")[-1],
                                "price": price,
                                "supermarket": retailer['name'],
                                "url": product_url,
                                "category": "Decaf" if "descafeinado" in p_name else "Classic"
                            })
                            count += 1
                    except (KeyError, IndexError):
                        continue
            
            progress_update(retailer['name'], "success", f"{count} productos encontrados")
        except Exception as e:
            sys.stderr.write(f"  Error consultando {retailer['name']}: {e}\n")
            progress_update(retailer['name'], "error", str(e))

    return all_data

def fetch_d1_prices(search_term):
    """Fetch prices from D1 using Playwright"""
    all_data = []
    progress_update("D1", "starting", "Consultando D1...")
    sys.stderr.write(f"[D1] Buscando en D1...\n")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_default_timeout(15000)
            
            # Navigate to D1 search
            search_url = f"https://domicilios.tiendasd1.com/search/?text={search_term.replace(' ', '%20')}"
            sys.stderr.write(f"  Navegando a: {search_url}\n")
            page.goto(search_url, wait_until="networkidle")
            time.sleep(2)  # Wait for dynamic content
            
            # Extract products
            products = page.query_selector_all(".product-item, .vtex-product-summary")
            sys.stderr.write(f"  Encontrados {len(products)} productos\n")
            
            for product in products[:10]:  # Limit to first 10
                try:
                    name_elem = product.query_selector(".product-name, .vtex-product-summary__product-brand")
                    price_elem = product.query_selector(".price, .vtex-product-price")
                    link_elem = product.query_selector("a")
                    
                    if name_elem and price_elem:
                        name = name_elem.inner_text().strip()
                        price_text = price_elem.inner_text().strip()
                        price = float(price_text.replace("$", "").replace(".", "").replace(",", "").strip())
                        url = link_elem.get_attribute("href") if link_elem else ""
                        
                        if not url.startswith("http"):
                            url = "https://domicilios.tiendasd1.com" + url
                        
                        all_data.append({
                            "brand": search_term.capitalize(),
                            "name": name,
                            "size": "N/A",
                            "price": price,
                            "supermarket": "D1",
                            "url": url,
                            "category": "Classic"
                        })
                except Exception as e:
                    continue
            
            browser.close()
            progress_update("D1", "success", f"{len(all_data)} productos encontrados")
    except Exception as e:
        sys.stderr.write(f"  Error consultando D1: {e}\n")
        progress_update("D1", "error", str(e))
    
    return all_data

def fetch_alkosto_prices(search_term):
    """Fetch prices from Alkosto using Playwright"""
    all_data = []
    progress_update("Alkosto", "starting", "Consultando Alkosto...")
    sys.stderr.write(f"[Alkosto] Buscando en Alkosto...\n")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_default_timeout(15000)
            
            search_url = f"https://www.alkosto.com/search?q={search_term.replace(' ', '+')}"
            sys.stderr.write(f"  Navegando a: {search_url}\n")
            page.goto(search_url, wait_until="networkidle")
            time.sleep(2)
            
            products = page.query_selector_all(".product, .product-item")
            sys.stderr.write(f"  Encontrados {len(products)} productos\n")
            
            for product in products[:10]:
                try:
                    name_elem = product.query_selector(".product-name, h3, .name")
                    price_elem = product.query_selector(".price, .product-price")
                    link_elem = product.query_selector("a")
                    
                    if name_elem and price_elem:
                        name = name_elem.inner_text().strip()
                        price_text = price_elem.inner_text().strip()
                        price = float(price_text.replace("$", "").replace(".", "").replace(",", "").strip())
                        url = link_elem.get_attribute("href") if link_elem else ""
                        
                        if url and not url.startswith("http"):
                            url = "https://www.alkosto.com" + url
                        
                        all_data.append({
                            "brand": search_term.capitalize(),
                            "name": name,
                            "size": "N/A",
                            "price": price,
                            "supermarket": "Alkosto",
                            "url": url,
                            "category": "Classic"
                        })
                except Exception as e:
                    continue
            
            browser.close()
            progress_update("Alkosto", "success", f"{len(all_data)} productos encontrados")
    except Exception as e:
        sys.stderr.write(f"  Error consultando Alkosto: {e}\n")
        progress_update("Alkosto", "error", str(e))
    
    return all_data

def fetch_ara_prices(search_term):
    """Fetch prices from Ara (placeholder - may not have online catalog)"""
    progress_update("Ara", "skipped", "Sin catálogo en línea")
    sys.stderr.write(f"[Ara] Ara no tiene catálogo en línea disponible\n")
    return []

def fetch_pricesmart_prices(search_term):
    """Fetch prices from PriceSmart (placeholder - requires membership)"""
    progress_update("PriceSmart", "skipped", "Requiere membresía")
    sys.stderr.write(f"[PriceSmart] PriceSmart requiere membresía para ver precios\n")
    return []

def group_by_product(raw_data):
    grouped = {}
    for item in raw_data:
        key = f"{item['name']}_{item['size']}"
        if key not in grouped:
            grouped[key] = {
                "brand": item["brand"],
                "name": item["name"],
                "size": item["size"],
                "category": item["category"],
                "prices": []
            }
        grouped[key]["prices"].append({
            "supermarket": item["supermarket"],
            "price": item["price"],
            "url": item["url"]
        })
    
    result = []
    for i, (key, value) in enumerate(grouped.items()):
        value["id"] = i + 1
        result.append(value)
    return result

def get_live_data(search_term):
    all_results = []
    
    # Fetch from all sources
    all_results.extend(fetch_vtex_prices(search_term))
    all_results.extend(fetch_d1_prices(search_term))
    all_results.extend(fetch_alkosto_prices(search_term))
    all_results.extend(fetch_ara_prices(search_term))
    all_results.extend(fetch_pricesmart_prices(search_term))
    
    if all_results:
        return group_by_product(all_results)
    return []

if __name__ == "__main__":
    term = sys.argv[1] if len(sys.argv) > 1 else "cafe buendia"
    results = get_live_data(term)
    print(json.dumps({
        "data": results,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "search": term
    }, ensure_ascii=False))
