import json,urllib.request,sys,time
B='https://irongravel.com/wp-json/wp/v2/'
def get(u):
    for i in range(4):
        try:
            r=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=60)
            return json.load(r),r.headers
        except Exception as e:
            err=e; time.sleep(2)
    print('FAIL',u,err); return None,None
for ep in ['pages','posts','producto','media','categories','tags','menus','menu-items','navigation','blocks','users','comments']:
    out=[];p=1
    while True:
        d,h=get(f'{B}{ep}?per_page=100&page={p}')
        if not isinstance(d,list) or not d: break
        out+=d
        if p>=int(h.get('X-WP-TotalPages',1)): break
        p+=1
    json.dump(out,open(ep.replace('/','_')+'.json','w'),ensure_ascii=False,indent=1)
    print(ep,len(out)); sys.stdout.flush()
