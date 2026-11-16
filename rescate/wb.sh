#!/bin/sh
# uso: wb.sh URL  -> wayback/<nombre>.html (captura mas cercana al 2026-02-07, HTML original)
u="$1"; n=$(echo "${u#https://irongravel.com/}" | sed 's#/$##; s#/#__#g'); [ -z "$n" ] && n=index
f="wayback/$n.html"; [ -s "$f" ] && exit 0
for w in 20 45 90 180; do
  code=$(curl -sSL -m 120 -A "Mozilla/5.0" -o "$f" -w "%{http_code} %{url_effective}" "https://web.archive.org/web/20260207193656id_/$u" 2>/dev/null)
  case "$code" in 200*) echo "OK $u ${code#200 https://web.archive.org/web/}"; sleep 7; exit 0;; 404*) rm -f "$f"; echo "NO-ARCHIVADA $u"; sleep 7; exit 0;; esac
  sleep $w
done; rm -f "$f"; echo "ERROR $u $code"
