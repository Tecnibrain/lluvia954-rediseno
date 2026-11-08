# Paso a producción — cPanel (Colombia Hosting)

> ## Ejecutado el 7 de noviembre de 2026
>
> El rediseño **ya está en producción** en `https://lluvia954.com`.
> Lo que sigue se conserva como referencia de lo que se hizo.
>
> | | |
> |---|---|
> | **Respaldo previo** | `/home/lluvia/respaldo-sitio-2026-11-07.zip` (6,9 MB, fuera de `public_html`) |
> | **Interruptor** | `index.php` renombrado a `index.php.anterior` |
> | **Vuelta atrás** | Renombrar `index.php.anterior` de vuelta a `index.php`. Las redirecciones del `.htaccess` llevan una condición y se desactivan solas |
> | **Sitio anterior** | Intacto en `home.html`, `acerca-de.html`, `style/`, `res/`, `pcss/`, `pluginAppObj/` |
>
> También se corrigieron 27 archivos que habían quedado con permisos `0666` al
> descomprimir, y se reescribieron `sitemap.xml` y `robots.txt` con las URL nuevas.


Guía para publicar el rediseño en `lluvia954.com`.
Va en dos tiempos: **primero una carpeta de pruebas**, y solo cuando todo funcione, la raíz.

El paquete listo para subir es **`lluvia954-produccion.zip`** (657 KB).

---

## Antes de empezar

### 1. Copia de seguridad (no te la saltes)

En cPanel → **Archivos → Copias de seguridad → Descargar una copia de seguridad del
directorio principal**. Espera a que termine y guarda el archivo en tu computador.

Es la red de seguridad: si algo sale mal, se restaura y el sitio vuelve como estaba.

### 2. Comprueba la versión de PHP

cPanel → **Software → Seleccionar versión de PHP**.

El agregador de noticias necesita **PHP 7.0 o superior**; lo ideal es **8.1 o 8.2**.
Si aparece 5.6, súbela — pero ojo: el sitio actual también correría con la versión nueva,
así que haz el cambio y revisa enseguida que los formularios actuales sigan enviando.

Deben estar activadas las extensiones **curl** y **simplexml** (vienen por defecto).

---

## Etapa 1 — Carpeta de pruebas

El sitio actual sigue intacto durante toda esta etapa.

1. cPanel → **Archivos → Administrador de archivos**.
2. Entra en **`public_html`**.
3. Botón **+ Carpeta** → créala con el nombre **`nuevo`**.
4. Entra en `public_html/nuevo`.
5. Botón **Cargar** (Upload) → sube **`lluvia954-produccion.zip`**.
6. Vuelve al administrador, clic derecho sobre el ZIP → **Extract / Extraer**.
7. Borra el ZIP del servidor una vez extraído.

Ya puedes abrir **`https://lluvia954.com/nuevo/`**.

### Qué revisar ahí

| Revisar | Cómo |
|---|---|
| Las 5 páginas cargan | Inicio, Noticias, Nosotros, Contacto, Privacidad |
| **Reproductor en vivo** | Pulsa «Escuchar en vivo». Debe sonar y aparecer la barra inferior |
| **Noticias** | Deben cargarse y el sello decir «Actualizado hace unos minutos» |
| **Formulario de contacto** | Envía una prueba. **Llegará a tu correo real** |
| **Formulario de pauta** | En Nosotros, abajo. Envía otra prueba |
| Aviso de cookies | Aparece, se acepta y no vuelve a salir |
| Móvil | Ábrelo desde el celular |
| Comparación | `https://lluvia954.com/nuevo/comparacion.html` |

### Si las noticias no cargan

Es lo único que depende del servidor. Abre directamente:

```
https://lluvia954.com/nuevo/api/noticias.php
```

- **Sale texto JSON** → funciona; el problema está en otra parte.
- **Se descarga el archivo o se ve el código PHP** → PHP no está procesando esa carpeta.
- **Error 500** → revisa la versión de PHP (punto 2).
- **`{"total":0,...}`** → el hosting bloquea las conexiones salientes. Avísame y lo
  resolvemos; mientras tanto el sitio usa el respaldo de `assets/data/noticias.json`.

La carpeta `api/cache/` se crea sola. Si da error de escritura, dale permisos **755**
desde el administrador de archivos.

---

## Etapa 2 — Pasar a la raíz

**Solo cuando todo lo anterior esté verificado.**

### Qué NO se debe tocar en `public_html`

| Carpeta / archivo | Por qué |
|---|---|
| **`imemail/`** | Los dos formularios envían a este PHP. Si se borra, dejan de funcionar |
| `images/` | Las etiquetas Open Graph apuntan a `lluvia954.com/images/LogoHeaderHD2.png` |
| `cgi-bin/`, `.well-known/` | Del servidor y los certificados |
| `.htaccess` | Si existe, consérvalo y añádele las redirecciones de abajo |

### Pasos

1. En `public_html/nuevo`, borra **`comparacion.html`**: es una herramienta de revisión,
   no parte del sitio.
2. Mueve el contenido de `public_html/nuevo/` a `public_html/` (Seleccionar todo → Mover).
3. Los archivos viejos del sitio anterior (`home.html`, `acerca-de.html`, `index.php`,
   `style/`, `res/`, `pcss/`, `pluginAppObj/`) **no los borres todavía**: déjalos una o dos
   semanas por si hay que volver atrás. Solo `index.php` debe salir o renombrarse, porque
   compite con el nuevo `index.html`.
4. Borra la carpeta `nuevo` vacía.

### Redirecciones

Para no perder el posicionamiento, añade esto al `.htaccess` de `public_html`.
Las URLs viejas están indexadas en Google y deben llevar a las nuevas:

```apache
# Redirecciones del rediseño 2026
Redirect 301 /home.html       /
Redirect 301 /index.php       /
Redirect 301 /acerca-de.html  /nosotros.html
```

`contacto.html` conserva el mismo nombre, así que no necesita redirección.

---

## Después de publicar

1. Abre el sitio en una ventana de incógnito y repasa las cinco páginas.
2. Envía una última prueba por cada formulario.
3. En **Google Search Console**, pide la reindexación de la página principal.
4. A los pocos días, revisa en Search Console que no aparezcan errores 404.

---

## Actualizaciones futuras

Los enlaces a CSS y JS llevan `?v=20260912d`. Cuando cambies uno de esos archivos,
sube ese número en las cinco páginas: así los visitantes reciben la versión nueva sin
tener que vaciar la caché del navegador.

### Alternativa: desplegar desde GitHub

cPanel trae **Archivos → Git™ Version Control**. Como el repositorio es público, se puede
clonar sin claves:

- URL: `https://github.com/Tecnibrain/lluvia954-rediseno.git`
- Después, cada cambio se actualiza con el botón **Pull** en vez de volver a subir archivos.

Requiere un archivo `.cpanel.yml` para definir qué se copia a `public_html`. Si prefieres
este camino, dímelo y lo preparo.

---

## Si algo sale mal

Restaura la copia de seguridad del primer paso: cPanel → **Copias de seguridad →
Restaurar**. El sitio vuelve exactamente a como estaba.
