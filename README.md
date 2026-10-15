# 연세아크로치과의원 홈페이지 (정적 사이트 + Decap CMS)

## 구조
- `data/clinic.json`: 병원 정보(주소·전화·진료시간·의료진·진료과목·링크·검색 인증코드). 출처: yonseiacro.com
- `content/posts/*.md`: 블로그 · `content/news/*.md`: 치과 소식 (각 글은 한 섹션에만; 옮긴 글은 `redirect_from`으로 _redirects 자동 생성)
- `content/cases/*.md`: 임상 케이스 (전/후 사진, 치료, 기간, 참고사항)
- `content/_templates/`: 새 글/케이스 템플릿
- `scripts/build.py`: md → HTML, `blog/posts.json`, `cases/cases.json`, `sitemap.xml`, `robots.txt`, `llms.txt`, JSON-LD 생성
- `scripts/import_naver.py`: 네이버 블로그 글 복사 (본문·날짜·이미지 로컬 저장·태그 자동지정)
- `admin/`: Decap CMS 관리자 (/admin/, noindex)
※ HTML 파일은 생성물입니다. 직접 고치지 말고 content/data를 수정한 뒤 빌드하세요.

## 로컬 빌드·확인
```
pip install -r requirements.txt
python3 scripts/build.py
python3 -m http.server 8000   # http://localhost:8000
```

## 새 글 추가 (3가지 방법)
1. **관리자 페이지**: `https://도메인/admin/` 로그인 → 블로그 / 치과 소식 / 임상 케이스 → 새로 만들기 → 저장 → 검토 → 게시. 게시하면 자동 빌드됩니다.
2. **네이버 블로그에서 복사**: `python3 scripts/import_naver.py https://blog.naver.com/yonseiacro/글번호` (또는 `--rss` 로 최신 글 전체). 제목에 '사례/케이스'가 있으면 임상 케이스 초안도 생성됩니다. 이후 `build.py`.
3. **직접 작성**: `content/_templates/post.md`를 `content/posts/`에 복사해 수정.
태그를 새로 쓰면 필터 버튼이 자동 생성됩니다. `summary`는 검색·AI 답변에 그대로 쓰이므로 질문에 대한 답 1~2문장으로 쓰세요.

## 배포
### Netlify (권장, 관리자 로그인 가장 쉬움)
1. 이 폴더를 GitHub 저장소에 push → Netlify에서 Import (netlify.toml에 빌드 설정 포함)
2. Site settings → Identity 활성화 → Registration을 **Invite only** → Services → **Git Gateway 활성화**
3. Identity → Invite users로 원장님/직원 이메일 초대 → 메일 링크로 비밀번호 설정 → `/admin/` 로그인
### Cloudflare Pages
빌드 명령 `pip install -r requirements.txt && python3 scripts/build.py`, 출력 디렉터리 `/`. 관리자 로그인은 Netlify Identity를 쓸 수 없으므로 `admin/config.yml`에서 `github` 백엔드로 바꾸고 GitHub OAuth 앱 + OAuth 프록시(예: decap-proxy Worker)를 설정해야 합니다.
### 도메인 연결 후
`data/clinic.json`의 `domain`을 실제 주소로, `verification`에 네이버 서치어드바이저·구글 서치콘솔 코드를 넣고 빌드. 두 곳에 `sitemap.xml` 제출.

## ⚠️ 의료광고법 주의 (반드시 확인)
- 의료법 제56조: 치료 전·후 사진, 치료경험담, 과장·비교 광고 등은 제한되며, 홈페이지/블로그 내용도 의료광고 심의(대한치과의사협회 의료광고심의위원회) 대상이 될 수 있습니다.
- 임상 케이스는 자동 가져온 3건 모두 `review_required: true`로 **검색엔진 noindex·사이트맵 제외** 상태입니다. 전/후 사진은 자동으로 첫/마지막 이미지를 넣은 것이므로 원장님이 직접 선정하고, 부작용·주의사항 기재와 심의 여부를 확인한 뒤 `review_required: false`로 바꾸세요. 환자 식별 가능 사진은 동의서 필수.
- 네이버 블로그 원문을 그대로 옮긴 글도 같은 기준으로 검토하세요. (네이버 블로그와 본문이 중복되면 검색 노출이 나뉠 수 있으니 장기적으로는 요약·재작성 권장)

## 남은 확인 항목
`[도메인]`, 네이버/구글 인증코드, 우편번호, 인스타그램 URL, 임상 케이스 치료기간, GitHub 저장소(OAuth 사용 시).

## 지도 (네이버 지도)
네이버 지도 페이지는 iframe 삽입을 막고 있어서(X-Frame-Options: DENY) 기본으로는 **네이버 정적 지도 이미지**(`assets/clinic/map-static.png`, 클릭 시 네이버 지도 플레이스로 이동)를 보여줍니다.
움직이는 지도를 원하면: 네이버 클라우드 플랫폼 → AI·NAVER API → Maps(Dynamic Map) 앱 등록 → 서비스 URL에 실제 도메인과 `*.netlify.app` 등록 → 발급된 **Client ID**를 `data/clinic.json`의 `naver_maps_client_id`에 넣고 빌드. 그러면 `js/site.js`가 Naver Maps JS API v3를 불러와 지도+마커로 바꿉니다.
