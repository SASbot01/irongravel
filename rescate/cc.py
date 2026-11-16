# Recupera de Common Crawl el HTML original de cada pagina de irongravel.com (ultima captura anterior al mantenimiento, 2026-03-05)
import json,urllib.request,time,gzip,io,os,re,sys
UA={'User-Agent':'Mozilla/5.0'}
def get(u,h={},t=45):
    for i in range(3):
        try: return urllib.request.urlopen(urllib.request.Request(u,headers={**UA,**h}),timeout=t).read()
        except Exception as e: err=e; time.sleep(5)
    print('FAIL',u,err); return None
cols=[c['id'] for c in json.loads(get('https://index.commoncrawl.org/collinfo.json'))]
cols=[c for c in cols if 'CC-MAIN-2025-08'<=c<='CC-MAIN-2026-12']
best={}
if os.path.exists('cc/index.json'): best=json.load(open('cc/index.json'))
else:
    for c in cols:
        cf=f'cc/idx_{c}.jsonl'
        if os.path.exists(cf): d=open(cf,'rb').read()
        else:
            d=get(f'https://index.commoncrawl.org/{c}-index?url=irongravel.com/*&output=json&filter=status:200')
            if d and d.lstrip().startswith(b'{'): open(cf,'wb').write(d)
            else: d=b''
        n=0
        for l in (d or b'').decode().splitlines():
            try: r=json.loads(l)
            except: continue
            if r['timestamp']>='20260305': continue
            u=re.sub(r'^https?://(www\.)?','https://',r['url'])
            n+=1
            if u not in best or r['timestamp']>best[u]['timestamp']: best[u]=r
        print(c,n,len(best)); sys.stdout.flush(); time.sleep(3)
    json.dump(best,open('cc/index.json','w'),indent=1)
    if '--index-only' in sys.argv: sys.exit()
for u,r in sorted(best.items()):
    n=re.sub(r'[^A-Za-z0-9_.=-]','_',u.split('irongravel.com/',1)[1].rstrip('/').replace('/','__')) or 'index'
    f=f'cc/{n}.html'
    if os.path.exists(f): continue
    o,l=int(r['offset']),int(r['length'])
    b=get('https://data.commoncrawl.org/'+r['filename'],{'Range':f'bytes={o}-{o+l-1}'})
    if not b: continue
    raw=gzip.decompress(b)
    body=raw.split(b'\r\n\r\n',2)[2]
    open(f,'wb').write(body); print(r['timestamp'][:8],len(body),u); sys.stdout.flush(); time.sleep(1)
