# Rediseño Lluvia 95.4 FM — Preview

Vista previa **independiente** del rediseño de <https://lluvia954.com>.
**No toca producción**: el sitio actual sigue funcionando exactamente igual; nada en el
servidor fue modificado, sustituido ni eliminado.

**▶ Demo en vivo:** _(enlace de GitHub Pages — se añade al publicar)_

> **Sobre la demo publicada.** GitHub Pages solo sirve archivos estáticos, así que ahí no
> se ejecuta `api/noticias.php`: las noticias salen de `assets/data/noticias.json`, que un
> workflow programado refresca cada 6 horas. Los formularios tampoco envían nada en la demo,
> muestran la confirmación y ya. En el servidor real, con PHP, ambas cosas funcionan de verdad.

### Derechos

El logotipo, las fotografías de los estudios y las imágenes de los programas son propiedad de
**CORPOCYNTHIA / Lluvia 95.4 FM** y se incluyen únicamente para esta vista previa: **no están
licenciados para su reutilización.** Los titulares y las imágenes de la sección Noticias
pertenecen a los medios que los publican (El Colombiano, El Tiempo) y se muestran como
titular, extracto y enlace a la fuente original.

---

## Cómo abrir la preview

```bash
python -m http.server 8765 --directory D:/Lluvia/preview
```

Luego abre en el navegador:

| Página | URL |
|---|---|
| **Comparación actual → nuevo** | <http://localhost:8765/comparacion.html> |
| Inicio | <http://localhost:8765/index.html> |
| Noticias | <http://localhost:8765/noticias.html> |
| Nosotros | <http://localhost:8765/nosotros.html> |
| Contacto | <http://localhost:8765/contacto.html> |
| Privacidad | <http://localhost:8765/privacidad.html> |

`comparacion.html` muestra el sitio real y el nuevo lado a lado o con una cortina deslizante,
y permite cambiar entre **escritorio / tablet / móvil**. Para Noticias y Privacidad avisa de
que no existen en el sitio actual.

---

## 1. Análisis del sitio actual

El sitio está generado con **WebSite X5 (Incomedia)**, un constructor visual. Eso explica
casi todo lo que se siente antiguo.

### Identidad detectada (y conservada)

| Elemento | Valor encontrado |
|---|---|
| Azul principal | `rgba(0,32,128)` = **`#002080`** — 109 usos en el CSS |
| Azul oscuro | `rgba(0,16,64)` = **`#001040`** — 13 usos |
| Dorado / amarillo | `rgba(241,194,50)` = **`#F1C232`** — 37 usos |
| Azul claro | `#5EBDEC` |
| Tipografía | **Quicksand** — 106 usos (fallbacks: Arial, Tahoma) |
| Logotipo | `LogoHeaderHD2.png` (color) y `Welcome-LLuvia954.png` (versión blanca) |
| Lema | «La emisora de la gente» |
| Grafismo de marca | `BG-HEAD2.png` — trazos pintados azul/dorado |
| Navegación | INICIO · NOSOTROS · CONTACTO + Fb / Yt / Tw / Ig |

### Qué se veía desactualizado

1. **Maquetación por posición absoluta.** X5 coloca cada bloque en coordenadas fijas, lo que
   deja **enormes zonas vacías** entre secciones y una jerarquía visual plana.
2. **Peso desmedido.** La portada carga **45 recursos y 4,4 MB**.
3. **jQuery + x5engine + modernizr + l10n** para efectos que hoy son CSS puro.
4. **Motor de carrito de compras** (`x5cartengine.js`) en una emisora de radio, que además
   lanza un **error 404** (`cart/x5cart.php`) en cada visita.
5. **Imágenes de programa duplicadas**: se descargan las 10 normales *y* las 10 versiones
   `-OVER` para el hover → 20 PNG en vez de 10.
6. **Imágenes sin comprimir**: `BG-HEAD2.png` 1 MB, `Hifi.jpg` 490 KB, `LLuviaStudios.png` 888 KB.
7. **Reproductor externo Muses** (`hosted.muses.org`) — dependencia de terceros heredada de la
   era Flash, con `autoplay: true`.
8. **Accesibilidad**: todas las imágenes con `alt=""`, menú móvil sin gestión de foco,
   iconos sociales como texto «Fb / Yt / Tw / Ig».
9. **SEO**: sin Open Graph completo, sin datos estructurados, sin `canonical`.
10. `index.php` hace un `<meta refresh>` de 2 segundos hacia `home.html` — una página de
    entrada que solo añade espera.

---

## 2. Qué se conservó

- **Los colores exactos** `#002080`, `#001040` y `#F1C232` como base del sistema.
- **Quicksand** como tipografía única.
- **Los logotipos originales**, sin recortar ni recolorear.
- **El grafismo de trazos pintados** (`BG-HEAD2`) como transición del hero a la sección azul.
- **El lema** «La emisora de la gente».
- **Todos los textos** de Quiénes somos, Misión, Visión, Objetivos y Valores, literales.
- **Los 10 programas** con sus nombres e imágenes reales.
- **Todos los datos de contacto**, teléfonos, correo y dirección.
- **La estructura de navegación** (se añadió «Programación» como ancla, no se quitó nada).

Los tonos se ampliaron a una escala (`--blue-900` … `--blue-50`, `--gold-600` … `--gold-100`)
derivada de esos mismos colores, para poder construir degradados, sombras y estados sin
inventar colores nuevos.

---

## 3. Qué cambió

### Estructura y experiencia
- Cabecera **sticky** translúcida con sombra al hacer scroll.
- **Menú móvil real**: panel lateral, cierre con `Esc`, foco atrapado, bloqueo de scroll.
- Hero con jerarquía clara: logo → identificador en vivo → titular → texto → dos CTA.
- **Reproductor persistente**: barra inferior fija que sigue sonando al cambiar de sección.
- Programación en **cuadrícula responsive** con `alt` correcto en cada programa.
- Nosotros reorganizado en Misión/Visión, Objetivos numerados y Valores.
- Contacto con datos y formulario en dos columnas.
- Pie de página de 4 columnas con mapa del sitio.

### Técnico
- **Sin jQuery, sin x5engine, sin modernizr, sin carrito.** HTML5 + CSS + JS nativo.
- El reproductor Muses se sustituye por un **`<audio>` nativo** contra el mismo stream
  `https://radiolatina.info/8136/stream`, con control de volumen, estado de carga,
  memoria de volumen e integración con los controles del sistema (`mediaSession`).
  **Sin autoplay**: solo suena cuando la persona lo pide.
- Imágenes convertidas a **WebP** y redimensionadas.
- `loading="lazy"` en todo lo que está bajo el pliegue.
- Animaciones solo con CSS + `IntersectionObserver`, con red de seguridad para saltos de scroll.

### Rendimiento medido

| | Sitio actual | Nuevo diseño |
|---|---|---|
| Peticiones (portada) | **45** | **9** |
| Peso total | **4.499 KB** | **306 KB** |
| — HTML | 37,6 KB | 29,9 KB |
| — CSS | 309,8 KB | 32,4 KB |
| — JS | 766,3 KB | 13,4 KB |
| — Imágenes | 3.386 KB | 227 KB (resto en *lazy*) |
| Scripts de terceros | jQuery, x5engine, Muses | ninguno (solo la fuente Quicksand) |
| Errores 404 por visita | 1 | 0 |

**≈93 % menos peso y 80 % menos peticiones.** `domInteractive` 51 ms, `load` 243 ms en local.

Optimización de imágenes: **2.529 KB → 382 KB (−85 %)**, más la foto de estudios
888 KB → 80 KB (−91 %). Los originales se conservan intactos junto a los `.webp`.

### Accesibilidad
- Enlace «saltar al contenido», `:focus-visible` dorado visible en todo elemento interactivo.
- `aria-label`, `aria-expanded`, `aria-pressed`, `aria-current`, `role="status"` donde aplica.
- Jerarquía de encabezados correcta (un solo `h1` por página).
- Contraste verificado: blanco sobre azul **13,8:1**; dorado sobre azul oscuro **8,2:1**.
  El dorado **nunca** se usa como texto sobre blanco (daría 1,7:1) — solo como relleno.
- `prefers-reduced-motion`: desactiva todas las animaciones.
- Áreas táctiles de 44×44 px mínimo.

### SEO
- `title` y `description` únicos y descriptivos por página.
- Open Graph y Twitter Card completos.
- `canonical` apuntando a las URLs reales de producción.
- **JSON-LD `RadioStation`** con frecuencia, dirección, teléfonos, correo y redes.
- HTML semántico (`header`, `nav`, `main`, `section`, `article`, `footer`).

---

## 3bis. Secciones nuevas

### Noticias automáticas con prioridad Colombia

Sección nueva en el inicio (6 titulares) y página propia `noticias.html` (hasta 40, con
filtros por categoría).

**Cómo funciona.** `api/noticias.php` lee canales RSS públicos, los mezcla, elimina
duplicados y los ordena. Guarda el resultado en `api/cache/noticias.json` durante 20 minutos,
así que las fuentes se consultan como mucho 3 veces por hora, sin importar las visitas.

**Prioridad.** No es un orden rígido por bloques: a la fecha de cada noticia se le suma un
“empujón” según la fuente, de modo que Antioquia manda sin tapar una noticia nacional de
última hora.

| Fuente | Canal | Empujón |
|---|---|---|
| El Colombiano | Antioquia | +12 h |
| El Colombiano · El Tiempo | Colombia | +4 h |
| El Colombiano · El Tiempo | Cultura | — |
| El Tiempo | Deportes | — |

Medido sobre la descarga real: **12 de los 20 primeros titulares son de Antioquia**, el resto
nacionales. En total 154 noticias, todas con imagen.

**Qué se publica.** Solo **titular + extracto de 180 caracteres + imagen + enlace al medio**,
que es el uso previsto de un RSS. No se reproduce ningún artículo completo y cada tarjeta
muestra el nombre del medio; al pulsarla se abre el sitio original. La página incluye un
crédito visible a El Colombiano y El Tiempo.

> **Conviene que lo sepas:** aunque este uso es el estándar de cualquier agregador, los
> titulares y las imágenes son propiedad de cada medio. Si quieres quedarte del todo
> tranquilo, basta con escribirles para avisar del uso del RSS. Si algún medio lo pidiera,
> retirar una fuente es borrar una línea del array `$FUENTES`.

**Si un canal falla**, se salta y se sigue con el resto; si fallan todos, se sirve la caché
anterior aunque esté vencida, y si tampoco la hay, la sección se oculta sola en lugar de
dejar un hueco roto.

**Para añadir o quitar fuentes:** edita el array `$FUENTES` en `api/noticias.php` (y el mismo
listado en `tools/generar-snapshot.py` si quieres regenerar el snapshot de la preview).

**En la preview** no hay PHP, así que el JavaScript cae automáticamente a
`assets/data/noticias.json`, un volcado real generado con:

```bash
python tools/generar-snapshot.py
```

### Aviso de cookies

Banner propio, sin librerías externas, con dos opciones reales: **Aceptar todas** y
**Solo las necesarias**. La decisión se guarda en el navegador y el aviso no vuelve a
aparecer; se puede revisar desde **Configurar cookies** en el pie o en la página de privacidad.

No es un botón decorativo como el actual: el consentimiento se puede consultar con
`window.lluviaCookies.estado()` y dispara el evento `lluvia:consentimiento`. Hoy el sitio
**no usa analítica**, así que no hay nada que bloquear; si mañana se añade Google Analytics o
similar, debe engancharse a ese evento para que solo cargue tras el «Aceptar».

### Página de privacidad

`privacidad.html`, redactada según la Ley 1581 de 2012 y el Decreto 1377 de 2013, con el
responsable (CORPOCYNTHIA, NIT, domicilio), qué datos se recogen en cada formulario, para qué
se usan, qué cookies hay, qué terceros intervienen (Google Fonts, radiolatina.info, El
Colombiano, El Tiempo, WhatsApp), plazos de conservación y los derechos del titular con los
plazos legales de respuesta.

> **Lleva un aviso visible en la propia página**: el texto describe con exactitud cómo
> funciona el sitio, pero **no soy abogado**. Debe revisarlo y aprobarlo el representante
> legal de CORPOCYNTHIA antes de publicarse.

---

## 4. Funcionalidades: inventario

### Conservadas sin cambios
- Señal en vivo (mismo stream).
- Enlace a Radio Garden.
- «¡Pide tu canción!» → WhatsApp `573246420773` con el mismo mensaje.
- Formulario de contacto: **mismo `action`** (`imemail/imEmailForm.php`) y **mismos `name`**
  (`imObjectForm_13_1/2/3` + `imSpProt`), para que el envío siga funcionando igual.
- Formulario de pauta: **mismo `action`** (`imemail/imEmailForm_eqicq8xk.php`) y mismos `name`
  (`imObjectForm_35_1/2` + `imSpProt`).
- Los 4 enlaces a redes sociales.
- Botón «volver arriba».

### Mejoradas
- Validación de formularios con mensajes en español y foco al primer error.
- Reproductor con volumen persistente y sin autoplay.

### Retiradas — requieren tu visto bueno
| Elemento | Motivo |
|---|---|
| Motor de carrito `x5cartengine.js` | No hay tienda; genera un 404 en cada visita |
| Página de entrada `index.php` con `meta refresh` | Añade 2 s de espera; el nuevo `index.html` es ya la portada |
| Banner de cookies actual | Sustituido por uno con consentimiento real (aceptar / solo necesarias) y página de privacidad |
| Imágenes-banner `01-QS`, `02-MV`, `03-O`, `04-V` | Eran títulos en imagen (uno en verde, fuera de marca). El texto ahora es HTML real: mejor SEO y accesibilidad |
| Imágenes `-OVER` de los programas | El hover ahora es CSS; no requiere una segunda imagen |

**Nada de esto se ha borrado del servidor.** Solo no se usa en la preview.

---

## 5. Pendiente de tus datos

1. **Horarios de la programación.** El sitio actual no publica horas, así que las tarjetas
   muestran solo nombre y género. Si me pasas la parrilla, la añado.
2. **Revisión legal de `privacidad.html`** por parte del representante legal de CORPOCYNTHIA.
3. **¿Van a usar analítica?** Hoy el sitio no mide nada. Si quieren estadísticas de visitas,
   dímelo y lo conecto al consentimiento ya implementado.
4. **Fuentes de noticias.** ¿Te sirven El Colombiano y El Tiempo, o prefieres añadir medios
   locales de Caldas o del sur del Valle de Aburrá? Si me pasas las URLs, compruebo sus RSS.
5. **Twitter/X.** El sitio enlaza a `twitter.com/lluvia954fm`; confirmar si la cuenta sigue activa.
6. **Descripción de los estudios** en la página Nosotros: redacté un texto a partir de la
   dirección real; revísalo por si prefieres otra redacción.

---

## 6. Estructura de archivos

```
D:\Lluvia\preview\
├── index.html          Portada
├── noticias.html       Noticias con filtros por categoría
├── nosotros.html       Quiénes somos, misión, visión, objetivos, valores, pauta
├── contacto.html       Datos de contacto y formulario
├── privacidad.html     Política de privacidad y cookies
├── comparacion.html    Herramienta de comparación (no forma parte del sitio)
├── README.md           Este documento
├── api\
│   ├── noticias.php    Agregador RSS con caché (se ejecuta en el servidor)
│   └── cache\          Se crea solo; debe ser escribible
├── tools\
│   └── generar-snapshot.py   Regenera el volcado de noticias de la preview
└── assets\
    ├── css\style.css       Sistema de diseño completo (~39 KB, un solo archivo)
    ├── js\main.js          Cabecera, menú, reproductor, animaciones, formularios, cookies (~16 KB)
    ├── js\noticias.js      Pintado del listado de noticias (~6 KB)
    ├── data\noticias.json  Volcado para la preview; en producción no se usa
    └── img\                Activos de marca: originales + versiones .webp optimizadas
```

Sin build, sin npm, sin framework: se sube por FTP tal cual. Lo único que necesita el
servidor es PHP (que ya tienen, por los formularios) y permiso de escritura en `api/cache/`.

Los enlaces a CSS y JS llevan `?v=…`. Al subir un cambio, sube ese número en las cinco
páginas y todos los visitantes reciben la versión nueva sin tener que vaciar la caché.

---

## 7. Segunda etapa — paso a producción

**No ejecutada.** Pendiente de tu aprobación explícita. Cuando la des, el plan sería:

1. Copia de seguridad completa del sitio actual (archivos + `imemail/`).
2. Publicar la preview en una subcarpeta o subdominio de pruebas (`/nuevo` o `beta.lluvia954.com`).
3. Verificar allí el envío real de los dos formularios PHP y el stream sobre HTTPS.
4. Comprobar `api/noticias.php` en el servidor: que exista `api/cache/` con permiso de
   escritura (755) y que el hosting permita salida HTTP hacia los medios. Si la carpeta no
   fuera escribible funciona igual, pero consultaría los RSS en cada visita.
5. Revisión legal de `privacidad.html` y decisión sobre analítica.
6. Definir redirecciones 301: `index.php` → `/`, `acerca-de.html` → `nosotros.html`.
7. Mantener las URLs `contacto.html` y `acerca-de.html` o redirigirlas, para no perder SEO.
8. Publicar en raíz, conservando `imemail/`, `favicon.ico` y la carpeta `images/`.
9. Revisar Search Console y comprobar que no queden 404.
