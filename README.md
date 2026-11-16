# irongravel.com — web recuperada

Copia estática de **https://irongravel.com** reconstruida el 12-11-2026 tras perderse el repo y el
servidor original (WordPress + tema Zephyr con tema hijo «IronGravel», en Plesk). El WordPress quedó
en «modo mantenimiento» el 05-03-2026; esta copia recupera la web tal y como se veía justo antes.

## Qué hay

| Ruta | Contenido |
|---|---|
| `public/` | **La web lista para servir** (HTML estático + `wp-content/` con todas las fotos, PDF, GPX, vídeos, fuentes, CSS y JS). |
| `build.py` | Genera `public/**/index.html` a partir de las fuentes de `rescate/`. |
| `check.py` | Comprueba que todo enlace y fichero interno existe. |
| `deploy/` | Publicación en el minipc (Docker + nginx + túnel de Cloudflare). |
| `rescate/cc/` | HTML original de cada página (Common Crawl, capturas de 2025-08 a 2026-02). |
| `rescate/api/` | Volcado de la API REST de WordPress: 50 páginas, 11 noticias, 12 productos, índice de la mediateca (3.888 entradas). |
| `rescate/live/` | Página de mantenimiento tal y como estaba el día del rescate. |
| `rescate/*.py, *.sh` | Scripts usados para la descarga. |

```bash
python3 build.py     # regenera public/
python3 check.py     # enlaces y ficheros
python3 -m http.server 8765 --directory public
```

## Publicación

- **Repo:** `SASbot01/irongravel` (rama `main`). Lleva la web entera, fotos incluidas (~1,2 GB; el
  fichero más grande, el aftermovie de 2022, pesa 58 MB, por debajo del límite de 100 MB de GitHub).
- **Dónde se sirve:** en el minipc, con `deploy/`. nginx sirve `public/` (solo en local,
  `127.0.0.1:8830`) y el túnel de Cloudflare `irongravel` (`4825a63f-fd33-4043-b2fe-a092799ff9de`) lo
  publica en `irongravel.com` y `www`. La credencial del túnel vive fuera del repo, en
  `/home/s4sf/.cloudflared/<uuid>.json`. No va en Vercel: el equipo es Hobby, ya se pasa del
  almacenamiento gratis y la web pesa 1,2 GB; detrás de Cloudflare las fotos salen de su caché.
- **Dominio:** canónica `https://irongravel.com/`. nginx manda `www` al dominio sin www (301) y las URL
  sin barra final a su versión con barra (`/contacto` → `/contacto/`), como hacía WordPress. En
  Cloudflare, `@` y `www` son CNAME con proxy a `4825a63f-fd33-4043-b2fe-a092799ff9de.cfargotunnel.com`;
  el certificado lo pone Cloudflare y «Always Use HTTPS» pasa `http` a `https`. El correo (Google
  Workspace, y Mailgun en `m.`) sigue en la misma zona.
- **Pantalla de mantenimiento (activa desde el 16-11-2026):** con `set $mantenimiento 1;` en
  `deploy/nginx.conf`, todas las páginas responden 503 con `public/mantenimiento.html` («Web en
  mantenimiento · Estamos realizando cambios.», el mismo texto que tenía el WordPress), con
  `Retry-After` para que Google no las dé por perdidas. Las fotos y ficheros de `wp-content/` y
  `robots.txt` siguen saliendo. Para abrir la web: poner `0` y `docker exec irongravel-web nginx -s reload`.
- **Actualizar:** en el minipc, `cd ~/sites/irongravel && git pull`. nginx lee `public/` directamente,
  así que no hay que reiniciar nada; si cambia `deploy/nginx.conf`,
  `docker exec irongravel-web nginx -s reload`. Levantarlo desde cero: `cd deploy && docker compose up -d`.
- El servicio `preview` de `deploy/docker-compose.yml` da una URL temporal `*.trycloudflare.com` (con
  `noindex`) para enseñarla mientras el dominio no apunta al túnel; se puede quitar cuando
  `irongravel.com` ya responda.

## De dónde sale cada página

- **41 páginas con su HTML original** (portada, IG360 720K, Festival Cabo de Palos, tienda y productos,
  contacto, newsletter, ediciones 2020/2023… en español e inglés): se usan tal cual, solo se reescriben
  las URL y se quitan restos de plugins.
- **36 páginas reconstruidas**: no había copia de su HTML, así que se montan con la plantilla original
  (cabecera, menú y pie) + el contenido que aún servía la API de WordPress. Son: `ig360/` y sus
  distancias 100K/226K/360K, ediciones 2021/2022, IG360 2022, Media, Noticias, Patrocinadores, FAQ,
  páginas legales, 8 noticias antiguas y sus equivalentes en inglés.
- **42 páginas de galería** (`…/page/N/`): generadas a partir de la lista completa de fotos de cada galería.

## Diferencias conocidas respecto al original

- **Fondos de cabecera inferidos** en 7 páginas reconstruidas (IG360, 100K, 226K, 360K, Patrocinadores,
  Noticias y sus versiones inglesas): su CSS de diseño se perdió; el fondo se ha deducido de la imagen
  adjunta a cada página en la mediateca (`INFERRED` / `HERO_BY_PATH` en `build.py`). Quedan 8 estilos
  menores sin recuperar (tamaños/espaciados de algún bloque en IG360, Media, Patrocinadores y FAQ).
- **Formularios**: el de contacto era de Gravity Forms (necesita WordPress) y **no envía**. El de
  newsletter es un iframe de RockTheSport y sigue funcionando.
- **Galerías**: «Cargar más» / scroll infinito se sustituyen por un botón propio que muestra las fotos
  de 40 en 40; la paginación numerada son páginas estáticas.
- **Tema**: el HTML es de Zephyr 8.4x y el CSS/JS recuperado es el 9.3.1 que servía el servidor.
- **Enlaces que ya estaban rotos** en el original (página «Iron Gravel Busot» retirada): `/iron-gravel/110k/`,
  `/iron-gravel/55k/`, `/en/iron-gravel/`.
- No es un WordPress: no hay panel de administración. Para editar contenido hay que tocar las fuentes
  y regenerar, o reimportar `rescate/api/*.json` en un WordPress nuevo (harían falta las licencias de
  Zephyr, Gravity Forms, WPML y WP Rocket).
