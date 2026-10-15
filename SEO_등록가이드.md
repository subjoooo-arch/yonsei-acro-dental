# 검색엔진·AI 검색 등록 가이드 (연세아크로치과)

## 0. 사이트 주소 설정 (한 곳만 수정)
`data/clinic.json`의 `"site_url"` 이 모든 canonical·OG·sitemap·robots·llms.txt·JSON-LD 주소의 기준입니다.
현재: `https://yonseiacro-preview.netlify.app` → 도메인 구매·연결 후 `"https://www.새도메인.com"`으로 **이 한 줄만** 바꾸고 커밋하면 자동 반영됩니다.
(도메인 변경 시 아래 1~3번을 새 도메인으로 다시 등록하고, Netlify에서 기존 주소 → 새 도메인 리디렉트가 자동 적용되는지 확인)

## 1. 네이버 서치어드바이저
1. https://searchadvisor.naver.com 접속 → 네이버 아이디 로그인 → 웹마스터 도구
2. 사이트 등록에 사이트 주소 입력 (예: https://yonseiacro-preview.netlify.app)
3. 소유확인 방법 **HTML 태그** 선택 → `<meta name="naver-site-verification" content="XXXX">` 의 **content 값(XXXX)** 만 복사
4. 그 값을 `data/clinic.json`의 `"naver_verification"`에 넣고 커밋(또는 CMS 병원 정보에서 입력) → 배포 후 **소유확인** 클릭
5. 요청 → **사이트맵 제출**: `https://사이트주소/sitemap.xml`
6. 요청 → **RSS 제출**(선택) 생략 가능 / **웹 페이지 수집 요청**: 홈, /about/, /blog/ 등 주요 URL 입력
7. 검증 → robots.txt 확인

## 2. Google Search Console
1. https://search.google.com/search-console → **URL 접두어** 속성에 사이트 주소 입력
2. 확인 방법 **HTML 태그** → `content="YYYY"` 값만 복사 → `"google_verification"`에 입력 → 배포 후 **확인**
   (도메인 구매 후에는 '도메인' 속성 + DNS TXT 방식 권장)
3. 색인 → Sitemaps → `sitemap.xml` 제출
4. 상단 URL 검사창에 홈/주요 글 URL 입력 → **색인 생성 요청**
5. Google 비즈니스 프로필(지도)에 웹사이트 주소 등록 (이미 Google 지도 장소 있음: place_id ChIJF5lYybOFfDUR36dHtXviqu0)

## 3. Bing 웹마스터 도구 (ChatGPT 검색·Copilot 노출용)
1. https://www.bing.com/webmasters → 로그인 → **Google Search Console에서 가져오기**(가장 쉬움) 또는 수동 추가
2. 수동 시 HTML 메타 태그 `msvalidate.01`의 content 값 → `"bing_verification"`에 입력 → 배포 후 확인
3. Sitemaps에 `sitemap.xml` 제출, **IndexNow** 사용 권장(URL 제출)

## 4. 네이버 플레이스 / 기타
- 네이버 스마트플레이스(https://smartplace.naver.com)에서 홈페이지 URL을 이 사이트로 등록
- 카카오맵 장소 정보에도 홈페이지 URL 등록

## 5. GEO(생성형 AI 검색) 관련 파일
- `/llms.txt` (요약), `/llms-full.txt` (전체 텍스트), `/about/` (병원 정보 Q&A) — 빌드 시 자동 생성
- robots.txt에서 GPTBot, OAI-SearchBot, ClaudeBot, PerplexityBot, Google-Extended, Yeti(네이버) 등 허용
- 글 작성 시 `summary`(질문에 대한 1~2문장 답), `faq`를 채우면 AI 답변 인용 확률이 높아집니다.
- 글 작성자(`author`)에 의료진 이름(황주섭/김안나)을 쓰면 해당 의사가 글·감수자로 표시됩니다. 비우면 대표원장으로 표시됩니다.
