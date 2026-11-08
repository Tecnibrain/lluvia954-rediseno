<?php
/**
 * Agregador de noticias — Lluvia 95.4 FM
 * ----------------------------------------------------------------------------
 * Lee varios canales RSS colombianos, los mezcla priorizando Antioquia y luego
 * el resto de Colombia, y devuelve JSON para el front-end.
 *
 * La prioridad regional se consigue de dos formas que se complementan: un
 * impulso en el orden (ver 'boost') y unos cupos reservados en las primeras
 * posiciones (ver CUPOS_ANTIOQUIA), porque el impulso por sí solo se queda
 * corto frente al volumen de noticias nacionales.
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
 * Cupos reservados a Antioquia, como pares [hasta_posición, mínimo]:
 * «al menos 4 entre las 8 primeras» y «al menos 8 entre las 20 primeras».
 * Solo se adelanta una noticia regional cuando, de no hacerlo, el cupo ya no
 * podría cumplirse con las posiciones libres que quedan; el resto del orden
 * por recencia se conserva intacto.
 */
const CUPOS_ANTIOQUIA = [[8, 4], [20, 8]];

/**
 * Antigüedad máxima, en horas, para que una noticia regional pueda ascender
 * por cupo. Evita clavar arriba una nota de hace tres días solo por llenar
 * el hueco reservado.
 */
const HORAS_FRESCURA_CUPO = 48;

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
        $ts          = fecha($item);

        $noticias[] = [
            'titulo'    => $titulo,
            'extracto'  => extracto($descripcion),
            'enlace'    => $enlace,
            'imagen'    => imagen($item, $descripcion),
            'fuente'    => $f['fuente'],
            'categoria' => $f['categoria'],
            'etiqueta'  => $f['etiqueta'],
            'fecha'     => gmdate('c', $ts),
            '_orden'    => $ts + $f['boost'],
            '_ts'       => $ts,
        ];
    }
}

// Prioridad: Antioquia primero, luego Colombia, después el resto — pero una
// noticia muy reciente de otra sección puede adelantar a una regional antigua.
usort($noticias, function ($a, $b) {
    return $b['_orden'] <=> $a['_orden'];
});

// El impulso por sí solo no bastaba: El Colombiano publica unas 20 notas de
// Antioquia frente a casi 60 nacionales, y las nacionales suelen ser más
// recientes, así que la región acababa relegada. Los cupos le reservan sitio.
$noticias = aplicarCupos($noticias, CUPOS_ANTIOQUIA, time() - HORAS_FRESCURA_CUPO * 3600);

foreach ($noticias as &$n) {
    unset($n['_orden'], $n['_ts']);
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

/**
 * Reordena la lista para cumplir los cupos regionales.
 *
 * Recorre las posiciones una a una tomando siempre la mejor noticia disponible
 * según el orden ya calculado. Solo cuando a un cupo le quedan tantas unidades
 * por cubrir como posiciones libres en su ventana, fuerza en ese hueco la
 * noticia de Antioquia más reciente que siga dentro del margen de frescura.
 * Si no queda ninguna disponible, continúa sin forzar: nunca deja huecos.
 *
 * @param array $noticias Ya ordenadas por relevancia.
 * @param array $cupos    Pares [hasta_posición, mínimo].
 * @param int   $frescura Marca de tiempo mínima para poder ascender por cupo.
 * @return array
 */
function aplicarCupos(array $noticias, array $cupos, $frescura)
{
    $total = count($noticias);
    if ($total === 0 || empty($cupos)) {
        return $noticias;
    }

    $ultima = 0;
    foreach ($cupos as $c) {
        $ultima = max($ultima, $c[0]);
    }

    $usado    = [];
    $salida   = [];
    $regional = 0; // noticias de Antioquia ya colocadas
    $cursor   = 0; // primera posición sin usar del orden general

    for ($pos = 1; $pos <= $total; $pos++) {
        $forzar = false;
        if ($pos <= $ultima) {
            foreach ($cupos as $c) {
                if ($pos > $c[0]) {
                    continue;
                }
                $faltan = $c[1] - $regional;
                $huecos = $c[0] - $pos + 1;
                if ($faltan > 0 && $faltan >= $huecos) {
                    $forzar = true;
                    break;
                }
            }
        }

        $elegido = -1;

        if ($forzar) {
            for ($j = $cursor; $j < $total; $j++) {
                if (isset($usado[$j])) {
                    continue;
                }
                if ($noticias[$j]['categoria'] === 'antioquia'
                    && $noticias[$j]['_ts'] >= $frescura) {
                    $elegido = $j;
                    break;
                }
            }
        }

        if ($elegido < 0) {
            while ($cursor < $total && isset($usado[$cursor])) {
                $cursor++;
            }
            if ($cursor >= $total) {
                break;
            }
            $elegido = $cursor;
        }

        $usado[$elegido] = true;
        if ($noticias[$elegido]['categoria'] === 'antioquia') {
            $regional++;
        }
        $salida[] = $noticias[$elegido];
    }

    return $salida;
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
