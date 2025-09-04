
async function fetchWithFallback(primary, fallback) {
  try {
    const r = await fetch(primary, {cache:'no-store'});
    if (!r.ok) throw new Error(r.status);
    return await r.json();
  } catch (e) {
    if (!fallback) throw e;
    const r2 = await fetch(fallback, {cache:'no-store'});
    return await r2.json();
  }
}


document.addEventListener('DOMContentLoaded', async () => {
  const target = document.querySelector('#clients-grid');
  if (!target) return;
  try{
    const res = await fetch('/api/clients.json', {cache:'no-cache'});
    const data = await res.json();
    target.innerHTML = '';
    if(!data.items || !data.items.length){
      target.innerHTML = '<div class="muted">No clients added yet.</div>';
      return;
    }
    for(const c of data.items){
      const card = document.createElement('div');
      card.className = 'client-card';
      card.innerHTML = `
        <div class="client-logo"><img src="${c.image || '/assets/img/placeholder.svg'}" alt="${c.name}"/></div>
        <div class="client-info">
          <div class="client-name">${c.name}</div>
          <div class="client-meta">${[c.industry||'', c.city||''].filter(Boolean).join(' • ')}</div>
          ${c.website ? `<a class="btn btn-sm" href="${c.website}" target="_blank" rel="noopener">Visit</a>` : ''}
        </div>`;
      target.appendChild(card);
    }
  }catch(e){
    console.error('clients load error', e);
    target.innerHTML = '<div class="muted">Failed to load clients.</div>';
  }
});
