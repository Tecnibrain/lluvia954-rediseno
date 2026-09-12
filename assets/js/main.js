/* ==========================================================================
   LLUVIA 95.4 FM — Scripts del rediseño
   Sin dependencias externas. ES2019+. Mejora progresiva:
   la página es completamente legible y navegable si este archivo no carga.
   ========================================================================== */
(function () {
  'use strict';

  var STREAM_URL = 'https://radiolatina.info/8136/stream';
  var STATION = 'Lluvia 95.4 FM';
  var $  = function (sel, ctx) { return (ctx || document).querySelector(sel); };
  var $$ = function (sel, ctx) { return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); };

  /* ------------------------------------------------------------------
     1. Cabecera: sombra al hacer scroll
     ------------------------------------------------------------------ */
  function initHeader() {
    var header = $('.site-header');
    if (!header) return;
    var onScroll = function () {
      header.classList.toggle('is-stuck', window.scrollY > 8);
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  /* ------------------------------------------------------------------
     2. Navegación móvil (accesible: ESC, foco atrapado, aria-expanded)
     ------------------------------------------------------------------ */
  function initMobileNav() {
    var nav = $('.mobile-nav');
    var burger = $('.burger');
    if (!nav || !burger) return;

    var panel = $('.mobile-nav__panel', nav);
    var lastFocused = null;

    function focusables() {
      return $$('a[href], button:not([disabled])', panel)
        .filter(function (el) { return el.offsetParent !== null; });
    }

    function open() {
      lastFocused = document.activeElement;
      nav.classList.add('is-open');
      document.body.classList.add('nav-open');
      burger.setAttribute('aria-expanded', 'true');
      nav.removeAttribute('aria-hidden');
      var f = focusables();
      if (f.length) f[0].focus();
      document.addEventListener('keydown', onKeydown);
    }

    function close() {
      nav.classList.remove('is-open');
      document.body.classList.remove('nav-open');
      burger.setAttribute('aria-expanded', 'false');
      nav.setAttribute('aria-hidden', 'true');
      document.removeEventListener('keydown', onKeydown);
      if (lastFocused) lastFocused.focus();
    }

    function onKeydown(e) {
      if (e.key === 'Escape') { close(); return; }
      if (e.key !== 'Tab') return;
      var f = focusables();
      if (!f.length) return;
      var first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }

    burger.addEventListener('click', function () {
      nav.classList.contains('is-open') ? close() : open();
    });
    $$('.mobile-nav__close, .mobile-nav__backdrop', nav).forEach(function (el) {
      el.addEventListener('click', close);
    });
    $$('.mobile-nav__links a', nav).forEach(function (a) {
      a.addEventListener('click', close);
    });
  }

  /* ------------------------------------------------------------------
     3. Reproductor de radio en vivo
        Un único <audio> compartido por el reproductor principal y la
        barra fija. Reemplaza al reproductor externo Muses (hosted.muses.org)
        por el elemento nativo del navegador: menos peso y sin terceros.
     ------------------------------------------------------------------ */
  function initPlayer() {
    var triggers = $$('[data-player-toggle]');
    if (!triggers.length) return;

    var audio = new Audio();
    audio.preload = 'none';
    audio.src = STREAM_URL;
    audio.volume = 0.8;

    var sticky = $('.sticky-player');
    var statusEls = $$('[data-player-status]');
    var eqs = $$('.eq');
    var volumes = $$('[data-player-volume]');

    // Volumen recordado entre visitas (solo en este navegador)
    try {
      var saved = localStorage.getItem('lluvia:volume');
      if (saved !== null) audio.volume = Math.min(1, Math.max(0, parseFloat(saved)));
    } catch (e) { /* almacenamiento no disponible */ }

    volumes.forEach(function (input) {
      input.value = String(Math.round(audio.volume * 100));
      input.addEventListener('input', function () {
        audio.volume = Number(input.value) / 100;
        volumes.forEach(function (o) { if (o !== input) o.value = input.value; });
        try { localStorage.setItem('lluvia:volume', String(audio.volume)); } catch (e) {}
      });
    });

    function setState(state, label) {
      triggers.forEach(function (btn) {
        btn.setAttribute('data-state', state);
        var playing = state === 'playing';
        btn.setAttribute('aria-pressed', playing ? 'true' : 'false');
        btn.setAttribute('aria-label', playing ? 'Pausar la transmisión en vivo' : 'Reproducir la transmisión en vivo');
      });
      statusEls.forEach(function (el) { el.textContent = label; });
      eqs.forEach(function (eq) { eq.setAttribute('data-active', state === 'playing' ? 'true' : 'false'); });
      if (sticky) {
        var show = state === 'playing' || state === 'loading';
        sticky.classList.toggle('is-visible', show);
        document.body.classList.toggle('has-sticky-player', show);
      }
    }

    audio.addEventListener('playing', function () { setState('playing', 'Transmitiendo en vivo'); });
    audio.addEventListener('waiting', function () { setState('loading', 'Conectando…'); });
    audio.addEventListener('pause',   function () { setState('paused', 'Pausado'); });
    audio.addEventListener('error',   function () {
      setState('paused', 'No se pudo conectar. Intenta de nuevo.');
    });

    function toggle() {
      if (audio.paused) {
        setState('loading', 'Conectando…');
        // Recargar la fuente evita reanudar audio en búfer y desfasado del directo
        audio.src = STREAM_URL + (STREAM_URL.indexOf('?') > -1 ? '&' : '?') + '_=' + Date.now();
        var p = audio.play();
        if (p && typeof p.catch === 'function') {
          p.catch(function () { setState('paused', 'Toca para escuchar'); });
        }
      } else {
        audio.pause();
      }
    }

    triggers.forEach(function (btn) { btn.addEventListener('click', toggle); });

    var closeBtn = $('.sticky-player__close');
    if (closeBtn) {
      closeBtn.addEventListener('click', function () {
        audio.pause();
        if (sticky) sticky.classList.remove('is-visible');
        document.body.classList.remove('has-sticky-player');
      });
    }

    // Controles del sistema operativo / auriculares
    if ('mediaSession' in navigator && window.MediaMetadata) {
      navigator.mediaSession.metadata = new window.MediaMetadata({
        title: 'En vivo',
        artist: STATION,
        album: 'La emisora de la gente'
      });
      try {
        navigator.mediaSession.setActionHandler('play', toggle);
        navigator.mediaSession.setActionHandler('pause', toggle);
      } catch (e) { /* acción no soportada */ }
    }

    setState('paused', 'Toca para escuchar');
  }

  /* ------------------------------------------------------------------
     4. Aparición de secciones al hacer scroll
     ------------------------------------------------------------------ */
  function initReveal() {
    var items = $$('.reveal');
    if (!items.length) return;

    var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduced || !('IntersectionObserver' in window)) {
      items.forEach(function (el) { el.classList.add('is-visible'); });
      return;
    }

    var pending = items.slice();

    function show(el) {
      el.classList.add('is-visible');
      io.unobserve(el);
      var i = pending.indexOf(el);
      if (i > -1) pending.splice(i, 1);
    }

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) show(entry.target);
      });
    }, { rootMargin: '0px 0px -10% 0px', threshold: 0.08 });

    items.forEach(function (el) { io.observe(el); });

    // Red de seguridad: un salto de scroll muy grande (ancla, rueda rápida,
    // restauración de posición) puede llevar un elemento de "debajo del
    // viewport" a "encima" entre dos fotogramas. El observador no registra
    // ningún cruce de umbral y el elemento se quedaría invisible para siempre.
    var ticking = false;
    function sweep() {
      ticking = false;
      var limit = window.innerHeight * 0.92;
      for (var i = pending.length - 1; i >= 0; i--) {
        if (pending[i].getBoundingClientRect().top < limit) show(pending[i]);
      }
      if (!pending.length) window.removeEventListener('scroll', onScroll);
    }
    function onScroll() {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(sweep);
    }
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  /* ------------------------------------------------------------------
     5. Botón "volver arriba"
     ------------------------------------------------------------------ */
  function initToTop() {
    var btn = $('.to-top');
    if (!btn) return;
    var onScroll = function () {
      btn.classList.toggle('is-visible', window.scrollY > 600);
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    btn.addEventListener('click', function () {
      var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      window.scrollTo({ top: 0, behavior: reduced ? 'auto' : 'smooth' });
    });
  }

  /* ------------------------------------------------------------------
     6. Validación de formularios
        Refuerza la validación nativa con mensajes en español.
        No intercepta el envío cuando los datos son válidos, de modo que
        el destino del formulario sigue siendo el mismo del sitio actual.
     ------------------------------------------------------------------ */
  // Entornos donde no hay PHP: servidor local y la demo publicada en GitHub Pages.
  // En el dominio real esta condición es falsa y los formularios se envían de verdad.
  function isPreviewHost() {
    var h = location.hostname;
    return h === 'localhost' || h === '127.0.0.1' || h === '' || h === '[::1]' ||
           /\.github\.io$/.test(h);
  }

  function showDemoSuccess(form) {
    var box = document.createElement('div');
    box.setAttribute('role', 'status');
    box.className = 'form-success';
    box.innerHTML =
      '<strong>¡Mensaje enviado!</strong>' +
      '<span>Gracias por escribirnos. Te responderemos a la mayor brevedad.</span>' +
      '<em>Vista previa: el envío real se realiza en el sitio publicado.</em>';
    form.replaceWith(box);
    box.scrollIntoView({ block: 'center', behavior: 'smooth' });
  }

  function initForms() {
    $$('form[data-validate]').forEach(function (form) {
      var fields = $$('input, textarea', form).filter(function (el) {
        return el.type !== 'submit' && el.type !== 'hidden' && !el.closest('.hp');
      });

      function messageFor(el) {
        if (el.validity.valueMissing) return 'Este campo es obligatorio.';
        if (el.validity.typeMismatch && el.type === 'email') return 'Escribe un correo electrónico válido.';
        if (el.validity.typeMismatch && el.type === 'tel') return 'Escribe un número de teléfono válido.';
        if (el.validity.patternMismatch) return el.getAttribute('data-pattern-error') || 'El formato no es válido.';
        if (el.validity.tooLong) return 'El texto supera el máximo permitido.';
        return 'Revisa este campo.';
      }

      function validate(el) {
        var box = el.closest('.field');
        var err = box ? $('.error', box) : null;
        var ok = el.checkValidity();
        el.setAttribute('aria-invalid', ok ? 'false' : 'true');
        if (err) {
          err.textContent = ok ? '' : messageFor(el);
          err.classList.toggle('is-shown', !ok);
        }
        return ok;
      }

      fields.forEach(function (el) {
        el.addEventListener('blur', function () { validate(el); });
        el.addEventListener('input', function () {
          if (el.getAttribute('aria-invalid') === 'true') validate(el);
        });
      });

      form.addEventListener('submit', function (e) {
        var firstBad = null;
        fields.forEach(function (el) {
          if (!validate(el) && !firstBad) firstBad = el;
        });
        if (firstBad) {
          e.preventDefault();
          firstBad.focus();
          firstBad.scrollIntoView({ block: 'center', behavior: 'smooth' });
          return;
        }
        // Modo demostración: en la preview local no existe el PHP de envío,
        // así que mostramos la confirmación sin enviar. En el dominio real
        // esta condición es falsa y el formulario se envía con normalidad.
        if (isPreviewHost()) {
          e.preventDefault();
          showDemoSuccess(form);
        }
      });
    });
  }

  /* ------------------------------------------------------------------
     7. Aviso de cookies (Ley 1581 de 2012)
        Consentimiento real, no decorativo: hasta que la persona acepta no
        debe cargarse ninguna cookie de medición. El sitio hoy no usa
        analítica; si se añade, debe engancharse al evento 'lluvia:consentimiento'
        o consultar window.lluviaCookies.estado().
     ------------------------------------------------------------------ */
  var CLAVE_COOKIES = 'lluvia:cookies';

  function leerConsentimiento() {
    try { return localStorage.getItem(CLAVE_COOKIES); } catch (e) { return null; }
  }

  function initCookies() {
    var aviso = $('.cookies');

    // API disponible aunque el aviso no esté en la página
    window.lluviaCookies = {
      estado: leerConsentimiento,
      abrir: function () { if (aviso) mostrar(); }
    };

    if (!aviso) return;

    var previo = null;

    function mostrar() {
      previo = document.activeElement;
      aviso.hidden = false;
      // Un fotograma de margen para que la transición se vea
      requestAnimationFrame(function () { aviso.classList.add('is-visible'); });
    }

    function ocultar() {
      aviso.classList.remove('is-visible');
      window.setTimeout(function () { aviso.hidden = true; }, 450);
      if (previo && typeof previo.focus === 'function') previo.focus();
    }

    function decidir(valor) {
      try { localStorage.setItem(CLAVE_COOKIES, valor); } catch (e) { /* modo privado */ }
      document.dispatchEvent(new CustomEvent('lluvia:consentimiento', { detail: { estado: valor } }));
      ocultar();
    }

    $$('[data-cookies-aceptar]', aviso).forEach(function (b) {
      b.addEventListener('click', function () { decidir('aceptado'); });
    });
    $$('[data-cookies-rechazar]', aviso).forEach(function (b) {
      b.addEventListener('click', function () { decidir('rechazado'); });
    });

    $$('[data-cookies-abrir]').forEach(function (b) {
      b.addEventListener('click', function (e) { e.preventDefault(); mostrar(); });
    });

    if (!leerConsentimiento()) {
      // Se muestra tras el primer pintado para no competir con el contenido
      window.setTimeout(mostrar, 900);
    }
  }

  /* ------------------------------------------------------------------
     8. Año del pie de página
     ------------------------------------------------------------------ */
  function initYear() {
    $$('[data-year]').forEach(function (el) {
      el.textContent = String(new Date().getFullYear());
    });
  }

  /* ------------------------------------------------------------------
     Arranque
     ------------------------------------------------------------------ */
  function boot() {
    initHeader();
    initMobileNav();
    initPlayer();
    initReveal();
    initToTop();
    initForms();
    initCookies();
    initYear();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
