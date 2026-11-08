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

# Cupos reservados a Antioquia: (hasta_posición, mínimo). Mismos valores y
# misma lógica que CUPOS_ANTIOQUIA en api/noticias.php; si se cambian aquí,
# hay que cambiarlos allí.
CUPOS_ANTIOQUIA = [(8, 4), (20, 8)]
HORAS_FRESCURA_CUPO = 48

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


def aplicar_cupos(noticias, cupos, frescura):
    """Reserva sitio a Antioquia arriba. Espejo de aplicarCupos() en el PHP.

    Toma siempre la mejor noticia disponible del orden ya calculado y solo
    fuerza una regional cuando, de no hacerlo, el cupo ya no cabría en las
    posiciones libres que quedan.
    """
    total = len(noticias)
    if not total or not cupos:
        return noticias

    ultima = max(c[0] for c in cupos)
    usado, salida = set(), []
    regional = 0   # noticias de Antioquia ya colocadas
    cursor = 0     # primera posición sin usar del orden general

    for pos in range(1, total + 1):
        forzar = False
        if pos <= ultima:
            for hasta, minimo in cupos:
                if pos > hasta:
                    continue
                faltan = minimo - regional
                huecos = hasta - pos + 1
                if faltan > 0 and faltan >= huecos:
                    forzar = True
                    break

        elegido = -1
        if forzar:
            for j in range(cursor, total):
                if j in usado:
                    continue
                if noticias[j]["categoria"] == "antioquia" and noticias[j]["_ts"] >= frescura:
                    elegido = j
                    break

        if elegido < 0:
            while cursor < total and cursor in usado:
                cursor += 1
            if cursor >= total:
                break
            elegido = cursor

        usado.add(elegido)
        if noticias[elegido]["categoria"] == "antioquia":
            regional += 1
        salida.append(noticias[elegido])

    return salida


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
                "_ts": d.timestamp(),
            })

    noticias.sort(key=lambda n: n["_orden"], reverse=True)

    frescura = datetime.now(timezone.utc).timestamp() - HORAS_FRESCURA_CUPO * 3600
    noticias = aplicar_cupos(noticias, CUPOS_ANTIOQUIA, frescura)

    for n in noticias:
        del n["_orden"], n["_ts"]

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

    def reg(k):
        return sum(1 for n in noticias[:k] if n["categoria"] == "antioquia")

    print(f"{len(noticias)} noticias -> {destino}")
    print("  por categoría:", porcat)
    print(f"  cupos Antioquia: {reg(8)}/8 en las 8 primeras (min 4), "
          f"{reg(20)}/20 en las 20 primeras (min 8)")
    print(f"  con imagen: {sum(1 for n in noticias if n['imagen'])}")
    for f in fallos:
        print("  fallo:", f)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
