#!/usr/bin/env python3
"""Reconstruye irongravel.com como web estática en ./public

Fuentes (todas en ./rescate):
  cc/*.html        HTML original de cada página (Common Crawl, capturas 2025-08 … 2026-02,
                   anteriores al modo mantenimiento del 2026-03-05)
  api/*.json       Volcado de la API REST de WordPress (páginas, noticias, productos, mediateca)
  live/            Página de mantenimiento actual (trae el CSS global del tema)
Los ficheros (fotos, fuentes, CSS, JS) ya están en ./public/wp-content y ./public/wp-includes.

Uso:  python3 build.py
"""
import json, re, os, html, glob, sys, collections

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'rescate')
OUT = os.path.join(ROOT, 'public')
DOM = 'irongravel.com'
BUNDLE = '/wp-content/cache/min/1/ff9b36acde01c116fc457b1c3d4f9e46.js'


def rd(f):
    return open(f, encoding='utf-8', errors='replace').read()


# ---------------------------------------------------------------- fuentes
idx = json.load(open(f'{SRC}/cc/index.json'))
CC = {}  # ruta ('' = portada, 'en/contact/') -> html
for u in idx:
    rel = u.split(DOM + '/', 1)[1]
    name = re.sub(r'[^A-Za-z0-9_.=-]', '_', rel.rstrip('/').replace('/', '__')) or 'index'
    f = f'{SRC}/cc/{name}.html'
    if os.path.exists(f) and not rel.startswith('wp-') and rel != 'robots.txt':
        CC[rel] = rd(f)

PAGES = json.load(open(f'{SRC}/api/pages.json'))
POSTS = json.load(open(f'{SRC}/api/posts.json'))
PRODS = json.load(open(f'{SRC}/api/producto.json'))
MEDIA = {m['id']: m for m in json.load(open(f'{SRC}/api/media.json'))}
BYID = {p['id']: p for p in PAGES}

ES_W = set('el la los las de del que y en un una para con por se es al más como su sus este esta también será desde hasta entre sobre cada todos nuestro nuestra'.split())
EN_W = set('the of and to in is for with on that this are be will from your you our we it as at by an or all each have has can more'.split())


EN_SLUGS = {'sponsors', 'contact', 'faq', 'cookies-policy', 'privacy-policy', 'terms-and-conditions', 'home'}
ES_SLUGS = {'patrocinadores', 'contacto', 'preguntas-frecuentes', 'politica-de-cookies', 'politica-de-privacidad', 'terminos-y-condiciones', 'noticias'}


def lang_of(p):
    if p['type'] == 'page':
        if p['id'] == 9 or p['slug'] in ES_SLUGS:
            return 'es'
        if p['slug'] in EN_SLUGS:
            return 'en'
        par = BYID.get(p.get('parent') or 0)
        if par:
            return lang_of(par)
        twins = sorted(q['id'] for q in PAGES if q['slug'] == p['slug'] and not q.get('parent'))
        if len(twins) == 2:  # WPML: la traducción inglesa es la copia posterior
            return 'es' if p['id'] == twins[0] else 'en'
    t = re.sub(r'<[^>]+>', ' ', p['content']['rendered'] + ' ' + p['title']['rendered']).lower()
    w = re.findall(r'[a-záéíóúñ]+', t)
    es = sum(1 for x in w if x in ES_W)
    en = sum(1 for x in w if x in EN_W)
    return 'en' if en > es else 'es'


def api_path(p):
    par = BYID.get(p.get('parent') or 0)
    return (api_path(par) if par else '') + p['slug'] + '/'


# ---------------------------------------------------------------- CSS de diseño (us_custom_*)
def css_chunks(css):
    out, depth, start = [], 0, 0
    for i, ch in enumerate(css):
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                out.append(css[start:i + 1].strip())
                start = i + 1
    return out


def design_css(h):
    m = re.search(r'<style id="us-design-options-css">([\s\S]*?)</style>', h)
    return m.group(1) if m else ''


base, media = [], collections.OrderedDict()
for h in list(CC.values()) + [rd(f'{SRC}/live/mantenimiento-actual.html')]:
    for ch in css_chunks(design_css(h)):
        if ch.startswith('@media'):
            q, inner = ch.split('{', 1)
            for r in css_chunks(inner[:-1]):
                media.setdefault(q.strip(), [])
                if r not in media[q.strip()]:
                    media[q.strip()].append(r)
        elif ch not in base:
            base.append(ch)
UNION_CSS = ''.join(base) + ''.join(q + '{' + ''.join(rs) + '}' for q, rs in media.items())

# Estilos INFERIDOS: 7 páginas no tenían copia de su HTML original, así que su CSS de diseño se perdió.
# El fondo de cada cabecera se deduce de la imagen adjunta a la página en la mediateca
# (mismo patrón que la página hermana ig360/720k, que sí se conserva).
HERO = 'background:url(/wp-content/uploads/%s) no-repeat center center / cover!important'
INFERRED = {
    'us_custom_2800f86c': HERO % '2024/10/PortadaIG360General-1.jpg',            # ig360
    'us_custom_f0df146e': HERO % '2024/10/PortadaIG100Individual-1.jpg',         # ig360/100k
    'us_custom_cc227a70': HERO % '2024/10/PortadaIG200Individual-1.jpg',         # ig360/226k
    'us_custom_8925c852': HERO % '2024/10/PortadaIG360Individual-1.jpg',         # ig360/360k
    'us_custom_8dc4b805': HERO % '2023/10/Foto-principal-PatrocinadoresFinal-1.jpg',  # patrocinadores
    'us_custom_01a63aac': HERO % '2023/10/Foto-principal-Noticias-final-1.jpg',  # noticias
    'us_custom_12a46547': 'color:#ffffff!important',                              # título sobre el slider de Media
}
HERO_BY_PATH = {'ig360/': '2024/10/PortadaIG360General-1.jpg', 'ig360/100k/': '2024/10/PortadaIG100Individual-1.jpg',
                'ig360/226k/': '2024/10/PortadaIG200Individual-1.jpg', 'ig360/360k/': '2024/10/PortadaIG360Individual-1.jpg',
                'patrocinadores/': '2023/10/Foto-principal-PatrocinadoresFinal-1.jpg', 'sponsors/': '2023/10/Foto-principal-PatrocinadoresFinal-1.jpg',
                'noticias/': '2023/10/Foto-principal-Noticias-final-1.jpg'}
UNION_CSS += ''.join('.%s{%s}' % (k, v) for k, v in INFERRED.items() if k not in UNION_CSS)
DEFINED = set(re.findall(r'us_custom_[0-9a-f]+', UNION_CSS))

# ---------------------------------------------------------------- páginas a generar (sin HTML original)
PAIRS = {'contacto/': 'contact/', 'patrocinadores/': 'sponsors/', 'preguntas-frecuentes/': 'faq/',
         'politica-de-cookies/': 'cookies-policy/', 'politica-de-privacidad/': 'privacy-policy/',
         'terminos-y-condiciones/': 'terms-and-conditions/', '': ''}
ES2EN = {k: 'en/' + v for k, v in PAIRS.items()}


def shell_for(path, lang):
    pre = 'en/' if lang == 'en' else ''
    p = path[len(pre):]
    if p in ('ig360/',):
        c = ['festival-cabo-de-palos/', 'ig360/720k/']
    elif p.startswith('ig360/'):
        c = ['ig360/720k/']
    elif p.startswith('ig360-20'):
        c = ['ig360-2023/']
    elif p.startswith('iron-gravel-20'):
        c = ['iron-gravel-2023/']
    else:
        c = []
    c += ['contact/' if lang == 'en' else 'contacto/']
    for x in c:
        if pre + x in CC:
            return CC[pre + x]
    raise SystemExit('sin plantilla para ' + path)


def set_main(shell, content):
    i = shell.index('<main')
    i = shell.index('>', i) + 1
    j = shell.index('</main>')
    return shell[:i] + '\n' + content + '\n' + shell[j:]


def set_head(h, p, path, lang):
    y = p.get('yoast_head') or ''
    h = re.sub(r'<!-- This site is optimized with the Yoast[\s\S]*?<!-- / Yoast SEO plugin\. -->',
               lambda m: '<!-- Yoast -->\n' + y + '\n<!-- / Yoast SEO plugin. -->', h, count=1)
    if '<title>' not in y:
        h = re.sub(r'<title>[\s\S]*?</title>', '', h, count=1)
        h = h.replace('<!-- Yoast -->', '<title>%s - Iron Gravel</title>' % p['title']['rendered'], 1)
    # canonical propio (la API devuelve el de la versión española en las traducciones)
    h = re.sub(r'<link rel="canonical" href="[^"]*"', '<link rel="canonical" href="https://%s/%s"' % (DOM, path), h)
    h = re.sub(r'(<meta property="og:url" content=")[^"]*', r'\g<1>https://%s/%s' % (DOM, path), h)
    h = re.sub(r'(<style id="us-design-options-css">)[\s\S]*?(</style>)', lambda m: m.group(1) + UNION_CSS + m.group(2), h, count=1)
    h = re.sub(r'<link rel="alternate" hreflang="[^"]*" href="[^"]*" />\s*', '', h)
    return h


def set_body(h, p, home=False):
    def f(m):
        c = re.sub(r'\b(home|page-id-\d+|postid-\d+|page-child|parent-pageid-\d+)\b', '', m.group(2))
        kind = 'postid' if p['type'] == 'post' else 'page-id'
        return m.group(1) + ('home ' if home else '') + c.strip() + ' %s-%d' % (kind, p['id']) + '"'
    return re.sub(r'(<body[^>]*class=")([^"]*)"', f, h, count=1)


def other_lang(path):
    if path.startswith('en/'):
        p = path[3:]
        inv = {v: k for k, v in PAIRS.items()}
        return inv.get(p, p)
    return ES2EN.get(path, 'en/' + path)


GEN = {}  # ruta -> html generado
missing_css = collections.Counter()
MISS_BY_PAGE = {}

for p in PAGES:
    if p['slug'] == 'mantenimiento':
        continue
    lang = lang_of(p)
    path = api_path(p)
    if path == 'home/':
        path = ''
    if lang == 'en':
        path = 'en/' + path
    if path in CC or path in GEN:
        continue
    # la versión inglesa usa otra clase para la misma cabecera: mismo fondo que su gemela española
    hero = HERO_BY_PATH.get(path[3:] if lang == 'en' else path)
    m = re.match(r'\s*<section class="l-section wpb_row (us_custom_[0-9a-f]+)[^"]*full_height', p['content']['rendered'])
    if hero and m and m.group(1) not in DEFINED:
        UNION_CSS += '.%s{%s}' % (m.group(1), HERO % hero)
        DEFINED.add(m.group(1))
    h = shell_for(path, lang)
    h = set_main(h, p['content']['rendered'])
    h = set_head(h, p, path, lang)
    h = set_body(h, p, home=path in ('', 'en/'))
    GEN[path] = h

# noticias sin HTML original: plantilla de una noticia que sí lo tiene
POST_SHELL = CC.get('iron-gravel-anuncia-patrocinio-con-maxxis/')
for p in POSTS:
    path = p['link'].split(DOM + '/', 1)[1]
    if path in CC or not POST_SHELL:
        continue
    h = POST_SHELL
    title = p['title']['rendered']
    fm = MEDIA.get(p.get('featured_media') or 0)
    img = ''
    if fm:
        w = fm.get('media_details', {}).get('width', '')
        hh = fm.get('media_details', {}).get('height', '')
        img = '<img width="%s" height="%s" src="%s" class="attachment-full size-full wp-post-image" alt="" decoding="async" />' % (w, hh, fm['source_url'])
    h = re.sub(r'(<div class="w-post-elm post_image stretched">)[\s\S]*?</noscript>(</div>)', lambda m: m.group(1) + img + m.group(2), h, count=1)
    d = p['date']
    h = re.sub(r'(<time class="w-post-elm post_date[^>]*datetime=")[^"]*("[^>]*>)([\s\S]*?)</time>',
               lambda m: m.group(1) + d + m.group(2) + '<i class="fas fa-calendar-alt"></i>%s / %s / %s</time>' % (d[8:10], d[5:7], d[0:4]), h, count=1)
    h = re.sub(r'(<h1 class="w-post-elm post_title[^>]*>)[\s\S]*?</h1>', lambda m: m.group(1) + title + '</h1>', h, count=1)
    h = re.sub(r'(<div class="w-post-elm post_content" itemprop="text">)[\s\S]*?(</div><div class="w-post-elm post_navigation)',
               lambda m: m.group(1) + p['content']['rendered'] + m.group(2), h, count=1)
    h = re.sub(r'<div class="w-post-elm post_navigation[\s\S]*?</a></div>', '', h, count=1)
    h = re.sub(r'<div class="w-sharing [\s\S]*?</div></div>', '', h, count=1)
    h = set_head(h, p, path, 'es')
    h = set_body(h, p)
    GEN[path] = h


# ---------------------------------------------------------------- post-proceso común
def cf_decode(hx):
    try:
        b = bytes.fromhex(hx)
    except ValueError:
        return ''
    return ''.join(chr(c ^ b[0]) for c in b[1:])


def exists(path):
    return os.path.isfile(os.path.join(OUT, path.lstrip('/').split('?')[0].split('#')[0]))


def fix_asset(m):
    p = m.group(0)
    if exists(p):
        return p
    for pre in ('/wp-content/cache/background-css/1/irongravel.com/wp-content/cache/min/1', '/wp-content/cache/background-css/1/irongravel.com', '/wp-content/cache/min/1'):
        if p.startswith(pre + '/wp-') and exists(p[len(pre):]):
            return p[len(pre):]
    return p


def cmplz_parts(h):
    b = re.search(r'<!-- Consent Management powered by Complianz[\s\S]*?<div id="cmplz-manage-consent"[\s\S]*?</div>', h)
    e = re.search(r'<script id="cmplz-cookiebanner-js-extra">[\s\S]*?</script>', h)
    c = re.search(r"<link rel='stylesheet' id='cmplz-general-css'[^>]*>", h)
    return {'banner': b.group(0), 'extra': e.group(0), 'css': c.group(0)}


CMPLZ = {'es': cmplz_parts(CC['']), 'en': cmplz_parts(next(h for p, h in sorted(CC.items()) if p.startswith('en/') and 'cmplz-cookiebanner-container' in h))}


def post(h, path):
    lang = 'en' if path.startswith('en/') else 'es'
    # el bloque de Yoast se queda con URL absolutas (canonical, og:image…)
    m = re.search(r'<!-- (?:This site is optimized with the Yoast|Yoast -->)[\s\S]*?<!-- / Yoast SEO plugin\. -->', h)
    yo = m.group(0) if m else ''
    if m:
        pre = ''.join(re.findall(r'<link[^>]*data-rocket-preload[^>]*>', yo))
        yo = re.sub(r'<link[^>]*data-rocket-preload[^>]*>', '', yo)
        h = h.replace(m.group(0), '\x00YOAST\x00' + pre, 1)
    # correos ofuscados por Cloudflare
    h = re.sub(r'<a ([^>]*?)href="/cdn-cgi/l/email-protection#([0-9a-f]+)"', lambda m: '<a %shref="mailto:%s"' % (m.group(1), html.escape(cf_decode(m.group(2)))), h)
    h = re.sub(r'<(?:span|a)[^>]*class="__cf_email__"[^>]*data-cfemail="([0-9a-f]+)"[^>]*>[\s\S]*?</(?:span|a)>', lambda m: html.escape(cf_decode(m.group(1))), h)
    h = re.sub(r'<script[^>]*email-decode\.min\.js[^>]*></script>', '', h)
    # scripts de terceros que ya no aplican
    h = re.sub(r'<script[^>]*static\.cloudflareinsights\.com[^>]*></script>', '', h)
    h = re.sub(r'<script[^>]*wpr-beacon[^>]*></script>', '', h)
    h = re.sub(r'<script type="speculationrules">[\s\S]*?</script>', '', h)
    # capturas antiguas: llevaban otro plugin de cookies (cookie-law-info); se sustituye por el actual (Complianz)
    if 'cookie-law-info-bar' in h:
        c = CMPLZ[lang]
        h = re.sub(r'<!--googleoff: all--><div id="cookie-law-info-bar"[\s\S]*?<!--googleon: all-->', lambda m: c['banner'] + c['extra'], h, count=1)
        h = re.sub(r'<script[^>]*cookie-law-info[^>]*>[\s\S]*?</script>', '', h)
        h = re.sub(r'<script([^>]*?) src="(https://www\.googletagmanager\.com/gtag/js[^"]*)"', r'<script type="text/plain" data-service="google-analytics" data-category="statistics"\1 data-cmplz-src="\2"', h)
        h = re.sub(r'<script>(\s*window\.dataLayer)', r'<script type="text/plain" data-service="google-analytics" data-category="statistics">\1', h)
        h = h.replace('</head>', c['css'] + '\n</head>', 1)
        h = re.sub(r'<body(?! data-cmplz)', '<body data-cmplz=1', h, count=1)
    h = re.sub(r'<link[^>]*cookie-law-info[^>]*>', '', h)
    h = re.sub(r'<script[^>]*language-cookie\.js[^>]*></script>', '', h)
    h = re.sub(r'<script[^>]*src="[^"]*/cache/min/1/js/form_embed\.js[^"]*"[^>]*>', '<script src="https://apicrm.rockthesport.com/js/form_embed.js" defer>', h)
    h = re.sub(r'<link[^>]*(?:rel="https://api\.w\.org/"|application/rsd\+xml|json\+oembed|xml\+oembed|rel=\'shortlink\'|application/rss\+xml|rel="alternate" title="JSON")[^>]*>', '', h)
    # URL internas -> relativas a la raíz
    h = h.replace('http://' + DOM, 'https://' + DOM).replace('https://www.' + DOM, 'https://' + DOM)
    h = re.sub(r'(?<![\w=?&/])(?:https:)?//' + re.escape(DOM) + r'/', '/', h)
    h = h.replace('https:\\/\\/' + DOM + '\\/wp-content', '\\/wp-content').replace('https:\\/\\/' + DOM + '\\/wp-includes', '\\/wp-includes')
    # enlaces de compartir y similares: vuelven a absolutos
    h = re.sub(r'((?:[?&](?:u|url|href)=|whatsapp[^"]*text=[^"]*?))/(?=[a-z0-9-]*/?["&])', r'\g<1>https://%s/' % DOM, h)
    # bundle JS de WP Rocket: las cachés antiguas ya no existen, se usa la actual
    h = re.sub(r'/wp-content/cache/min/1/[0-9a-f]{32}\.js', BUNDLE, h)
    h = re.sub(r'/wp-(?:content|includes)/[^"\'\s\\)<>,&?#]+', fix_asset, h)
    # variantes de srcset que ya no están en el servidor
    def clean_srcset(m):
        keep = [c for c in m.group(2).split(',') if not c.strip().startswith('/wp-content/') or exists(c.strip().split(' ')[0])]
        return m.group(1) + ','.join(keep) + m.group(3)
    h = re.sub(r'((?:data-lazy-)?srcset=")([^"]*)(")', clean_srcset, h)
    h = h.replace('href="/en/contacto"', 'href="/en/contact/"').replace('href="/en/contacto/"', 'href="/en/contact/"')
    # selector de idioma: enlace a la página equivalente
    ol = other_lang(path)
    if ol not in ALL:
        ol = 'en/' if lang == 'es' else ''
    h = re.sub(r'(<a href=")[^"]*(" class="wpml-ls-link")', r'\g<1>/%s\g<2>' % ol, h)
    es_url = path if lang == 'es' else ol
    en_url = ol if lang == 'es' else path
    alt = ''.join('<link rel="alternate" hreflang="%s" href="https://%s/%s" />\n' % (k, DOM, v) for k, v in (('es', es_url), ('en', en_url), ('x-default', es_url)))
    h = re.sub(r'<link rel="alternate" hreflang="[^"]*" href="[^"]*" />\s*', '', h)
    h = h.replace('</head>', alt + '<script defer src="/wp-content/plugins/sitepress-multilingual-cms/templates/language-switchers/legacy-dropdown-click/script.min.js"></script>\n</head>', 1)
    for c in set(re.findall(r'us_custom_[0-9a-f]+', h)) - DEFINED - set(re.findall(r'us_custom_[0-9a-f]+', design_css(h))):
        missing_css[c] += 1
        MISS_BY_PAGE.setdefault(path, []).append(c)
    return h.replace('\x00YOAST\x00', yo)


# ---------------------------------------------------------------- galerías
# Las galerías de fotos las paginaba WordPress (por páginas, «Cargar más» o scroll infinito).
# El JSON de cada galería trae la lista completa de fotos, así que se reconstruyen enteras:
#  - paginación normal  -> páginas estáticas /…/page/N/
#  - «Cargar más»/scroll -> todas las fotos en la página, mostradas de 40 en 40 con un botón propio
LOADMORE_JS = ("<script>document.addEventListener('click',function(e){var b=e.target.closest('.ig-loadmore button');if(!b)return;"
               "var g=b.closest('.w-grid'),n=0;g.querySelectorAll('.w-grid-item[hidden]').forEach(function(a){if(n++<40)a.hidden=false});"
               "if(!g.querySelector('.w-grid-item[hidden]'))b.parentNode.remove()});</script>")


def media_item(tpl, mid):
    m = MEDIA[int(mid)]
    src = re.sub(r'^https?://' + re.escape(DOM), '', m['source_url'])
    md = m.get('media_details') or {}
    t = re.sub(r'post-\d+', 'post-%s' % mid, tpl, count=1)
    t = re.sub(r'data-id="\d+"', 'data-id="%s"' % mid, t, count=1)
    t = re.sub(r'(<a [^>]*href=")[^"]*("[^>]*aria-label=")[^"]*', lambda x: x.group(1) + src + x.group(2) + html.escape(m['title']['rendered'], quote=True), t, count=1)
    t = re.sub(r'<img [^>]*>', '<img loading="lazy" decoding="async" width="%s" height="%s" src="%s" class="attachment-full size-full" alt="" />' % (md.get('width', ''), md.get('height', ''), src), t, count=1)
    return re.sub(r'<noscript>[\s\S]*?</noscript>', '', t)


def nav_html(base, cur, last, lang):
    prev_t, next_t = ('Previous', 'Next') if lang == 'en' else ('Anterior', 'Siguiente')
    url = lambda i: '/%s' % base if i == 1 else '/%spage/%d/' % (base, i)
    o = ['<nav class="pagination navigation" role="navigation">\n<div class="nav-links">']
    if cur > 1:
        o.append('<a class="prev page-numbers" href="%s"><span>%s</span></a>' % (url(cur - 1), prev_t))
    shown, dots = [i for i in range(1, last + 1) if i in (1, last) or abs(i - cur) <= 3], 0
    for k, i in enumerate(shown):
        if k and i - shown[k - 1] > 1:
            o.append('<span class="page-numbers dots">&hellip;</span>')
        o.append('<span aria-current="page" class="page-numbers current"><span>%d</span></span>' % i if i == cur else '<a class="page-numbers" href="%s"><span>%d</span></a>' % (url(i), i))
    if cur < last:
        o.append('<a class="next page-numbers" href="%s"><span>%s</span></a>' % (url(cur + 1), next_t))
    return '\n'.join(o) + '</div>\n</nav>'


def galleries(h, path):
    """Devuelve {ruta: html}: la página y, si su galería va paginada, sus /page/N/."""
    lang = 'en' if path.startswith('en/') else 'es'
    out = {path: h}
    for g in list(re.finditer(r'<div class="w-grid [^"]*pagination_(regular|ajax|infinite)[^"]*"', h))[::-1]:
        mode, a = g.group(1), g.start()
        j = re.compile(r'<div class="w-grid-json hidden" onclick=\'return (\{[\s\S]*?\})\'').search(h, a)
        if not j:
            continue
        q = json.loads(html.unescape(j.group(1)))['template_vars']['query_args']
        ids = [i for i in q.get('post__in', []) if int(i) in MEDIA]
        if q.get('post_type') != ['attachment'] or not ids:
            continue
        per = int(q.get('posts_per_page') or 40)
        i0, i1 = h.index('<article', a), h.rindex('</article>', a, j.start()) + len('</article>')
        tpl = h[i0:h.index('</article>', i0) + len('</article>')]
        tail = re.sub(r'<nav class="pagination[\s\S]*?</nav>|<div class="g-loadmore[\s\S]*?</button>\s*</div>', '\x01', h[i1:j.start()])
        items = [media_item(tpl, i) for i in ids]
        if mode == 'regular':
            last = -(-len(items) // per)
            for n in range(1, last + 1):
                body = h[:i0] + '\n'.join(items[(n - 1) * per:n * per]) + tail.replace('\x01', nav_html(path, n, last, lang)) + h[j.start():]
                if n == 1:
                    out[path] = body
                else:
                    p = '%spage/%d/' % (path, n)
                    body = body.replace('<link rel="canonical" href="https://%s/%s"' % (DOM, path), '<link rel="canonical" href="https://%s/%s"' % (DOM, p))
                    out[p] = body
            h = out[path]
        else:
            its = [x if k < per else x.replace('<article ', '<article hidden ', 1) for k, x in enumerate(items)]
            btn = ''
            if len(items) > per:
                btn = ('<div class="ig-loadmore" style="text-align:center;margin-top:2rem"><button type="button" class="w-btn us-btn-style_1">'
                       '<span class="w-btn-label">%s</span></button></div>%s' % ('Load more' if lang == 'en' else 'Cargar más', LOADMORE_JS))
            h = h[:i0] + '\n'.join(its) + tail.replace('\x01', btn) + h[j.start():]
            h = h[:a] + h[a:g.end()].replace('pagination_' + mode, 'pagination_none') + h[g.end():]
            out[path] = h
    return out


ALL = {p: h for p, h in CC.items() if '/page/' not in p}  # las /page/N/ se regeneran completas
ALL.update(GEN)
n = 0
WRITTEN = []
for path, h in sorted(ALL.items()):
    for p2, h2 in galleries(post(h, path), path).items():
        d = os.path.join(OUT, p2)
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(h2)
        WRITTEN.append(p2)
        n += 1

# ---------------------------------------------------------------- extras
os.makedirs(f'{OUT}/wp-content/plugins/sitepress-multilingual-cms/res/flags', exist_ok=True)
os.makedirs(f'{OUT}/wp-content/plugins/sitepress-multilingual-cms/templates/language-switchers/legacy-dropdown-click', exist_ok=True)
open(f'{OUT}/wp-content/plugins/sitepress-multilingual-cms/res/flags/es.svg', 'w').write(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 18 12"><path fill="#c60b1e" d="M0 0h18v12H0z"/><path fill="#ffc400" d="M0 3h18v6H0z"/></svg>')
open(f'{OUT}/wp-content/plugins/sitepress-multilingual-cms/res/flags/en.svg', 'w').write(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 18 12"><path fill="#012169" d="M0 0h18v12H0z"/><path stroke="#fff" stroke-width="2.4" d="M0 0l18 12M18 0L0 12"/><path stroke="#c8102e" stroke-width="1" d="M0 0l18 12M18 0L0 12"/><path stroke="#fff" stroke-width="4" d="M9 0v12M0 6h18"/><path stroke="#c8102e" stroke-width="2.4" d="M9 0v12M0 6h18"/></svg>')
open(f'{OUT}/wp-content/plugins/sitepress-multilingual-cms/templates/language-switchers/legacy-dropdown-click/script.min.js', 'w').write(
    "document.addEventListener('click',function(e){var t=e.target.closest&&e.target.closest('.js-wpml-ls-item-toggle');"
    "document.querySelectorAll('.js-wpml-ls-sub-menu').forEach(function(m){var mine=t&&t.parentNode.contains(m);"
    "m.style.visibility=mine&&m.style.visibility!=='visible'?'visible':'hidden'});if(t)e.preventDefault()});")
nf = set_main(CC['contacto/'], '<section class="l-section wpb_row height_huge"><div class="l-section-h i-cf" style="text-align:center">'
              '<h1>Página no encontrada</h1><p>La página que buscas no existe o ha cambiado de sitio.</p>'
              '<p><a class="w-btn us-btn-style_1" href="/"><span class="w-btn-label">Volver al inicio</span></a></p></div></section>')
nf = re.sub(r'<title>[\s\S]*?</title>', '<title>Página no encontrada - Iron Gravel</title>', nf, count=1)
nf = re.sub(r'<link rel="canonical"[^>]*>', '<meta name="robots" content="noindex" />', nf, count=1)
open(f'{OUT}/404.html', 'w', encoding='utf-8').write(post(nf, '404/'))
open(f'{OUT}/robots.txt', 'w').write('User-agent: *\nDisallow:\n\nSitemap: https://%s/sitemap.xml\n' % DOM)
open(f'{OUT}/sitemap.xml', 'w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
                                      ''.join('  <url><loc>https://%s/%s</loc></url>\n' % (DOM, p) for p in sorted(WRITTEN) if '/page/' not in p) + '</urlset>\n')

print('%d páginas (%d originales, %d reconstruidas, %d de galería)' % (n, len(ALL) - len(GEN), len(GEN), n - len(ALL)))
print('generadas:', ', '.join(sorted(GEN)))
if missing_css:
    print('clases us_custom sin CSS recuperado:', len(missing_css))
    for k, v in sorted(MISS_BY_PAGE.items()):
        print('  ', k, len(v))
