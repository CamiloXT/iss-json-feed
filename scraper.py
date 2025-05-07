#!/usr/bin/env python3
# ── scraper.py ───────────────────────────────────────────────────────────
"""
Extrae los pasos visibles de la ISS desde Heavens-Above y los devuelve
agrupados por fecha ISO (YYYY-MM-DD).  Si se ejecuta como script, genera
un archivo 'iss_hoy.json' con los pasos del día actual.
"""
import requests, json
from bs4 import BeautifulSoup
from datetime import datetime
from collections import defaultdict
from typing import Dict, List

# ────────────────────────── CONFIGURACIÓN ────────────────────────────────
URL = ("https://heavens-above.com/PassSummary.aspx?"
       "satid=25544&lat=3.3474&lng=-76.5315&loc=Unnamed&alt=1000&tz=UCT5")

HEADERS = {"Accept-Language": "es"}    # ° y puntos cardinales español
MESES   = "ene feb mar abr may jun jul ago sep oct nov dic".split()

# ────────────────────────── FUNCIONES AUXILIARES ─────────────────────────
def ac2deg(cardinal: str) -> int:
    """Convierte texto cardinal a grados (0-360). Retorna -1 si no existe."""
    tabla = {
        "N":0,"NNE":22,"NE":45,"ENE":67,"E":90,"ESE":112,"SE":135,"SSE":157,
        "S":180,"SSO":202,"SO":225,"OSO":247,"O":270,"ONO":292,"NO":315,"NNO":337
    }
    return tabla.get(cardinal.upper(), -1)

def fecha_iso(dia_mes: str) -> str:
    """
    Convierte '05 may' → '2025-05-05' (usa año UTC actual).
    Ajusta año si scrapeas cerca de enero/diciembre y el mes retrocede.
    """
    dia, mes_txt = dia_mes.split()
    mes_num      = MESES.index(mes_txt.lower()) + 1
    año          = datetime.utcnow().year
    return f"{año:04d}-{mes_num:02d}-{int(dia):02d}"

# ────────────────────────── FUNCIÓN PRINCIPAL ────────────────────────────
def extraer_pasos() -> Dict[str, List[dict]]:
    """
    Descarga la tabla de Heavens-Above y devuelve:
        { "YYYY-MM-DD": [ {magnitud, hora_ini, alt_ini, …}, … ] }
    """
    html   = requests.get(URL, headers=HEADERS, timeout=20).content
    soup   = BeautifulSoup(html, "lxml")          # más rápido que html.parser
    tabla  = soup.find("table", class_="standardTable")
    if not tabla:                                 # página cambió o error
        return {}

    agrupados = defaultdict(list)
    for fila in tabla.find_all("tr")[1:]:         # salta cabecera
        c = [td.text.strip() for td in fila.find_all("td")]
        if len(c) < 12:
            continue                              # fila incompleta

        fecha = fecha_iso(c[0])
        paso  = {
            "magnitud" : c[1],
            "hora_ini" : c[2],
            "alt_ini"  : int(c[3][:-1]),         # quita símbolo °
            "ac_ini"   : ac2deg(c[4]),
            "hora_max" : c[5],
            "alt_max"  : int(c[6][:-1]),
            "ac_max"   : ac2deg(c[7]),
            "hora_fin" : c[8],
            "alt_fin"  : int(c[9][:-1]),
            "ac_fin"   : ac2deg(c[10]),
            "tipo"     : c[11]
        }
        agrupados[fecha].append(paso)

    return agrupados

# ────────────────────────── EJECUCIÓN DIRECTA ────────────────────────────
if __name__ == "__main__":
    datos = extraer_pasos()
    hoy   = datetime.utcnow().strftime("%Y-%m-%d")
    with open("iss_hoy.json", "w", encoding="utf-8") as f:
        json.dump(datos.get(hoy, []), f, ensure_ascii=False, indent=2)
    print(f"Archivo 'iss_hoy.json' generado con {len(datos.get(hoy, []))} paso(s).")
