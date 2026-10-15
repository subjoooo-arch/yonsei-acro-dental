#!/usr/bin/env python3
"""content/*.md + data/clinic.json -> 정적 HTML, posts.json, cases.json, sitemap.xml, llms.txt 생성.
사용: python3 scripts/build.py   (필요: pip install -r requirements.txt)"""
import os, json, re, glob, html, shutil, datetime
import yaml, markdown
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C=json.load(open(f'{R}/data/clinic.json')); D=C['site_url'].rstrip('/'); L=C['links']  # 실제 도메인 연결 시 data/clinic.json의 site_url만 바꾸면 됩니다
E=html.escape; J=lambda o: json.dumps(o,ensure_ascii=False,indent=1).replace('</','<\\/')
def load(d):
  out=[]
  for f in sorted(glob.glob(f'{R}/content/{d}/*.md')):
    t=open(f).read(); m=re.match(r'---\n(.*?)\n---\n?(.*)',t,re.S)
    fm=yaml.safe_load(m[1]) or {}; fm['body']=m[2]; fm['slug']=os.path.basename(f)[:-3]
    fm['date']=str(fm.get('date',''))[:10]; fm['summary']=re.sub(r'\s+',' ',str(fm.get('summary','') or '')).strip()
    out.append(fm)
  return sorted(out,key=lambda x:x['date'],reverse=True)
from PIL import Image
_IMG={}
def webp(src):
  """/assets/...jpg|png -> 최적화된 .webp (최대 1200px) 생성, (url,w,h) 반환"""
  if src in _IMG: return _IMG[src]
  fp=R+src; out=None
  if src.startswith('/assets/') and re.search(r'\.(jpe?g|png)$',src,re.I) and os.path.exists(fp):
    wp=re.sub(r'\.(jpe?g|png)$','.webp',fp,flags=re.I)
    if not os.path.exists(wp):
      im=Image.open(fp); im=im.convert('RGBA' if im.mode in('RGBA','LA','P') else 'RGB')
      if im.width>1200: im=im.resize((1200,round(im.height*1200/im.width)),Image.LANCZOS)
      im.save(wp,'WEBP',quality=78,method=6)
    im=Image.open(wp); out=(wp[len(R):],im.width,im.height)
  elif os.path.exists(fp) and src.endswith('.webp'):
    im=Image.open(fp); out=(src,im.width,im.height)
  _IMG[src]=out; return out
def optimize(s):
  n=[0]
  def f(m):
    tag=m[0]; src=re.search(r'src="([^"]+)"',tag)
    if not src: return tag
    r=webp(src[1]); n[0]+=1
    if r:
      tag=tag.replace(src[0],f'src="{r[0]}"')
      if 'width=' not in tag: tag=tag.replace('<img ',f'<img width="{r[1]}" height="{r[2]}" ',1)
    if 'loading=' not in tag: tag=tag.replace('<img ','<img loading="lazy" decoding="async" ',1) if n[0]>1 else tag.replace('<img ','<img fetchpriority="high" ',1)
    if 'alt=' not in tag: tag=tag.replace('<img ','<img alt="" ',1)
    return tag
  return re.sub(r'<img [^>]*>',f,s)
def w(p,s):
  if p.endswith('.html'): s=optimize(s)
  p=f'{R}/{p}'; os.makedirs(os.path.dirname(p),exist_ok=True); open(p,'w').write(s)
def ld(*objs): return ''.join(f'<script type="application/ld+json">{J(o)}</script>' for o in objs)
CLINIC_ID=D+'/#clinic'
def clinic_ld():
  return {"@context":"https://schema.org","@type":["Dentist","MedicalClinic"],"@id":CLINIC_ID,"name":C['name'],"alternateName":C['name_en'],
   "url":D+'/',"telephone":C['telephone_intl'],"image":[D+'/assets/clinic/interior-1.jpg',D+'/assets/clinic/interior-2.jpg'],"logo":{"@type":"ImageObject","url":D+'/assets/brand/logo-stacked.png',"width":710,"height":460},"priceRange":"₩₩","currenciesAccepted":"KRW","hasMap":L['naver_map'],"areaServed":["고양시 일산서구","일산동구","고양시","파주시"],"isAcceptingNewPatients":True,"knowsLanguage":"ko",
   "address":{"@type":"PostalAddress","addressCountry":"KR","addressRegion":C['address_parts']['region'],"addressLocality":C['address_parts']['locality'],"streetAddress":C['address_parts']['street']},
   "geo":{"@type":"GeoCoordinates","latitude":C['geo']['lat'],"longitude":C['geo']['lng']},
   "openingHoursSpecification":[{"@type":"OpeningHoursSpecification","dayOfWeek":h['days'],"opens":h['open'],"closes":h['close']} for h in C['hours']],
   "medicalSpecialty":["Dentistry","Prosthodontics","Endodontics"],"availableService":[{"@type":"MedicalProcedure","name":t['name']} for t in C['treatments']],
   "sameAs":[L['naver_map'],L['google_maps'],L['kakao_channel'],L['naver_blog']],"potentialAction":{"@type":"ReserveAction","target":L['naver_booking']},
   "employee":[{"@id":D+f'/#doctor-{i}'} for i in range(len(C['doctors']))]}
def physician_ld():
  return [{"@context":"https://schema.org","@type":"Physician","@id":D+f'/#doctor-{i}',"name":d['name'],"jobTitle":d['role'],"medicalSpecialty":d['specialty'],"url":D+'/about/#doctor-'+str(i),"knowsAbout":[x for x in d['career'] if '전문의' in x],
    "description":' / '.join(d['career']),"image":D+d['photo'],"worksFor":{"@id":CLINIC_ID},"alumniOf":{"@type":"CollegeOrUniversity","name":re.sub(r"\s.*","",d['career'][1])}} for i,d in enumerate(C['doctors'])]
def crumbs(items): return {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":i+1,"name":n,"item":D+u} for i,(n,u) in enumerate(items)]}
def faq_ld(qs): return {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in qs]}
def faq_html(qs): return '<section class="faq"><h2>자주 묻는 질문</h2>'+''.join(f'<details><summary>{E(q)}</summary><p>{E(a)}</p></details>' for q,a in qs)+'</section>'
HOURS_TXT=' / '.join(f"{h['label']} {h['open']}~{h['close']}" for h in C['hours'])
BASE_FAQ=[("연세아크로치과의원 진료시간은 어떻게 되나요?",f"{HOURS_TXT}. 평일 점심시간 {C['lunch']}, {C['closed']}입니다."),
 ("연세아크로치과의원은 어디에 있나요?",f"{C['address']}. {C['directions']['subway']}에 있습니다."),
 ("주차가 가능한가요?",C['directions']['car']),
 ("예약은 어떻게 하나요?",f"대표전화 {C['phone']} 또는 네이버 예약, 카카오톡 채널로 예약 문의하실 수 있습니다.")]
CSS=re.sub(r'\s*\n\s*','',open(f'{R}/css/style.css').read())
FONT='https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard-dynamic-subset.min.css'
def verif():
  o=''
  for k,n in (('naver_verification','naver-site-verification'),('google_verification','google-site-verification'),('bing_verification','msvalidate.01')):
    if C.get(k): o+=f'<meta name="{n}" content="{E(C[k])}">'
  return o
def head(title,desc,path,img='/assets/brand/og-image.jpg',typ='website',noindex=False,extra=''):
  return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><script>if(/(invite|recovery|confirmation|email_change)_token=/.test(location.hash))location.replace('/admin/'+location.hash)</script>
<title>{E(title)}</title><meta name="description" content="{E(desc)}"><link rel="canonical" href="{D}{path}">
{'<meta name="robots" content="noindex,follow">' if noindex else '<meta name="robots" content="index,follow,max-image-preview:large">'}
{verif()}
<meta property="og:type" content="{typ}"><meta property="og:site_name" content="{C['name']}"><meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:url" content="{D}{path}"><meta property="og:image" content="{D}{img}"><meta property="og:locale" content="ko_KR">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{E(title)}"><meta name="twitter:description" content="{E(desc)}"><meta name="twitter:image" content="{D}{img}">
<meta name="geo.region" content="KR-41"><meta name="geo.position" content="{C['geo']['lat']};{C['geo']['lng']}">
<link rel="icon" href="/favicon.ico" sizes="any"><link rel="icon" type="image/png" href="/assets/favicon-192.png"><link rel="apple-touch-icon" href="/assets/apple-touch-icon.png"><meta name="theme-color" content="#2f4a6b"><link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin><link rel="preload" as="style" href="{FONT}" onload="this.onload=null;this.rel='stylesheet'"><noscript><link rel="stylesheet" href="{FONT}"></noscript>{'<link rel="preload" as="image" href="/assets/clinic/interior-1.webp" fetchpriority="high">' if path=="/" else ""}<style>{CSS}</style>{extra}</head><body class="{"home" if path=="/" else "sub"}">
<header class="site"><div class="wrap"><a class="logo" href="/" aria-label="{C['name']} 홈"><img class="lc" src="/assets/brand/logo-horizontal-96.png" alt="{C['name']} 로고" loading="eager"><img class="lw" src="/assets/brand/logo-horizontal-white-96.png" alt="" aria-hidden="true" loading="eager"></a><nav aria-label="주 메뉴"><a href="/#doctors">의료진</a><a href="/treatments/">진료과목</a><a href="/blog/">블로그</a><a href="/cases/">임상 케이스</a><a href="/about/">병원 정보</a><a href="/faq/">FAQ</a><a href="/#location">오시는 길</a></nav><a class="hbtn" href="{L['naver_booking']}" target="_blank" rel="noopener">예약하기</a></div></header><main>'''
def foot():
  return f'''</main><section class="ctaband"><div class="wrap"><div><p class="eyebrow light">예약 · 상담</p><h2>아픈 곳이 없어도,<br><em>궁금한 점부터</em> 편하게<br>물어보세요.</h2><p>전문의가 현재 상태를 정확히 설명드리고,<br>꼭 필요한 치료만 함께 정하겠습니다.</p></div>
<div class="cbtns"><a class="cb w" href="tel:{C['phone']}"><span>전화 {C['phone']}</span><i>→</i></a><a class="cb y" href="{L['kakao_channel']}" target="_blank" rel="noopener"><span>카카오톡 상담</span><i>→</i></a><a class="cb g" href="{L['naver_booking']}" target="_blank" rel="noopener"><span>네이버 예약</span><i>→</i></a></div></div></section><footer class="site"><div class="wrap fgrid"><div><img class="flogo" src="/assets/brand/logo-stacked-white-260.png" alt="{C['name']} 로고" loading="lazy"><strong>{C['name']}</strong><address>주소: {C['address']}<br>대표전화: <a href="tel:{C['phone']}">{C['phone']}</a><br>대표: {C['ceo']} · 사업자등록번호: {C['biz_no']}</address></div>
<div class="flinks"><a href="{L['naver_booking']}" target="_blank" rel="noopener">네이버 예약</a><a href="{L['kakao_channel']}" target="_blank" rel="noopener">카카오톡 채널 상담·예약</a><a href="{L['naver_map']}" target="_blank" rel="noopener">네이버 지도</a><a href="{L['google_maps']}" target="_blank" rel="noopener">Google 지도</a><a href="{L['naver_blog']}" target="_blank" rel="noopener">네이버 블로그</a></div></div>
<div class="wrap copy">© {datetime.date.today().year} Yonsei Acro Dental Clinic. 본 사이트의 의료 정보는 일반적인 안내이며, 치료 결과는 개인에 따라 다를 수 있습니다.</div></footer>
<div class="fab"><a href="{L['naver_booking']}" target="_blank" rel="noopener" class="f1" aria-label="네이버 예약">예약</a><a href="{L['kakao_channel']}" target="_blank" rel="noopener" class="f2" aria-label="카카오톡 상담">톡</a><a href="tel:{C['phone']}" class="f3" aria-label="전화">☎</a></div><script src="/js/site.js" defer></script><div class="mbar"><a href="tel:{C['phone']}">📞 전화</a><a href="{L['naver_booking']}" target="_blank" rel="noopener" class="nv">N 네이버 예약</a><a href="{L['kakao_channel']}" target="_blank" rel="noopener" class="kk">💬 카카오 예약</a></div></body></html>'''
def card(p,base=None):
  th=f'<img loading="lazy" src="{p["thumbnail"]}" alt="{E(p["title"])} 대표 이미지">' if p.get('thumbnail') else ''
  return f'<a class="pcard" data-tag="{E(p["tag"])}" href="{p.get("url") or "/blog/posts/"+p["slug"]+".html"}">{th}<div><span class="tag">#{E(p["tag"])}</span><h3>{E(p["title"])}</h3><p>{E(p["summary"][:90])}…</p><time datetime="{p["date"]}">{p["date"].replace("-",". ")}</time></div></a>'
def booking_box():
  return f'<div class="bbox"><a class="btn" href="{L["naver_booking"]}" target="_blank" rel="noopener">네이버 예약</a><a class="btn kk" href="{L["kakao_channel"]}" target="_blank" rel="noopener">카카오톡 상담·예약</a><a class="btn ghost" href="tel:{C["phone"]}">{C["phone"]}</a></div>'
def md(t): return re.sub(r'<(/?)h1>',r'<\1p>',markdown.markdown(re.sub(r'(?m)^#(?=[^#\s])',r'\#',t),extensions=['extra']))
for d in ('blog/posts','cases'):
  for f in glob.glob(f'{R}/{d}/*.html'): os.remove(f)
blog=load('posts'); cases=load('cases')
for p in blog: p['url']=f'/blog/posts/{p["slug"]}.html'; p['category']='블로그'
posts=blog
for c in cases: c['public']=not c.get('review_required',True)
# ---- data json
w('blog/posts.json',J([{k:p.get(k) for k in ('slug','title','date','category','tag','summary','thumbnail','popular','url','source_url')} for p in posts]))
w('cases/cases.json',J([{k:c.get(k) for k in ('slug','title','date','treatment','period','before','after','notes','review_required','post','source_url')} for c in cases]))
# ---- home
docs=''.join(f'<article class="doc" id="doctor-{i}"><img src="{d["photo"]}" alt="{d["role"]} {d["name"]}" loading="lazy"><div><p class="role">{d["role"]}</p><h3>{d["name"]}</h3><ul>'+''.join(f'<li>{E(x)}</li>' for x in d['career'])+'</ul></div></article>' for i,d in enumerate(C['doctors']))
tr=''.join(f'<a class="card" href="/treatments/{t["id"]}.html"><h3>{t["name"]}</h3><p>{t["text"]}</p></a>' for t in C['treatments'])
hrs=''.join(f'<tr><th>{h["label"]}</th><td>{h["open"]} ~ {h["close"]}</td></tr>' for h in C['hours'])+f'<tr><th>점심시간</th><td>{C["lunch"]}</td></tr><tr><th>휴진</th><td>{C["closed"]}</td></tr>'
egal=('<div class="egal">'+''.join(f'<figure class="ecard{" contain" if g.get("fit")=="contain" else ""}"><img src="{g["image"]}" alt="{E(g.get("alt") or g["caption"])}" loading="lazy"><figcaption>{E(g["caption"])}</figcaption></figure>' for g in C.get('gallery',[]))+'</div>') if C.get('gallery') else ''
column_sec=(f'''<section class="reveal"><div class="wrap"><div class="shead"><div><p class="eyebrow">COLUMN</p><h2 class="big">최근 블로그.</h2></div><a class="tlink" href="/blog/">블로그 전체 보기 →</a></div><div class="pgrid">{''.join(card(p) for p in blog[:3])}</div></div></section>''' if blog else '')
home=head(f'일산 대화역 치과 {C["name"]} | 일산서구 보철·보존과 전문의','일산서구 대화동, 대화역 6번 출구 앞 연세아크로치과의원. 보건복지부 인증 치과보철과·치과보존과·통합치의학과 전문의 진료. 임플란트, 충치치료, 신경치료, 심미보철, 틀니, 치아미백. 화·목 야간진료, 토요일 진료.','/')+f'''
<section class="hero"><div class="wrap"><p class="eyebrow light">YONSEI ACRO DENTAL CLINIC</p><h1>처음부터 끝까지,<br><em>대표원장</em>이 책임집니다.</h1><p class="hsub">{C["intro"]}</p>{booking_box()}
<dl class="hstats"><div><dt>SPECIALIST</dt><dd>보건복지부 인증 보철과·보존과 전문의</dd></div><div><dt>LOCATION</dt><dd>3호선 대화역 6번 출구 바로 앞</dd></div><div><dt>HOURS</dt><dd>화·목 야간 20:30 · 토 14:00까지</dd></div></dl></div></section>
<section class="mission reveal"><div class="wrap two"><div><p class="eyebrow">OUR PRINCIPLE</p><h2 class="big">꼭 필요한 치료만,<br><em>정직하게</em> 권합니다.</h2></div><div class="mtext"><p>{C["treatments"][1]["text"]} 꼭 필요한 치료만 집중하여 권하며, 불필요한 치료로 어려움을 겪지 않도록 올바른 방향을 제시해드립니다.</p><a class="tlink" href="#doctors">의료진 보기 →</a></div></div></section>
<section class="cream reveal"><div class="wrap two"><div><p class="eyebrow">WHY ACRO</p><h2 class="big">연세아크로치과의<br>세 가지 진료 원칙.</h2></div><ol class="nums">'''+''.join(f'<li><span>{i+1:02d}</span><div><h3>{f["title"]}</h3><p>{f["text"]}</p></div></li>' for i,f in enumerate(C['features']))+f'''</ol></div></section>
<section class="gray reveal" id="doctors"><div class="wrap"><p class="eyebrow">OUR DOCTORS</p><h2 class="big">진료하는 <em>사람들.</em></h2><p class="lead l">연세아크로치과는 보건복지부 인증 치과보철과 전문의, 치과보존과 전문의, 통합치의학과 전문의가 진료합니다.</p><div class="docs">{docs}</div></div></section>
<section class="reveal" id="treat"><div class="wrap"><div class="shead"><div><p class="eyebrow">TREATMENTS</p><h2 class="big">진료과목.</h2></div><a class="tlink" href="/treatments/">전체 보기 →</a></div><div class="tgrid">{tr}</div></div></section>
<section class="dark reveal"><div class="wrap"><p class="eyebrow light">SPACE &amp; EQUIPMENT</p><h2 class="big">진료공간과 장비.</h2><div class="gallery"><img src="/assets/clinic/interior-1.jpg" alt="연세아크로치과 내부" loading="lazy"><img src="/assets/clinic/interior-2.jpg" alt="연세아크로치과 진료실" loading="lazy"><img src="/assets/clinic/interior-3.jpg" alt="연세아크로치과 대기실" loading="lazy"></div>{egal}<ul class="chips">'''+''.join(f'<li>{e}</li>' for e in C['equipment'])+f'''</ul></div></section>
{column_sec}
<section class="visit reveal" id="location"><div class="wrap"><p class="eyebrow">VISIT</p><h2 class="big">오시는 길 <em>· 진료시간</em></h2><div class="vgrid"><div class="vinfo">
<h3>주소</h3><p>{C["address"]}<br><span class="muted">{C["directions"]["subway"]}</span></p><p>{C["directions"]["car"]}</p>
<h3>진료시간</h3><ul class="hlist">'''+''.join(f'<li>{h["label"]} <b>{h["open"]} – {h["close"]}</b></li>' for h in C['hours'])+f'''</ul><p class="muted">평일 점심 {C["lunch"]} · {C["closed"]}</p>
<h3>실제 평가</h3><p>환자분들이 남긴 후기를 네이버·구글에서 직접 확인해 보세요.</p>
<div class="pills"><a class="pill nv" href="{L["naver_map"]}?placePath=/review" target="_blank" rel="noopener">네이버 플레이스 리뷰 →</a><a class="pill gg" href="{L["google_maps"]}" target="_blank" rel="noopener">구글 리뷰 →</a><a class="pill ol" href="tel:{C["phone"]}">전화 {C["phone"]}</a></div></div>
<div class="vmap"><div id="nmap" data-key="{C.get('naver_maps_client_id','')}" data-lat="{C['geo']['lat']}" data-lng="{C['geo']['lng']}"><a href="{L["naver_map"]}" target="_blank" rel="noopener" class="nstatic"><img src="/assets/clinic/map-static.png" alt="연세아크로치과 위치 - 대화역 6번 출구 앞 네이버 지도" loading="lazy"><span>네이버 지도에서 크게 보기 →</span></a></div><p class="maplinks"><a href="{L["naver_map"]}" target="_blank" rel="noopener">네이버 지도로 보기</a><a href="{L["google_maps"]}" target="_blank" rel="noopener">구글 지도로 보기</a></p></div></div></div></div></section>
<section class="reveal"><div class="wrap narrow"><p class="eyebrow">FAQ</p>{faq_html(BASE_FAQ)}</div></section>
'''+ld(clinic_ld(),*physician_ld(),faq_ld(BASE_FAQ),{"@context":"https://schema.org","@type":"WebSite","name":C['name'],"url":D+'/',"inLanguage":"ko-KR"})+foot()
w('index.html',home)
# ---- list pages
EMPTY='<div class="empty"><p class="eyebrow">COMING SOON</p><h2>곧 새 글이 올라올 예정입니다</h2><p>연세아크로치과 전문의가 직접 쓰는 치료 정보와 소식을 준비하고 있습니다.</p><p><a class="btn ghost" href="/faq/">자주 묻는 질문 보기</a></p></div>'
def list_page(path,title,h1,desc,items,crumb,tagfilter=True,base='/blog/posts/',cardf=card,extra_top=''):
  tags=[]; [tags.append(x) for x in [p.get('tag') or p.get('treatment') for p in items] if x not in tags]
  btn=('<div class="tags" id="tags"><button class="on">전체</button>'+''.join(f'<button>{E(t)}</button>' for t in tags)+'</div>') if tagfilter and items else ''
  pop=[p for p in items if p.get('popular')][:5] or items[:5]
  s=head(title,desc,path)+f'<div class="wrap page"><nav class="bc" aria-label="breadcrumb"><a href="/">홈</a> › {h1}</nav><h1 class="ptitle">{h1}</h1><p class="lead l">{desc}</p>{extra_top}{btn}<div class="blog-layout{'' if items else ' one'}"><div class="plist" id="list">{"".join(cardf(p) for p in items) or EMPTY}</div>'+(('<aside class="popular"><h2>인기 게시물</h2>'+''.join(f'<a href="{p.get("url") or base+p["slug"]+".html"}">{E(p["title"])}</a>' for p in pop)+'</aside>') if pop else '')+f'</div></div><script src="/js/filter.js"></script>'
  s+=ld(crumbs([('홈','/'),(h1,path)]),{"@context":"https://schema.org","@type":"CollectionPage","name":title,"url":D+path,"isPartOf":{"@id":CLINIC_ID}})+foot(); w(path.lstrip('/')+'index.html',s)
list_page('/blog/',f'일산 치과 블로그 – 치료 정보 | 대화역 {C["name"]}','블로그','일산 대화역 연세아크로치과 전문의가 설명하는 임플란트·충치·신경치료·사랑니·미백 등 치료 정보입니다.',blog,None)
def case_card(c):
  img=c.get('thumbnail') or c.get('after') or c.get('before'); th=f'<img loading="lazy" src="{img}" alt="{E(c["title"])} 대표 이미지">' if img else ''
  badge='<span class="rev">검수 필요 · 비공개(noindex)</span>' if not c['public'] else ''
  return f'<a class="pcard" data-tag="{E(c["treatment"])}" href="/cases/{c["slug"]}.html">{th}<div><span class="tag">#{E(c["treatment"])}</span>{badge}<h3>{E(c["title"])}</h3><p>치료기간: {E(str(c.get("period","")))}</p><time datetime="{c["date"]}">{c["date"].replace("-",". ")}</time></div></a>'
for c in cases: c['url']=f'/cases/{c["slug"]}.html'
list_page('/cases/',f'임상 케이스 | 일산 대화역 치과 {C["name"]}','임상 케이스','일산 대화역 연세아크로치과의 실제 진료 사례입니다. 치료 결과는 개인의 구강 상태에 따라 다를 수 있습니다.',cases,None,cardf=case_card,
  extra_top='<p class="notice">※ 본 사례는 「의료법」 제56조 및 의료광고 심의 기준에 따라 게시되며, 치료 결과는 개인에 따라 다를 수 있습니다. 부작용·주의사항은 상담 시 안내드립니다.</p>')
# ---- post pages
def doc_idx(p):
  a=str(p.get('author') or '')
  for i,d in enumerate(C['doctors']):
    if d['name'] in a: return i
  return C.get('default_author',0)
def byline(p):
  d=C['doctors'][doc_idx(p)]; return f'글·감수: <a href="/about/#doctor-{doc_idx(p)}" rel="author">{d["role"]} {d["name"]}</a> ({d["career"][0].replace("보건복지부 인증 ","")})'
def modified(p):
  u=p.get('updated')
  if u: return str(u)[:10]
  try:
    import subprocess; g=subprocess.run(['git','log','-1','--format=%cs','--',f"content/posts/{p['slug']}.md"],cwd=R,capture_output=True,text=True).stdout.strip()
    return max(g,p['date']) if g else p['date']
  except Exception: return p['date']
def related(p): return [x for x in blog if x['tag']==p['tag'] and x['slug']!=p['slug']][:3]
for p in posts:
  sec=('블로그','/blog/')
  img=p.get('thumbnail') or '/assets/brand/og-image.jpg'
  qa=p.get('faq') or []; qs=[(q['q'],q['a']) for q in qa if q.get('q')]
  s=head(f'{p["title"]} | {C["name"]}',p['summary'][:150],p['url'],img,'article')+f'''<article class="col"><nav class="bc"><a href="/">홈</a> › <a href="{sec[1]}">{sec[0]}</a></nav>
<header><a class="tag" href="{sec[1]}#{E(p["tag"])}">#{E(p["tag"])}</a><h1>{E(p["title"])}</h1><p class="meta"><time datetime="{p["date"]}">{p["date"].replace("-",". ")}</time> · {byline(p)}</p></header>
<aside class="tldr" aria-label="핵심 요약"><strong>한눈에 보기</strong><p><b>Q.</b> {E(p.get("question") or p["title"])}</p><p><b>A.</b> {E(p["summary"])}</p><p class="small">진료: {C["name"]} · {C["address"]} · {C["phone"]}</p></aside>
<div class="body">{md(p["body"])}</div>{faq_html(qs) if qs else ""}
{f'<p class="src">원문: <a href="{p["source_url"]}" target="_blank" rel="noopener">네이버 블로그</a></p>' if p.get("source_url") else ""}
<div class="cta"><p>궁금한 점은 편하게 문의하세요.</p>{booking_box()}</div>
{'<section class="rel"><h2>관련 글</h2><div class="plist">'+''.join(card(x) for x in related(p))+'</div></section>' if related(p) else ''}</article>'''
  art={"@context":"https://schema.org","@type":"BlogPosting","headline":p['title'][:110],"description":p['summary'],"datePublished":p['date'],"dateModified":modified(p),
   "image":D+img,"inLanguage":"ko-KR","mainEntityOfPage":D+p['url'],"author":{"@id":D+f'/#doctor-{doc_idx(p)}'},"publisher":{"@id":CLINIC_ID},"reviewedBy":{"@id":D+f'/#doctor-{doc_idx(p)}'},"about":{"@type":"MedicalProcedure","name":p['tag']}}
  if p.get('source_url'): art['isBasedOn']=p['source_url']
  s+=ld(art,crumbs([('홈','/'),(sec[0],sec[1]),(p['title'],p['url'])]),physician_ld()[doc_idx(p)],*( [faq_ld(qs)] if qs else []))+foot(); w(p['url'].lstrip('/'),s)
# ---- case pages
for c in cases:
  ba=''.join(f'<figure><img src="{c[k]}" alt="{lbl}"><figcaption>{lbl}</figcaption></figure>' for k,lbl in (('before','치료 전'),('after','치료 후')) if c.get(k))
  s=head(f'{c["title"]} | 임상 케이스 | {C["name"]}',c['summary'] or c['title'],c['url'],c.get('after') or c.get('before') or '/assets/clinic/interior-1.jpg','article',noindex=not c['public'])+f'''<article class="col"><nav class="bc"><a href="/">홈</a> › <a href="/cases/">임상 케이스</a></nav>
<header><span class="tag">#{E(c["treatment"])}</span><h1>{E(c["title"])}</h1><p class="meta">{c["date"].replace("-",". ")}</p></header>
{'<p class="sample">⚠️ 검수 필요: 자동 가져온 사례입니다. 전/후 사진 선정과 의료광고 심의 확인 전까지 검색엔진 비공개(noindex)입니다.</p>' if not c['public'] else ''}
<table class="hours"><tr><th>치료</th><td>{E(c["treatment"])}</td></tr><tr><th>치료기간</th><td>{E(str(c.get("period","")))}</td></tr><tr><th>참고</th><td>{E(str(c.get("notes","")))}</td></tr></table>
<div class="ba">{ba}</div><div class="body">{md(c["body"])}</div>
{f'<p><a class="btn ghost" href="{c["post"]}">관련 블로그 글 보기</a></p>' if c.get("post") else ""}
<p class="notice">※ 치료 결과는 개인의 구강 상태에 따라 다를 수 있으며, 시술 후 부기·통증·감염 등 부작용이 발생할 수 있습니다.</p><div class="cta">{booking_box()}</div></article>'''
  s+=ld(crumbs([('홈','/'),('임상 케이스','/cases/'),(c['title'],c['url'])]),{"@context":"https://schema.org","@type":"Article","headline":c['title'][:110],"datePublished":c['date'],"author":{"@id":CLINIC_ID},"publisher":{"@id":CLINIC_ID}})+foot()
  w(c['url'].lstrip('/'),s)
# ---- treatments
ti=head(f'진료과목 | 일산 대화역 치과 {C["name"]}','일산서구 대화역 연세아크로치과 진료과목: '+', '.join(t['name'] for t in C['treatments']),'/treatments/')+'<div class="wrap page"><nav class="bc"><a href="/">홈</a> › 진료과목</nav><h1 class="ptitle">진료과목</h1><div class="grid">'+tr+'</div></div>'+ld(crumbs([('홈','/'),('진료과목','/treatments/')]))+foot()
w('treatments/index.html',ti)
for t in C['treatments']:
  rel=[p for p in blog if p['tag']==t['tag']][:6]; rc=[c for c in cases if c['treatment']==t['tag'] and c['public']]
  qs=[(f"연세아크로치과에서 {t['name']} 진료를 받을 수 있나요?",f"네. {t['text']} 보건복지부 인증 전문의가 진료합니다."),
      (f"{t['name']} 상담은 어떻게 예약하나요?",f"대표전화 {C['phone']}, 네이버 예약 또는 카카오톡 채널로 예약하실 수 있습니다."),BASE_FAQ[0],BASE_FAQ[1]]
  path=f'/treatments/{t["id"]}.html'
  s=head(f'일산 대화역 {t["name"]} | {C["name"]} (일산서구 치과)',f'일산 {t["name"]} – {t["text"]} 일산서구 대화역 6번 출구 앞 연세아크로치과의원, 보건복지부 인증 전문의 진료.',path)+f'''<article class="col"><nav class="bc"><a href="/">홈</a> › <a href="/treatments/">진료과목</a> › {t["name"]}</nav><h1>{t["name"]}</h1>
<aside class="tldr"><strong>한눈에 보기</strong><p>{t["text"]}</p><p class="small">{C["name"]} · {C["address"]} · {C["phone"]}</p></aside>{faq_html(qs)}
{'<section class="rel"><h2>관련 블로그 글</h2><div class="plist">'+''.join(card(x) for x in rel)+'</div></section>' if rel else ''}
{'<section class="rel"><h2>임상 케이스</h2><div class="plist">'+''.join(case_card(x) for x in rc)+'</div></section>' if rc else ''}
<div class="cta">{booking_box()}</div></article>'''
  s+=ld(crumbs([('홈','/'),('진료과목','/treatments/'),(t['name'],path)]),faq_ld(qs),{"@context":"https://schema.org","@type":"MedicalWebPage","name":t['name'],"about":{"@type":"MedicalProcedure","name":t['name'],"description":t['text']},"publisher":{"@id":CLINIC_ID}})+foot()
  w(path.lstrip('/'),s)
# ---- about (fact sheet for search/AI)
ABOUT_QA=[
 ("연세아크로치과의원은 어떤 치과인가요?",f"{C['name']}({C['name_en']})은 {C['address']}에 있는 치과의원입니다. {C['directions']['subway']}에 위치하며, 보건복지부 인증 치과보철과·치과보존과·통합치의학과 전문의가 진료합니다."),
 ("의료진은 누구인가요?"," ".join(f"{d['role']} {d['name']}: {', '.join(d['career'])}." for d in C['doctors'])),
 ("어떤 진료를 하나요?",", ".join(t['name'] for t in C['treatments'])+"를 진료합니다."),
 ("임플란트는 어떻게 진행하나요?",C['features'][1]['text']+" "+C['features'][2]['text']),
 ("진료시간은 어떻게 되나요?",BASE_FAQ[0][1]),
 ("야간진료나 토요일 진료를 하나요?","화요일·목요일은 20:30까지 야간진료, 토요일은 09:30~14:00(점심시간 없음) 진료합니다. 일요일·공휴일은 휴진입니다."),
 ("어떻게 찾아가나요?",f"지하철: {C['directions']['subway']}. 버스: {C['directions']['bus']}."),
 ("주차가 되나요?",C['directions']['car']+"합니다."),
 ("전화번호와 예약 방법은?",f"대표전화 {C['phone']}. 네이버 예약({L['naver_booking']}) 또는 카카오톡 채널({L['kakao_channel']})로 예약·상담할 수 있습니다."),
 ("어떤 장비를 갖추고 있나요?",", ".join(C['equipment'])+"를 갖추고 있습니다."),
]
dl=''.join(f'<section class="fact" id="doctor-{i}"><h3>{d["role"]} {d["name"]}</h3><ul>'+''.join(f'<li>{E(x)}</li>' for x in d['career'])+'</ul></section>' for i,d in enumerate(C['doctors']))
facts=(f"<table class=\"hours\"><tr><th>병원명</th><td>{C['name']} ({C['name_en']})</td></tr><tr><th>주소</th><td>{C['address']}</td></tr><tr><th>위치</th><td>{C['directions']['subway']}</td></tr><tr><th>대표전화</th><td><a href=\"tel:{C['phone']}\">{C['phone']}</a></td></tr>"
 +''.join(f"<tr><th>{h['label']}</th><td>{h['open']} ~ {h['close']}</td></tr>" for h in C['hours'])
 +f"<tr><th>점심시간</th><td>{C['lunch']}</td></tr><tr><th>휴진</th><td>{C['closed']}</td></tr><tr><th>주차</th><td>{C['directions']['car']}</td></tr><tr><th>대표자</th><td>{C['ceo']} (사업자등록번호 {C['biz_no']})</td></tr><tr><th>진료과목</th><td>{', '.join(t['name'] for t in C['treatments'])}</td></tr></table>")
ab=head(f'병원 정보 한눈에 보기 | 일산 대화역 치과 {C["name"]}',f'{C["name"]} 기본 정보: 주소 {C["address"]}, 전화 {C["phone"]}, 진료시간, 의료진(치과보철과·치과보존과 전문의), 진료과목, 주차·교통 안내.','/about/')
ab+=f'<article class="col"><nav class="bc"><a href="/">홈</a> › 병원 정보</nav><h1>연세아크로치과의원 병원 정보</h1><aside class="tldr"><strong>요약</strong><p>{ABOUT_QA[0][1]}</p></aside><h2>기본 정보</h2>{facts}<h2>의료진</h2>{dl}{faq_html(ABOUT_QA)}<div class="cta">{booking_box()}</div></article>'
ab+=ld(clinic_ld(),*physician_ld(),faq_ld(ABOUT_QA),crumbs([('홈','/'),('병원 정보','/about/')]),{"@context":"https://schema.org","@type":"AboutPage","name":"연세아크로치과의원 병원 정보","url":D+'/about/',"about":{"@id":CLINIC_ID},"dateModified":datetime.date.today().isoformat()})+foot()
w('about/index.html',ab)
w('404.html',head(f'페이지를 찾을 수 없습니다 | {C["name"]}','요청하신 페이지를 찾을 수 없습니다.','/404.html',noindex=True)+'<div class="wrap page" style="text-align:center"><p class="eyebrow" style="justify-content:center">404</p><h1 class="ptitle">페이지를 찾을 수 없습니다</h1><p class="lead" style="margin:0 auto 30px">주소가 바뀌었거나 삭제된 페이지입니다.</p><p><a class="btn" href="/">홈으로</a> <a class="btn ghost" href="/blog/">블로그</a> <a class="btn ghost" href="/about/">병원 정보</a></p></div>'+foot())
# ---- FAQ page (data/faq.json, CMS 편집 가능)
FAQ=json.load(open(f'{R}/data/faq.json'))['groups']
seen=set(); fqs=[]
for gp in FAQ:
  gp['items']=[x for x in gp['items'] if x.get('q') and x['q'] not in seen and not seen.add(x['q'])]; fqs+= [(x['q'],x['a']) for x in gp['items']]
nav=''.join(f'<a class="pill ol" href="#faq-{i}">{E(g["category"])}</a>' for i,g in enumerate(FAQ) if g['items'])
body=''.join(f'<section class="faq" id="faq-{i}"><h2>{E(g["category"])}</h2>'+''.join(f'<details><summary>{E(x["q"])}</summary><p>{E(x["a"])}</p></details>' for x in g['items'])+'</section>' for i,g in enumerate(FAQ) if g['items'])
alltxt=' '.join(q+' '+a for q,a in fqs)
chips=''.join(f'<button type="button" class="chipq">{k}</button>' for k in ['진료시간','야간진료','예약','주차','지하철','임플란트','충치치료','신경치료','사랑니','치아미백','의료진'] if k in alltxt)
fp=head(f'자주 묻는 질문(FAQ) | 일산 대화역 치과 {C["name"]}',f'연세아크로치과의원 FAQ: 진료시간·야간진료·예약·주차·교통, 의료진, 진료과목 등 자주 묻는 질문 {len(fqs)}개에 답합니다.','/faq/')
fp+=f'<div class="wrap page narrow"><nav class="bc"><a href="/">홈</a> › FAQ</nav><h1 class="ptitle">자주 묻는 질문</h1><p class="lead l">진료시간, 예약, 위치, 의료진, 진료과목에 대해 자주 묻는 질문입니다. 더 궁금한 점은 전화({C["phone"]})나 카카오톡으로 문의해 주세요.</p><div class="fsearch" role="search"><label for="fq" class="sr">FAQ 검색</label><input id="fq" type="search" placeholder="궁금한 내용을 검색해보세요 (예: 주차, 임플란트)" autocomplete="off"><button type="button" id="fqx" aria-label="검색어 지우기" hidden>×</button></div><div class="chipsq">{chips}</div><p id="fqn" class="muted" aria-live="polite"></p><div class="pills" style="margin-bottom:40px">{nav}</div><div id="fqbody">{body}</div><div id="fqempty" class="empty" hidden><h2>검색 결과가 없습니다</h2><p>찾으시는 내용이 없다면 편하게 문의해 주세요.</p>{booking_box()}</div></div><script src="/js/faq.js" defer></script>'
fp+=ld(faq_ld(fqs),crumbs([('홈','/'),('FAQ','/faq/')]))+foot()
w('faq/index.html',fp)
# ---- sitemap / llms
urls=['/','/about/','/faq/','/treatments/','/blog/','/cases/']+[f'/treatments/{t["id"]}.html' for t in C['treatments']]+[p['url'] for p in posts]+[c['url'] for c in cases if c['public']]
lm={p['url']:modified(p) for p in posts}
w('sitemap.xml','<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+''.join(f'<url><loc>{D}{u}</loc>{"<lastmod>"+lm[u]+"</lastmod>" if u in lm else ""}</url>\n' for u in urls)+'</urlset>\n')
w('robots.txt','User-agent: *\nAllow: /\nDisallow: /admin/\n\n'+''.join(f'User-agent: {b}\nAllow: /\nDisallow: /admin/\n\n' for b in ['GPTBot','OAI-SearchBot','ChatGPT-User','ClaudeBot','Claude-Web','PerplexityBot','Google-Extended','Applebot-Extended','Yeti','Bingbot','CCBot'])+f'Sitemap: {D}/sitemap.xml\n')
llms=f"""# {C['name']} ({C['name_en']})

> 경기도 고양시 일산서구 대화동, 3호선 대화역 6번 출구 바로 앞 롯데리아 건물 5층에 위치한 치과의원. 보건복지부 인증 치과보철과·치과보존과·통합치의학과 전문의가 진료합니다.

## 기본 정보
- 주소: {C['address']}
- 대표전화: {C['phone']}
- 진료시간: {HOURS_TXT} / 점심 {C['lunch']} / {C['closed']}
- 주차: {C['directions']['car']}
- 예약: 네이버 예약 {L['naver_booking']} · 카카오톡 채널 {L['kakao_channel']}
- 지도: 네이버 {L['naver_map']} · Google {L['google_maps']}

## 의료진
"""+''.join(f"- {d['role']} {d['name']}: {', '.join(d['career'][:3])}\n" for d in C['doctors'])+"\n## 진료과목\n"+''.join(f"- [{t['name']}]({D}/treatments/{t['id']}.html): {t['text']}\n" for t in C['treatments'])+"\n## 블로그 (치료 정보)\n"+''.join(f"- [{p['title']}]({D}{p['url']}) ({p['date']})\n" for p in blog[:15])+"\n## 임상 케이스\n"+''.join(f"- [{c['title']}]({D}{c['url']}) ({c['date']})\n" for c in cases if c['public'])
llms=re.sub(r'\n## [^\n]+\n(?=\n## |\s*$)','\n',llms)
llms=llms.replace('## 기본 정보','## 병원 정보 페이지\n- '+D+'/about/ (사실 정보 요약, Q&A)\n- 전체 텍스트: '+D+'/llms-full.txt\n\n## 기본 정보',1)
w('llms.txt',llms)
full=llms+'\n\n# 자주 묻는 질문\n'+''.join(f'\nQ. {q}\nA. {a}\n' for q,a in fqs)+'\n\n# 진료과목 상세\n'+''.join(f"\n## {t['name']}\n{t['text']}\nURL: {D}/treatments/{t['id']}.html\n" for t in C['treatments'])
def plain(b): return re.sub(r'!\[[^\]]*\]\([^)]*\)\n*','',b).strip()
for title,items in (('블로그',blog),('임상 케이스',[c for c in cases if c['public']])):
  if items: full+=f'\n\n# {title}\n'+''.join(f"\n## {p['title']}\nURL: {D}{p['url']}\n작성일: {p['date']}\n요약: {p['summary']}\n\n{plain(p['body'])}\n" for p in items)
w('llms-full.txt',full)

rd=[f'{u} {x["url"]} 301' for x in posts+cases for u in (x.get('redirect_from') or [])]
w('_redirects','\n'.join(rd)+'\n')
print(f'built: {len(blog)} blog, {len(cases)} cases')
