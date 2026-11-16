import json,re,sys,glob
sp=sys.argv[1]
orig=set();ref=set()
for m in json.load(open('api/media.json')):
    if m.get('source_url'): orig.add(m['source_url'])
rx=re.compile(r'https?:\\?/\\?/irongravel\.com\\?/wp-content\\?/[^"\'\s\\)<>,]+(?:\\?/[^"\'\s\\)<>,]+)*')
for f in ['api/pages.json','api/posts.json','api/producto.json','api/navigation.json','api/categories.json']+glob.glob(sp+'/*.xml')+glob.glob(sp+'/*.html'):
    t=open(f,encoding='utf-8',errors='replace').read().replace('\\/','/')
    for u in re.findall(r'https?://irongravel\.com/wp-content/[^"\'\s\\)<>,&]+',t): ref.add(u.split('?')[0].replace('http://','https://'))
orig={u.replace('http://','https://') for u in orig}
allu=sorted(orig|ref)
open('urls_all.txt','w').write('\n'.join(allu)+'\n')
print(len(orig),len(ref),len(allu))
from collections import Counter
print(Counter(u.rsplit('.',1)[-1].lower()[:5] for u in allu).most_common(15))
print(sum(1 for u in allu if '/uploads/' not in u))
