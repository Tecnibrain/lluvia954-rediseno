<?php
/**
 * Agregador de noticias — Lluvia 95.4 FM
 * ----------------------------------------------------------------------------
 * Lee varios canales RSS colombianos, los mezcla priorizando Antioquia y luego
 * el resto de Colombia, y devuelve JSON para el front-end.
 *
 * Publica SOLO titular + extracto corto + enlace a la fuente original, que es
 * el uso previsto de un RSS. No reproduce artículos completos.
 *
 * Uso:  /api/noticias.php            -> todas las categorías
 *       /api/noticias.php?cat=antioquia
 *       /api/noticias.php?limit=12
 *
 * Requiere PHP 7.0+ con SimpleXML. No necesita base de datos.
 */

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Cache-Control: public, max-age=300');

// ---------------------------------------------------------------------------
// Configuración
// ---------------------------------------------------------------------------

/** Minutos que se conserva la caché antes de volver a consultar las fuentes. */
const CACHE_MINUTOS = 20;

/** Segundos máximos de espera por canal. Evita que una fuente lenta cuelgue la página. */
const TIMEOUT = 8;

/** Máximo de caracteres del extracto. */
const EXTRACTO = 180;

/**
 * Canales. 'boost' son segundos que se suman a la fecha al ordenar: cuanto más
 * alto, más arriba aparece esa fuente frente a otras de antigüedad parecida.
 * Así Antioquia manda sin ocultar una noticia nacional de última hora.
 */
$FUENTES = [
    [
        'url'      => 'https://www.elcolombiano.com/rss/antioquia.xml',
        'fuente'   => 'El Colombiano',
        'categoria'=> 'antioquia',
        'etiqueta' => 'Antioquia',
        'boost'    => 43200, // 12 h
    ],
    [
        'url'      => 'https://www.elcolombiano.com/rss/colombia.xml',
        'fuente'   => 'El Colombiano',
        'categoria'=> 'colombia',
        'etiqueta' => 'Colombia',
        'boost'    => 14400, // 4 h
    ],
    [
        'url'      => 'https://www.eltiempo.com/rss/colombia.xml',
        'fuente'   => 'El Tiempo',
        'categoria'=> 'colombia',
        'etiqueta' => 'Colombia',
        'boost'    => 14400,
    ],
    [
        'url'      => 'https://www.elcolombiano.com/rss/cultura.xml',
        'fuente'   => 'El Colombiano',
        'categoria'=> 'cultura',
        'etiqueta' => 'Cultura',
        'boost'    => 0,
    ],
    [
        'url'      => 'https://www.eltiempo.com/rss/cultura.xml',
        'fuente'   => 'El Tiempo',
        'categoria'=> 'cultura',
        'etiqueta' => 'Cultura',
        'boost'    => 0,
    ],
    [
        'url'      => 'https://www.eltiempo.com/rss/deportes.xml',
        'fuente'   => 'El Tiempo',
        'categoria'=> 'deportes',
        'etiqueta' => 'Deportes',
        'boost'    => 0,
    ],
];

// ---------------------------------------------------------------------------
// Caché
// ---------------------------------------------------------------------------

$cacheDir  = __DIR__ . '/cache';
$cacheFile = $cacheDir . '/noticias.json';

if (!is_dir($cacheDir)) {
    @mkdir($cacheDir, 0755, true);
}

if (is_readable($cacheFile) && (time() - filemtime($cacheFile)) < CACHE_MINUTOS * 60) {
    $cacheado = file_get_contents($cacheFile);
    if ($cacheado !== false && $cacheado !== '') {
        echo responder($cacheado);
        exit;
    }
}

// ---------------------------------------------------------------------------
// Descarga y análisis
// ---------------------------------------------------------------------------

$noticias = [];
$vistos   = [];

foreach ($FUENTES as $f) {
    $xml = descargar($f['url']);
    if ($xml === null) {
        continue;
    }

    $previo = libxml_use_internal_errors(true);
    $rss = simplexml_load_string($xml);
    libxml_use_internal_errors($previo);

    if ($rss === false || !isset($rss->channel->item)) {
        continue;
    }

    foreach ($rss->channel->item as $item) {
        $enlace = trim((string) $item->link);
        $titulo = limpiar((string) $item->title);

        if ($enlace === '' || $titulo === '') {
            continue;
        }

        // Evita repetir la misma noticia si aparece en dos canales
        $clave = md5(strtolower($enlace));
        if (isset($vistos[$clave])) {
            continue;
        }
        $vistos[$clave] = true;

        $descripcion = (string) $item->description;

        $noticias[] = [
            'titulo'    => $titulo,
            'extracto'  => extracto($descripcion),
            'enlace'    => $enlace,
            'imagen'    => imagen($item, $descripcion),
            'fuente'    => $f['fuente'],
            'categoria' => $f['categoria'],
            'etiqueta'  => $f['etiqueta'],
            'fecha'     => gmdate('c', fecha($item)),
            '_orden'    => fecha($item) + $f['boost'],
        ];
    }
}

// Prioridad: Antioquia primero, luego Colombia, después el resto — pero una
// noticia muy reciente de otra sección puede adelantar a una regional antigua.
usort($noticias, function ($a, $b) {
    return $b['_orden'] <=> $a['_orden'];
});

foreach ($noticias as &$n) {
    unset($n['_orden']);
}
unset($n);

$salida = json_encode([
    'actualizado' => gmdate('c'),
    'total'       => count($noticias),
    'noticias'    => $noticias,
], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

if ($salida === false) {
    http_response_code(500);
    echo json_encode(['error' => 'No se pudo generar la respuesta']);
    exit;
}

// Solo se guarda la caché si hubo resultados: así un fallo temporal de red no
// borra una caché buena.
if (count($noticias) > 0) {
    @file_put_contents($cacheFile, $salida, LOCK_EX);
} elseif (is_readable($cacheFile)) {
    $salida = file_get_contents($cacheFile); // servimos la caché vencida
}

echo responder($salida);

// ---------------------------------------------------------------------------
// Funciones auxiliares
// ---------------------------------------------------------------------------

/** Aplica los filtros ?cat= y ?limit= sobre el JSON ya construido. */
function responder($json)
{
    $datos = json_decode($json, true);
    if (!is_array($datos) || !isset($datos['noticias'])) {
        return $json;
    }

    $cat = isset($_GET['cat']) ? preg_replace('/[^a-z]/', '', strtolower($_GET['cat'])) : '';
    if ($cat !== '' && $cat !== 'todas') {
        $datos['noticias'] = array_values(array_filter(
            $datos['noticias'],
            function ($n) use ($cat) { return $n['categoria'] === $cat; }
        ));
    }

    $limite = isset($_GET['limit']) ? (int) $_GET['limit'] : 0;
    if ($limite > 0) {
        $datos['noticias'] = array_slice($datos['noticias'], 0, min($limite, 60));
    }

    $datos['total'] = count($datos['noticias']);

    return json_encode($datos, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
}

/** Descarga una URL con cURL y, si no está disponible, con file_get_contents. */
function descargar($url)
{
    if (function_exists('curl_init')) {
        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_FOLLOWLOCATION => true,
            CURLOPT_MAXREDIRS      => 3,
            CURLOPT_TIMEOUT        => TIMEOUT,
            CURLOPT_CONNECTTIMEOUT => 5,
            CURLOPT_USERAGENT      => 'LluviaBot/1.0 (+https://lluvia954.com)',
            CURLOPT_ENCODING       => '',
        ]);
        $cuerpo = curl_exec($ch);
        $codigo = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        return ($cuerpo !== false && $codigo >= 200 && $codigo < 300) ? $cuerpo : null;
    }

    $ctx = stream_context_create(['http' => [
        'timeout'    => TIMEOUT,
        'user_agent' => 'LluviaBot/1.0 (+https://lluvia954.com)',
    ]]);
    $cuerpo = @file_get_contents($url, false, $ctx);

    return $cuerpo !== false ? $cuerpo : null;
}

/** Normaliza espacios y decodifica entidades. */
function limpiar($texto)
{
    $texto = html_entity_decode($texto, ENT_QUOTES | ENT_HTML5, 'UTF-8');
    $texto = strip_tags($texto);
    $texto = preg_replace('/\s+/u', ' ', $texto);

    return trim($texto);
}

/** Extracto corto, cortado en la última palabra completa. */
function extracto($html)
{
    $texto = limpiar($html);
    if ($texto === '') {
        return '';
    }
    if (mb_strlen($texto, 'UTF-8') <= EXTRACTO) {
        return $texto;
    }
    $corte = mb_substr($texto, 0, EXTRACTO, 'UTF-8');
    $esp   = mb_strrpos($corte, ' ', 0, 'UTF-8');
    if ($esp !== false && $esp > 60) {
        $corte = mb_substr($corte, 0, $esp, 'UTF-8');
    }

    return rtrim($corte, " ,;:.-") . '…';
}

/** Busca la imagen en enclosure, media:content o dentro del HTML del resumen. */
function imagen($item, $descripcion)
{
    if (isset($item->enclosure['url'])) {
        $u = (string) $item->enclosure['url'];
        if ($u !== '') {
            return $u;
        }
    }

    $media = $item->children('http://search.yahoo.com/mrss/');
    if (isset($media->content) && isset($media->content->attributes()->url)) {
        $u = (string) $media->content->attributes()->url;
        if ($u !== '') {
            return $u;
        }
    }
    if (isset($media->thumbnail) && isset($media->thumbnail->attributes()->url)) {
        $u = (string) $media->thumbnail->attributes()->url;
        if ($u !== '') {
            return $u;
        }
    }

    $html = html_entity_decode($descripcion, ENT_QUOTES | ENT_HTML5, 'UTF-8');
    if (preg_match('/<img[^>]+src=["\']([^"\']+)["\']/i', $html, $m)) {
        return $m[1];
    }

    return '';
}

/** Fecha de publicación como marca de tiempo; si falta, la hora actual. */
function fecha($item)
{
    $bruta = trim((string) $item->pubDate);
    if ($bruta === '') {
        $dc = $item->children('http://purl.org/dc/elements/1.1/');
        $bruta = isset($dc->date) ? trim((string) $dc->date) : '';
    }
    if ($bruta === '') {
        return time();
    }
    $t = strtotime($bruta);

    return $t !== false ? $t : time();
}
