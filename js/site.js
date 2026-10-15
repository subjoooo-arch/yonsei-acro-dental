(()=>{const h=document.querySelector('header.site');const f=()=>h&&h.classList.toggle('scrolled',scrollY>40);addEventListener('scroll',f,{passive:true});f();
const io='IntersectionObserver'in window?new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target)}}),{threshold:.12}):null;
document.querySelectorAll('.reveal').forEach(el=>io?io.observe(el):el.classList.add('in'))})();
(()=>{const m=document.getElementById('nmap');if(!m)return;const k=m.dataset.key;if(!k||k.startsWith('['))return;
const s=document.createElement('script');s.src='https://oapi.map.naver.com/openapi/v3/maps.js?ncpKeyId='+encodeURIComponent(k);
s.onload=()=>{try{const p=new naver.maps.LatLng(+m.dataset.lat,+m.dataset.lng);m.innerHTML='';m.classList.add('live');const map=new naver.maps.Map(m,{center:p,zoom:17});new naver.maps.Marker({position:p,map})}catch(e){}};document.head.appendChild(s)})();
