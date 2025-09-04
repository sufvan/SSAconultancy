
async function fetchJSON(u){ const r=await fetch(u); if(!r.ok) throw new Error('Fetch failed'); return await r.json(); }
function esc(s){ return (s??'').toString().replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m])); }
function pill(st){ const cls = st==='Open'?'pill red':(st==='Fixed'?'pill green':'pill amber'); return `<span class="${cls}">${esc(st||'Open')}</span>`; }
function card(x){
  return `<details class="card"><summary>${esc(x.title)} ${pill(x.status)}</summary><div class="note">${(x.content||'').replace(/\n/g,'<br/>')}</div></details>`;
}
(async ()=>{
  const root = document.getElementById('issues-root');
  try{
    const data = await fetchJSON('/api/known_issues.json');
    root.innerHTML = (data.items||[]).length ? data.items.map(card).join('') : '<p class="subtle">No issues yet.</p>';
  }catch(e){ console.error(e); root.innerHTML='<p class="subtle">Failed to load issues.</p>'; }
})();
