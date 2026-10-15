(()=>{const h=document.querySelector('header.site');const f=()=>h&&h.classList.toggle('scrolled',scrollY>40);addEventListener('scroll',f,{passive:true});f();
const io='IntersectionObserver'in window?new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target)}}),{threshold:.12}):null;
document.querySelectorAll('.reveal').forEach(el=>io?io.observe(el):el.classList.add('in'))})();
