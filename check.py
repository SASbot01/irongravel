#!/usr/bin/env python3
"""Comprueba que todo enlace y fichero interno de ./public existe."""
import re, os, glob, collections, urllib.parse
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'public')
miss_a, miss_p = collections.defaultdict(set), collections.defaultdict(set)
pages = glob.glob(OUT + '/**/index.html', recursive=True)
for f in pages:
    h = open(f, encoding='utf-8').read()
    h = re.sub(r'<script[^>]*>[\s\S]*?</script>', lambda m: m.group(0) if 'src=' in m.group(0)[:300] and len(m.group(0)) < 600 else '', h)
    urls = set(re.findall(r'(?:href|src|data-lazy-src|data-src|poster)=["\'](/[^"\'#?]*)', h))
    for s in re.findall(r'(?:srcset|data-lazy-srcset)=["\']([^"\']+)', h):
        urls |= {x.strip().split(' ')[0].split('?')[0] for x in s.split(',') if x.strip().startswith('/')}
    urls |= set(re.findall(r'url\(["\']?(/[^"\')?#]+)', h))
    for u in urls:
        if u.startswith('//'):
            continue
        p = os.path.join(OUT, urllib.parse.unquote(u).lstrip('/'))
        if os.path.isfile(p) or os.path.isfile(os.path.join(p, 'index.html')):
            continue
        (miss_a if re.search(r'\.[a-z0-9]{2,5}$', u) else miss_p)[u].add(os.path.relpath(os.path.dirname(f), OUT))
print(len(pages), 'páginas')
print('FICHEROS que faltan:', len(miss_a))
for u, w in sorted(miss_a.items()): print('  ', u, '<-', len(w), sorted(w)[:2])
print('PÁGINAS enlazadas que faltan:', len(miss_p))
for u, w in sorted(miss_p.items()): print('  ', u, '<-', len(w), sorted(w)[:2])
