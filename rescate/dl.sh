#!/bin/sh
# uso: dl.sh URL  -> guarda en site/<ruta>
u="$1"; p="../public/${u#https://irongravel.com/}"
[ -s "$p" ] && exit 0
mkdir -p "$(dirname "$p")"
curl -sSL --retry 3 --retry-delay 2 -m 300 -A "Mozilla/5.0" -f -o "$p" "$u" 2>/dev/null || { rm -f "$p"; echo "$u" >> fallidos.txt; }
