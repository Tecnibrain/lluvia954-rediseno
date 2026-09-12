"""
Genera assets/data/noticias.json a partir de los mismos canales RSS que usa
api/noticias.php, con idéntica lógica de prioridad.

Sirve para que la preview local (sin PHP) muestre noticias reales.
En producción no hace falta: allí responde el PHP.

    python tools/generar-snapshot.py
"""

import json
import os
import re
import ssl
import sys
import urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from xml.etree import ElementTree

EXTRACTO = 180
TIMEOUT = 12

FUENTES = [
    ("https://www.elcolombiano.com/rss/antioquia.xml", "El Colombiano", "antioquia", "Antioquia", 43200),
    ("https://www.elcolombiano.com/rss/colombia.xml",  "El Colombiano", "colombia",  "Colombia",  14400),
    ("https://www.eltiempo.com/rss/colombia.xml",      "El Tiempo",     "colombia",  "Colombia",  14400),
    ("https://www.elcolombiano.com/rss/cultura.xml",   "El Colombiano", "cultura",   "Cultura",       0),
    ("https://www.eltiempo.com/rss/cultura.xml",       "El Tiempo",     "cultura",   "Cultura",       0),
    ("https://www.eltiempo.com/rss/deportes.xml",      "El Tiempo",     "deportes",  "Deportes",      0),
]

MEDIA_NS = "{http://search.yahoo.com/mrss/}"
DC_NS = "{http://purl.org/dc/elements/1.1/}"


def descargar(url):
    req = urllib.request.Request(url, headers={"User-Agent": "LluviaBot/1.0 (+https://lluvia954.com)"})
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as r:
        return r.read().decode("utf-8", "replace")


def limpiar(texto):
    texto = unescape(texto or "")
    texto = re.sub(r"<[^>]+>", " ", texto)
    texto = unescape(texto)
    return re.sub(r"\s+", " ", texto).strip()


def extracto(html):
    texto = limpiar(html)
    if len(texto) <= EXTRACTO:
        return texto
    corte = texto[:EXTRACTO]
    esp = corte.rfind(" ")
    if esp > 60:
        corte = corte[:esp]
    return corte.rstrip(" ,;:.-") + "…"


def imagen(item, descripcion):
    enc = item.find("enclosure")
    if enc is not None and enc.get("url"):
        return enc.get("url")
    for tag in ("content", "thumbnail"):
        el = item.find(MEDIA_NS + tag)
        if el is not None and el.get("url"):
            return el.get("url")
    m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', unescape(descripcion or ""), re.I)
    return m.group(1) if m else ""


def fecha(item):
    bruta = (item.findtext("pubDate") or item.findtext(DC_NS + "date") or "").strip()
    if not bruta:
        return datetime.now(timezone.utc)
    try:
        d = parsedate_to_datetime(bruta)
    except (TypeError, ValueError):
        try:
            d = datetime.fromisoformat(bruta.replace("Z", "+00:00"))
        except ValueError:
            return datetime.now(timezone.utc)
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d


def main():
    noticias, vistos, fallos = [], set(), []

    for url, fuente, categoria, etiqueta, boost in FUENTES:
        try:
            xml = descargar(url)
            raiz = ElementTree.fromstring(xml)
        except Exception as e:                                  # noqa: BLE001
            fallos.append(f"{url} -> {type(e).__name__}")
            continue

        for item in raiz.iter("item"):
            enlace = (item.findtext("link") or "").strip()
            titulo = limpiar(item.findtext("title") or "")
            if not enlace or not titulo:
                continue
            clave = enlace.lower()
            if clave in vistos:
                continue
            vistos.add(clave)

            descripcion = item.findtext("description") or ""
            d = fecha(item)
            noticias.append({
                "titulo": titulo,
                "extracto": extracto(descripcion),
                "enlace": enlace,
                "imagen": imagen(item, descripcion),
                "fuente": fuente,
                "categoria": categoria,
                "etiqueta": etiqueta,
                "fecha": d.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
                "_orden": d.timestamp() + boost,
            })

    noticias.sort(key=lambda n: n["_orden"], reverse=True)
    for n in noticias:
        del n["_orden"]

    if not noticias:
        print("Sin noticias: no se escribe el archivo.", file=sys.stderr)
        for f in fallos:
            print("  fallo:", f, file=sys.stderr)
        return 1

    destino = os.path.join(os.path.dirname(__file__), "..", "assets", "data", "noticias.json")
    destino = os.path.normpath(destino)
    os.makedirs(os.path.dirname(destino), exist_ok=True)

    salida = {
        "actualizado": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "total": len(noticias),
        "noticias": noticias,
    }
    with open(destino, "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=1)

    porcat = {}
    for n in noticias:
        porcat[n["categoria"]] = porcat.get(n["categoria"], 0) + 1

    print(f"{len(noticias)} noticias -> {destino}")
    print("  por categoría:", porcat)
    print(f"  con imagen: {sum(1 for n in noticias if n['imagen'])}")
    for f in fallos:
        print("  fallo:", f)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
