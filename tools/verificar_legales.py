# -*- coding: utf-8 -*-
"""Comprueba linea a linea que la conversion no perdio ni altero texto.

Hace su propia extraccion, sin reutilizar la del conversor: si el conversor
tuviera un fallo, reutilizar su codigo lo ocultaria.

Compara la lista de lineas que un navegador mostraria en el documento
original con la lista de bloques de texto de la pagina generada.

    python -X utf8 -I verificar_legales.py <origen> <nuevo>
"""
import io
import os
import re
import sys

from lxml import html as LH

ORIGEN, NUEVO = sys.argv[1], sys.argv[2]
ARCHIVOS = ["politica-de-tratamiento-de-datos.html", "aviso-privacidad.html"]
BLOQUES = ("p", "h2", "h3", "li")


def norm(t):
    t = (t or "").replace(" ", " ").replace("•", " ")
    return re.sub(r"\s+", " ", t).strip()


def lineas_originales(ruta):
    """Lo que el navegador muestra como lineas en el documento viejo."""
    doc = LH.parse(ruta, parser=LH.HTMLParser(encoding="utf-8"))
    cont = doc.getroot().get_element_by_id("imContent")
    mejor, n_mejor = None, 0
    for el in cont.iter("div"):
        i = el.get("id") or ""
        if "TextObject" in i and i.endswith("tab0"):
            n = len(el.text_content() or "")
            if n > n_mejor:
                mejor, n_mejor = el, n
    # las lineas son los div mas profundos que contienen texto directo
    lineas = []
    for d in mejor.iter("div"):
        if len(d) == 0 or all(c.tag == "br" for c in d):
            t = norm(d.text_content())
            if t:
                lineas.append(t)
    return lineas


def lineas_nuevas(ruta):
    doc = LH.parse(ruta, parser=LH.HTMLParser(encoding="utf-8"))
    raiz = doc.getroot()
    art = None
    for a in raiz.iter("article"):
        if "prosa" in (a.get("class") or ""):
            art = a
            break
    lineas, saltar = [], False
    for el in art.iter(*BLOQUES):
        t = norm(el.text_content())
        if el.tag == "h2" and t == "Documentos relacionados":
            saltar = True
        if saltar or not t:
            continue
        lineas.append(t)
    return lineas


fallo = False
for f in ARCHIVOS:
    a = lineas_originales(os.path.join(ORIGEN, f))
    b = lineas_nuevas(os.path.join(NUEVO, f))

    # la primera linea del original es el titulo del documento: pasa al <h1>,
    # asi que no debe aparecer en el cuerpo
    titulo = a[0]
    cuerpo = a[1:]

    ok = cuerpo == b
    print("%-40s lineas original=%-4d nuevo=%-4d  %s"
          % (f, len(cuerpo), len(b), "IDENTICO" if ok else "*** DIFERENCIAS ***"))
    print("    titulo del documento: %r" % titulo)

    if not ok:
        fallo = True
        n = min(len(cuerpo), len(b))
        mostradas = 0
        for i in range(n):
            if cuerpo[i] != b[i]:
                print("    linea %d" % i)
                print("      viejo: %s" % cuerpo[i][:130])
                print("      nuevo: %s" % b[i][:130])
                mostradas += 1
                if mostradas >= 10:
                    print("      ...")
                    break
        if len(cuerpo) != len(b):
            print("    sobran/faltan lineas: %d vs %d" % (len(cuerpo), len(b)))
            for x in cuerpo[n:n + 5]:
                print("      solo en el viejo: %s" % x[:120])
            for x in b[n:n + 5]:
                print("      solo en el nuevo: %s" % x[:120])

    # ningun caracter perdido, al margen de como se hayan repartido las lineas
    ca, cb = norm(" ".join(cuerpo)), norm(" ".join(b))
    print("    caracteres: viejo=%d nuevo=%d  %s"
          % (len(ca), len(cb), "coinciden" if ca == cb else "NO COINCIDEN"))
    if ca != cb:
        fallo = True

sys.exit(1 if fallo else 0)
