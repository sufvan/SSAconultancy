
async function fetchJSON(u){ const r=await fetch(u); if(!r.ok) throw new Error('Fetch failed'); return await r.json(); }
function esc(s){ return (s??'').toString().replace(/[&<>"']/g, m=>({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[m])); }
function fmtDate(d){ try{ const x=new Date(d); return x.toLocaleString(); }catch(e){ return d; } }
function card(x){
  return `<article class="card">
    <div class="head">
      <div class="ver">${esc(x.title)} ${x.version?`<span class="subtle">(${esc(x.version)})</span>`:''}</div>
      <div class="date">${fmtDate(x.release_date)}</div>
    </div>
    <div class="subtle" style="margin:8px 0">${x.software_name?esc(x.software_name):'General'}</div>
    <div class="note">${esc(x.content||'')}</div>
  </article>`;
}
(async ()=>{
  const root=document.getElementById('rel-root');
  try{
    const data = await fetchJSON('/api/releases.json');
    root.innerHTML = data.items.length ? data.items.map(card).join('') : '<p class="subtle">No releases yet.</p>';
  }catch(e){
    root.innerHTML = '<p class="subtle">Failed to load releases.</p>';
  }
})();
