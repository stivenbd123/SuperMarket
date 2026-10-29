"""Prueba del Paso 4 con Selenium: ¿refurb.me carga o sale el reto de Cloudflare?

Corre:  python check_selenium.py
Si imprime BLOQUEADO, no sigas con el scraper así: avísame y lo replanteamos.
"""
import json
import time

from selenium import webdriver

URL = "https://www.refurb.me/refurbished/macbook/macbook-pro/16-inch/m1-pro"

options = webdriver.ChromeOptions()  # tu Google Chrome; Selenium Manager baja el driver solo
driver = webdriver.Chrome(options=options)
try:
    driver.get(URL)
    time.sleep(5)  # dar tiempo a que cargue (o a que aparezca el reto)
    title = driver.title
    print("titulo:", title)
    if "Just a moment" in title or "Un momento" in title:
        print("BLOQUEADO: Cloudflare mostró el reto.")
    else:
        result = driver.execute_script(
            "return window.__NUXT__ && window.__NUXT__.state.result")
        if not result:
            print("Cargó, pero no hay window.__NUXT__.state.result")
        else:
            print("grupos:", len(result["data"]))
            print("paginacion:", result.get("pagination"))
            print(json.dumps(result["data"][0], indent=2)[:1500])
finally:
    driver.quit()
