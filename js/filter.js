(()=>{const T=document.getElementById('tags');if(!T)return;const cards=[...document.querySelectorAll('#list .pcard')];
const show=t=>{cards.forEach(c=>c.hidden=!(t==='전체'||c.dataset.tag===t));[...T.children].forEach(b=>b.classList.toggle('on',b.textContent===t));history.replaceState(null,'',t==='전체'?location.pathname:'#'+encodeURIComponent(t))};
T.onclick=e=>e.target.tagName==='BUTTON'&&show(e.target.textContent);const h=decodeURIComponent(location.hash.slice(1));if([...T.children].some(b=>b.textContent===h))show(h)})();
