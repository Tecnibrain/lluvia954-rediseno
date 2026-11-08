# -*- coding: utf-8 -*-
"""Pasa las paginas legales del X5 antiguo a la plantilla del sitio nuevo.

El texto legal no se reescribe: se extrae tal cual del original y solo se
envuelve en etiquetas semanticas. Las unicas decisiones de estructura son
las inequivocas: lineas numeradas -> titulo, lineas con vineta -> lista.

    python -X utf8 -I convertir_legales.py <origen> <plantilla> <destino> [--escribir]
"""
import html as H
import io
import os
import re
import sys

from lxml import html as LH

ORIGEN = sys.argv[1]       # carpeta con los html descargados del sitio viejo
PLANTILLA = sys.argv[2]    # privacidad.html del sitio nuevo
DESTINO = sys.argv[3]      # carpeta donde escribir
SECO = "--escribir" not in sys.argv

PAGINAS = [
    {
        "archivo": "politica-de-tratamiento-de-datos.html",
        "titulo": "Política de tratamiento de datos",
        "miga": "Tratamiento de datos",
        "lead": "Manual interno de CORPOCYNTHIA para el tratamiento de los datos "
                "personales contenidos en sus bases de datos.",
        "desc": "Política de tratamiento de datos personales de CORPOCYNTHIA "
                "(Lluvia 95.4 FM), adoptada conforme a la Ley 1581 de 2012 y el "
                "Decreto 1377 de 2013.",
    },
    {
        "archivo": "aviso-privacidad.html",
        "titulo": "Aviso de privacidad",
        "miga": "Aviso de privacidad",
        "lead": "Información que CORPOCYNTHIA entrega al titular sobre el "
                "tratamiento al que serán sometidos sus datos personales.",
        "desc": "Aviso de privacidad de CORPOCYNTHIA (Lluvia 95.4 FM), en "
                "cumplimiento de la Ley Estatutaria 1581 de 2012.",
    },
]

# Enlaces entre documentos legales: cumplen la funcion de los tres botones
# que tenia el sitio viejo en la cabecera de estas paginas.
RELACIONADOS = [
    ("privacidad.html", "Privacidad y cookies de este sitio"),
    ("politica-de-tratamiento-de-datos.html", "Política de tratamiento de datos"),
    ("aviso-privacidad.html", "Aviso de privacidad"),
]

VINETA = "•"


def bloques(ruta):
    """Lineas de texto del documento, en orden y sin perder ninguna."""
    doc = LH.parse(ruta, parser=LH.HTMLParser(encoding="utf-8"))
    cont = doc.getroot().get_element_by_id("imContent")

    mejor, mejor_n = None, 0
    for el in cont.iter("div"):
        ident = el.get("id") or ""
        if "TextObject" in ident and ident.endswith("tab0"):
            n = len(el.text_content() or "")
            if n > mejor_n:
                mejor, mejor_n = el, n

    just = mejor.find('.//div[@class="imTAJustify"]')
    if just is None:
        just = mejor.find('.//div[@class="text-inner"]')[0]

    # Segun la pagina, las lineas cuelgan de imTAJustify o de un div intermedio.
    # Se desciende mientras solo haya un hijo que a su vez agrupe varias lineas.
    while len(just) == 1 and just[0].tag == "div" and len(just[0]) > 1:
        just = just[0]

    salida = []
    for d in just:
        t = (d.text_content() or "").replace(" ", " ")
        t = re.sub(r"\s+", " ", t).strip()
        if t:
            salida.append(t)
    return salida


def prosa(lineas):
    """Envuelve las lineas en HTML semantico. Devuelve (html, estadisticas)."""
    partes, lista = [], []
    est = {"h2": 0, "h3": 0, "li": 0, "p": 0}

    def cerrar():
        if lista:
            partes.append('        <ul class="lista">')
            partes.extend("          <li>%s</li>" % x for x in lista)
            partes.append("        </ul>")
            del lista[:]

    for t in lineas:
        if t.startswith(VINETA):
            lista.append(H.escape(t.lstrip(VINETA + " ").strip()))
            est["li"] += 1
            continue
        cerrar()
        # El prefijo se conserva literal, con su punto final o sin el, tal como
        # venga en el original: "4.1 Introduccion" y "4.2. Normatividad" conviven.
        m = re.match(r"^((?:\d+\.)*\d+\.?)\s+(\S.*)$", t)
        if m and len(t) < 90:
            prefijo = m.group(1)
            nivel = "h2" if len(re.findall(r"\d+", prefijo)) == 1 else "h3"
            partes.append("        <%s>%s %s</%s>"
                          % (nivel, H.escape(prefijo), H.escape(m.group(2)), nivel))
            est[nivel] += 1
        else:
            partes.append("        <p>%s</p>" % H.escape(t))
            est["p"] += 1
    cerrar()
    return "\n".join(partes), est


def construir(plantilla, pg, cuerpo):
    """Clona privacidad.html cambiando metadatos, encabezado y contenido."""
    s = plantilla

    def rep(viejo, nuevo):
        if s.count(viejo) != 1:
            raise AssertionError("plantilla: %r aparece %d veces"
                                 % (viejo[:60], s.count(viejo)))
        return s.replace(viejo, nuevo)

    base = "https://lluvia954.com/" + pg["archivo"]
    s = rep("<title>Privacidad y tratamiento de datos — Lluvia 95.4 FM</title>",
            "<title>%s — Lluvia 95.4 FM</title>" % pg["titulo"])
    s = rep('<meta name="description" content="Política de privacidad, tratamiento de datos '
            'personales y uso de cookies de Lluvia 95.4 FM (Corpocynthia), conforme a la Ley '
            '1581 de 2012.">',
            '<meta name="description" content="%s">' % pg["desc"])
    s = rep('<link rel="canonical" href="https://lluvia954.com/privacidad.html">',
            '<link rel="canonical" href="%s">' % base)
    s = rep('<meta property="og:title" content="Privacidad — Lluvia 95.4 FM">',
            '<meta property="og:title" content="%s — Lluvia 95.4 FM">' % pg["titulo"])
    s = rep('<meta property="og:description" content="Política de privacidad y tratamiento '
            'de datos personales.">',
            '<meta property="og:description" content="%s">' % pg["lead"])
    s = rep('<meta property="og:url" content="https://lluvia954.com/privacidad.html">',
            '<meta property="og:url" content="%s">' % base)
    s = rep("<span>Privacidad</span>", "<span>%s</span>" % pg["miga"])
    s = rep("<h1>Privacidad y tratamiento de datos</h1>", "<h1>%s</h1>" % pg["titulo"])
    s = rep("<p>Cómo tratamos tus datos personales y qué cookies usa este sitio.</p>",
            "<p>%s</p>" % pg["lead"])

    # Si la plantilla aun lleva el aviso de validacion juridica, no se replica.
    # Se retiro de privacidad.html el 7-11-2026, asi que puede no estar.
    a = s.find('      <div class="aviso-legal reveal">')
    if a != -1:
        b = s.index("</div>", s.index("antes de publicarse.")) + len("</div>")
        s = s[:a] + s[b:].lstrip("\n")

    # Sustituir el interior del articulo por el documento convertido.
    ini = s.index('<article class="prosa reveal" data-delay="1">')
    ini = s.index("\n", ini) + 1
    fin = s.index("      </article>")
    s = s[:ini] + cuerpo + "\n" + s[fin:]

    # Sin animacion de entrada: estos documentos miden miles de pixeles y el
    # observador exige que se vea el 8% del elemento, cosa imposible en un
    # viewport normal. Quedarian invisibles hasta que el visitante se desplace.
    return rep('<article class="prosa reveal" data-delay="1">', '<article class="prosa">')


def main():
    plantilla = io.open(PLANTILLA, encoding="utf-8").read()
    for pg in PAGINAS:
        lineas = bloques(os.path.join(ORIGEN, pg["archivo"]))

        # La primera linea es el titulo del documento en mayusculas; pasa al h1.
        primera = lineas[0]
        quitar_primera = primera.upper() == primera and len(primera) < 70
        cuerpo_lineas = lineas[1:] if quitar_primera else lineas

        cuerpo, est = prosa(cuerpo_lineas)

        rel = [r for r in RELACIONADOS if r[0] != pg["archivo"]]
        cuerpo += ("\n        <h2>Documentos relacionados</h2>\n"
                   '        <ul class="lista">\n'
                   + "\n".join('          <li><a href="%s">%s</a></li>' % r for r in rel)
                   + "\n        </ul>")

        salida = construir(plantilla, pg, cuerpo)
        texto = sum(len(l) for l in cuerpo_lineas)
        print("%-40s lineas=%-4d h2=%-3d h3=%-3d li=%-3d p=%-3d texto=%-6d html=%d B"
              % (pg["archivo"], len(cuerpo_lineas), est["h2"], est["h3"],
                 est["li"], est["p"], texto, len(salida.encode("utf-8"))))
        print("    titulo retirado del cuerpo: %s" % (primera if quitar_primera else "(ninguno)"))

        if not SECO:
            destino = os.path.join(DESTINO, pg["archivo"])
            io.open(destino, "w", encoding="utf-8", newline="\n").write(salida)

    print("(simulacion: no se escribio nada)" if SECO else "(archivos escritos)")



if __name__ == "__main__":
    main()
