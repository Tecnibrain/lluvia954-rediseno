/* ==========================================================================
   LLUVIA 95.4 FM — Noticias
   Pinta el listado que sirve /api/noticias.php (o el snapshot local en la
   preview). Sin dependencias. Si falla, la sección se oculta en lugar de
   dejar un bloque roto en la página.
   ========================================================================== */
(function () {
  'use strict';

  var contenedor = document.querySelector('[data-noticias]');
  if (!contenedor) return;

  // En producción responde el PHP. Donde no hay PHP (servidor local o la demo
  // de GitHub Pages) se usa el snapshot de tools/generar-snapshot.py, que en
  // Pages mantiene fresco un workflow programado.
  var SIN_PHP = /\.github\.io$/.test(location.hostname);
  var FUENTES = SIN_PHP
    ? ['assets/data/noticias.json']
    : ['api/noticias.php', 'assets/data/noticias.json'];

  var limite = parseInt(contenedor.getAttribute('data-limite'), 10) || 0;
  var estado = document.querySelector('[data-noticias-estado]');
  var sello  = document.querySelector('[data-noticias-actualizado]');
  var filtros = document.querySelectorAll('[data-filtro]');

  var todas = [];
  var categoriaActiva = 'todas';

  /* ---------------------------------------------------------------- utilidades */

  function texto(el, valor) { if (el) el.textContent = valor; }

  function haceCuanto(iso) {
    var d = new Date(iso);
    if (isNaN(d)) return '';
    var seg = Math.floor((Date.now() - d.getTime()) / 1000);
    if (seg < 60)    return 'hace un momento';
    if (seg < 3600)  return 'hace ' + Math.floor(seg / 60) + ' min';
    if (seg < 86400) {
      var h = Math.floor(seg / 3600);
      return 'hace ' + h + (h === 1 ? ' hora' : ' horas');
    }
    var dias = Math.floor(seg / 86400);
    if (dias === 1) return 'ayer';
    if (dias < 7)   return 'hace ' + dias + ' días';
    return d.toLocaleDateString('es-CO', { day: 'numeric', month: 'long', year: 'numeric' });
  }

  function fechaLarga(iso) {
    var d = new Date(iso);
    if (isNaN(d)) return '';
    return d.toLocaleString('es-CO', {
      day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit'
    });
  }

  /* ------------------------------------------------------------------ pintado */

  function tarjeta(n) {
    var art = document.createElement('article');
    art.className = 'noticia';

    var enlace = document.createElement('a');
    enlace.className = 'noticia__enlace';
    enlace.href = n.enlace;
    enlace.target = '_blank';
    enlace.rel = 'noopener noreferrer';
    // El titular es el nombre accesible; se añade la fuente para dar contexto
    enlace.setAttribute('aria-label', n.titulo + ' — leer en ' + n.fuente + ' (abre en una pestaña nueva)');

    if (n.imagen) {
      var media = document.createElement('div');
      media.className = 'noticia__media';
      var img = document.createElement('img');
      img.src = n.imagen;
      img.alt = '';
      img.loading = 'lazy';
      img.decoding = 'async';
      img.referrerPolicy = 'no-referrer';
      // Si el medio bloquea la imagen, se retira el hueco en vez de dejar un roto
      img.addEventListener('error', function () { media.remove(); });
      media.appendChild(img);
      enlace.appendChild(media);
    }

    var cuerpo = document.createElement('div');
    cuerpo.className = 'noticia__cuerpo';

    var chip = document.createElement('span');
    chip.className = 'noticia__chip noticia__chip--' + n.categoria;
    chip.textContent = n.etiqueta;
    cuerpo.appendChild(chip);

    var h3 = document.createElement('h3');
    h3.className = 'noticia__titulo';
    h3.textContent = n.titulo;
    cuerpo.appendChild(h3);

    if (n.extracto) {
      var p = document.createElement('p');
      p.className = 'noticia__extracto';
      p.textContent = n.extracto;
      cuerpo.appendChild(p);
    }

    var pie = document.createElement('p');
    pie.className = 'noticia__pie';
    var fuente = document.createElement('strong');
    fuente.textContent = n.fuente;
    var t = document.createElement('time');
    t.dateTime = n.fecha;
    t.textContent = haceCuanto(n.fecha);
    t.title = fechaLarga(n.fecha);
    pie.appendChild(fuente);
    pie.appendChild(document.createTextNode(' · '));
    pie.appendChild(t);
    cuerpo.appendChild(pie);

    enlace.appendChild(cuerpo);
    art.appendChild(enlace);
    return art;
  }

  function pintar() {
    var lista = categoriaActiva === 'todas'
      ? todas
      : todas.filter(function (n) { return n.categoria === categoriaActiva; });

    if (limite > 0) lista = lista.slice(0, limite);

    contenedor.textContent = '';

    if (!lista.length) {
      texto(estado, 'No hay noticias en esta categoría por ahora.');
      if (estado) estado.hidden = false;
      return;
    }

    if (estado) estado.hidden = true;

    var frag = document.createDocumentFragment();
    lista.forEach(function (n) { frag.appendChild(tarjeta(n)); });
    contenedor.appendChild(frag);
  }

  /* ------------------------------------------------------------------ filtros */

  filtros.forEach(function (btn) {
    btn.addEventListener('click', function () {
      categoriaActiva = btn.getAttribute('data-filtro');
      filtros.forEach(function (o) {
        o.setAttribute('aria-pressed', o === btn ? 'true' : 'false');
      });
      pintar();
    });
  });

  /* ------------------------------------------------------------------- carga */

  function intentar(indice) {
    if (indice >= FUENTES.length) {
      // Sin datos: se retira la sección entera para no dejar un hueco vacío
      var seccion = contenedor.closest('[data-noticias-seccion]');
      if (seccion) seccion.hidden = true;
      else texto(estado, 'No pudimos cargar las noticias en este momento.');
      return;
    }

    fetch(FUENTES[indice], { cache: 'no-store' })
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then(function (datos) {
        if (!datos || !Array.isArray(datos.noticias) || !datos.noticias.length) {
          throw new Error('sin noticias');
        }
        todas = datos.noticias;
        if (sello && datos.actualizado) {
          sello.textContent = 'Actualizado ' + haceCuanto(datos.actualizado);
          sello.setAttribute('datetime', datos.actualizado);
        }
        pintar();
      })
      .catch(function () { intentar(indice + 1); });
  }

  texto(estado, 'Cargando noticias…');
  intentar(0);
})();
