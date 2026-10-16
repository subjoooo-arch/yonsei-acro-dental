#!/usr/bin/env python3
"""네이버 블로그 글 가져오기.
사용: python3 scripts/import_naver.py <글URL|logNo ...>   또는   python3 scripts/import_naver.py --rss [--limit N]
결과: 한 섹션에만 저장 — 모두 content/posts/ (제목에 사례/케이스가 있으면 태그 '임상 케이스'), 이미지는 assets/blog/<slug>/ 에 저장.
이미 있는 파일은 건너뜀(--force 로 덮어쓰기). 이후 python3 scripts/build.py 실행."""
import sys, re, os, json, urllib.request, xml.etree.ElementTree as ET, email.utils
from bs4 import BeautifulSoup
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); BLOG='yonseiacro'
UA={'User-Agent':'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)'}
def get(u): return urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=20).read()
TAGS=[('미백','치아미백'),('사랑니','사랑니 발치'),('임플란트','임플란트'),('턱관절','턱관절 치료'),('레진','충치치료'),('인레이','충치치료'),
 ('충치','충치치료'),('크라운','보철치료'),('틀니','틀니'),('스케일링','잇몸치료'),('잇몸','잇몸치료'),('소아','소아치과'),('교정','교정·유지장치'),('신경치료','신경치료'),('마우스피스','예방·검진')]
NEWS=('연세아크로 일상',); NEWS_KW=('소개합니다','이름에 담긴','연세아크로치과의원입니다','진료팀','화환','스냅')
CASE_KW=('사례','케이스')
def tag_for(t):
  for k,v in TAGS:
    if k in t: return v
  return '병원 이야기'
def yq(s): return json.dumps(s,ensure_ascii=False)
def rss_items():
  r=ET.fromstring(get(f'https://rss.blog.naver.com/{BLOG}.xml'))
  return [(re.search(r'/(\d+)',i.findtext('link').split(BLOG)[1]).group(1), i.findtext('category'), email.utils.parsedate_to_datetime(i.findtext('pubDate')).strftime('%Y-%m-%d')) for i in r.iter('item')]
def import_post(logno,cat=None,date=None,force=False):
  slug=f'naver-{logno}'
  if not force and any(os.path.exists(f'{ROOT}/content/{d}/{slug}.md') for d in ('posts',)): print('skip',slug); return
  url=f'https://blog.naver.com/{BLOG}/{logno}'
  s=BeautifulSoup(get(f'https://m.blog.naver.com/PostView.naver?blogId={BLOG}&logNo={logno}'),'html.parser')
  title=(s.select_one('meta[property="og:title"]') or {}).get('content','').strip()
  if not date:
    m=re.search(r'(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})',s.select_one('.blog_date, .se_publishDate').get_text() if s.select_one('.blog_date, .se_publishDate') else '')
    date=f'{m[1]}-{int(m[2]):02d}-{int(m[3]):02d}' if m else ''
  c=s.select_one('.se-main-container'); os.makedirs(f'{ROOT}/assets/blog/{slug}',exist_ok=True)
  body=[]; imgs=[]
  for comp in c.select('.se-component'):
    cl=comp.get('class',[])
    if 'se-image' in cl or 'se-imageGroup' in cl or 'se-imageStrip' in cl:
      for im in comp.find_all('img'):
        src=(im.get('data-lazy-src') or im.get('src') or '').split('?')[0]
        if 'pstatic' not in src: continue
        n=len(imgs)+1; p=f'/assets/blog/{slug}/{n}.jpg'
        try: open(ROOT+p,'wb').write(get(src+'?type=w966')); imgs.append(p); body.append(f'![{title} 이미지 {n}]({p})')
        except Exception as e: print('img fail',src,e)
    elif 'se-text' in cl or 'se-quotation' in cl or 'se-sectionTitle' in cl:
      paras=[p.get_text(' ',strip=True).replace('\u200b','') for p in comp.select('p')] or [comp.get_text(' ',strip=True)]
      txt='\n'.join(x for x in paras if x.strip())
      if txt: body.append(('## ' if 'se-sectionTitle' in cl else '> ' if 'se-quotation' in cl else '')+txt.replace('\n','\n\n') )
  text=' '.join(b for b in body if not b.startswith('!'))
  summary=re.sub(r'\s+',' ',text); summary=re.sub(r'^안녕하세요\.?\s*[^.:)]*[.:)]+\s*','',summary)[:150].strip()
  category='블로그'  # 치과 소식 섹션 폐지: 모든 일반 글은 블로그로
  tag=tag_for(title)
  is_case=any(k in title for k in CASE_KW)
  fm=f'---\ntitle: {yq(title)}\ndate: {yq(date)}\ncategory: {yq(category)}\ntag: {yq(tag)}\nsummary: {yq(summary)}\nthumbnail: {yq(imgs[0] if imgs else "")}\npopular: false\nauthor: "연세아크로치과"\nsource_url: {yq(url)}\nnaver_category: {yq(cat or "")}\n---\n\n'
  # 섹션은 하나만: 임상 케이스 > 블로그
  if is_case:
    out=f'{ROOT}/content/posts/{slug}.md'
    fm=fm.replace(f'tag: {yq(tag)}','tag: "임상 케이스"')
  else:
    out=f'{ROOT}/content/posts/{slug}.md'
  os.makedirs(os.path.dirname(out),exist_ok=True); open(out,'w').write(fm+'\n\n'.join(body)+'\n'); print('ok',out.split('/content/')[1],tag,len(imgs),'imgs')
if __name__=='__main__':
  a=sys.argv[1:]; force='--force' in a
  if '--rss' in a:
    lim=int(a[a.index('--limit')+1]) if '--limit' in a else 999
    for l,c,d in rss_items()[:lim]: import_post(l,c,d,force)
  else:
    for x in a:
      if x.startswith('--'): continue
      m=re.search(r'(\d{9,})',x); m and import_post(m[1],force=force)
