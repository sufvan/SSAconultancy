
(async function(){
  try{
    const r = await fetch('/api/software.json', {cache:'no-store'});
    if(!r.ok) return;
    const data = await r.json();
    const all = (data.items||[]).filter(x=>x.is_active!==false);
    const esc = s=>String(s||'').replace(/[&<>"]/g, m=>({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;' }[m]));
    const money = n=> n==null? '' : 'PKR '+ Number(n).toLocaleString();

    // --- DOWNLOAD: show only FREE software ---
    // --- DOWNLOAD: show only FREE software ---
const dRoot = document.getElementById('download-root');
if (dRoot) {
  const items = all.filter(x => x.is_free === true);
  dRoot.innerHTML = items.length ? items.map((x, idx) => {
    const esc = s => String(s || '').replace(/[&<>"]/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));
    const id = `dl_${x.id || idx}`;
    const imgs = [x.image, ...(Array.isArray(x.gallery) ? x.gallery : [])].filter(Boolean);
    const actions = `<a class="btn" href="${esc(x.download_url || '#')}">Download Free</a>`;

    return `
      <div class="card" style="display:grid;grid-template-columns:1.1fr .9fr;gap:24px;align-items:start;">
        <div>
          <div style="height:220px;display:flex;align-items:center;justify-content:center;background:#fff;border:1px solid rgba(2,6,23,.08);border-radius:16px;padding:10px;">
            ${imgs.length ? `<img id="${id}_main" src="${esc(imgs[0])}" alt="${esc(x.name)}" style="max-width:100%;max-height:100%;object-fit:contain;">` : ''}
          </div>
          ${imgs.length > 1 ? `
            <div style="display:flex;gap:8px;margin-top:10px;flex-wrap:wrap;">
              ${imgs.map((u,i)=>`
                <img src="${esc(u)}" alt="" style="width:72px;height:60px;object-fit:cover;cursor:pointer;opacity:${i===0?1:.85};border:1px solid rgba(2,6,23,.1);border-radius:10px;background:#fff;"
                     onclick="document.getElementById('${id}_main').src='${esc(u)}'">
              `).join('')}
            </div>
          ` : ''}
        </div>

        <div>
          <h3 style="margin:0 0 6px 0;">${esc(x.name)}</h3>
          ${x.description ? `<p class="subtle" style="margin:0 0 10px 0;">${esc(x.description)}</p>` : ''}
          <div style="margin-top:12px;display:flex;gap:10px;flex-wrap:wrap;">
            ${actions}
          </div>
          <div class="badge-soft" style="margin-top:12px;">
            ${esc(x.category || 'Software')}
          </div>
        </div>
      </div>
    `;
  }).join('') : '<p class="subtle">No free downloads right now.</p>';
}


    // --- PRICING: show only PAID software ---
    // --- PRICING: show only PAID software ---
const pRoot = document.getElementById('pricing-root');
if (pRoot) {
  const items = all.filter(x => x.is_free !== true);

  pRoot.innerHTML = items.length ? items.map((x, idx) => {
    const esc = s => String(s || '').replace(/[&<>"]/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));
    const money = n => n == null ? '' : 'PKR ' + Number(n).toLocaleString();

    // gallery support (x.gallery = ['url1','url2',...]) — agar na ho to sirf main image
    const id = `pc_${x.id || idx}`;
    const imgs = [x.image, ...(Array.isArray(x.gallery) ? x.gallery : [])].filter(Boolean);

    return `
      <div class="card price-card">
        <div class="media">
          <div class="main">
            ${imgs.length ? `<img id="${id}_main" src="${esc(imgs[0])}" alt="${esc(x.name)}">` : ''}
          </div>
          ${imgs.length ? `
            <div class="thumbs">
              ${imgs.map((u,i)=>`<img class="${i===0?'active':''}" data-target="${id}_main" src="${esc(u)}" alt="">`).join('')}
            </div>` : ''}
        </div>

        <div class="details">
          <h3 class="ttl">${esc(x.name)}</h3>
          ${x.description ? `<p class="subtle">${esc(x.description)}</p>` : ''}

          <div class="price-row">
            <div class="price-big">${money(x.price_one_time)} <span class="subtle">/ one-time</span></div>
            ${x.price_yearly ? `<div class="yearly subtle"><strong>Yearly:</strong> ${money(x.price_yearly)} /year</div>` : ''}
          </div>

          <div class="actions">
            <a class="btn" data-payment-link="${esc(x.payment_link_onetime||'#')}">Buy One-Time</a>
            <a class="btn btn-outline" data-payment-link="${esc(x.payment_link_yearly||'#')}">Buy Yearly</a>
          </div>

          <div class="badge-soft cat">${esc(x.category || 'Software')}</div>
        </div>
      </div>
    `;
  }).join('') : '<p class="subtle">No paid products configured.</p>';

  // thumbs → main swap
  pRoot.querySelectorAll('.thumbs img').forEach(img => {
    img.addEventListener('click', e => {
      const t = e.currentTarget;
      const main = document.getElementById(t.dataset.target);
      if (main) main.src = t.src;
      t.parentElement.querySelectorAll('img').forEach(x => x.classList.remove('active'));
      t.classList.add('active');
    });
  });
}


    // --- PRODUCTS: show only PAID software with big image + slug + description ---
    const prodRoot = document.getElementById('products-root');
    if(prodRoot){
      const items = all.filter(x=>x.is_free!==true);
      prodRoot.innerHTML = items.length ? items.map(x=>{
        return `<article class="card product-xxxl">
          ${x.image?`<img class="thumb-xxxl" src="${esc(x.image)}" alt="${esc(x.name)}"/>`:''}
          <div class="meta">
            <div class="badge-soft">${esc(x.category||'Software')}</div>
            <h3>${esc(x.name)}</h3>
            <div class="small muted" title="slug">@${esc(x.slug||'')}</div>
            <p class="subtle">${esc(x.description||'')}</p>
          </div>
        </article>`;
      }).join('') : '<p class="subtle">No paid products yet.</p>';
    }

  }catch(e){ console.warn(e); }
})();


// ----- PRODUCTS HERO SLIDER (top 4 paid) -----
(function(){
  const host = document.getElementById('products-hero');
  if(!host) return;
  const esc = s=>String(s||'').replace(/[&<>"]/g, m=>({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;' }[m]));
  const money = n=> n==null? '' : 'PKR '+ Number(n).toLocaleString();

  fetch('/api/software.json',{cache:'no-store'}).then(r=>r.json()).then(data=>{
    const all = (data.items||[]).filter(x=>x.is_active!==false && x.is_free!==true);
    // sort desc by sort_order then id
    const paidTop = all.sort((a,b)=> (b.sort_order||0)-(a.sort_order||0) || (b.id||0)-(a.id||0)).slice(0,4);

    if(!paidTop.length){ host.remove(); return; }

    const slides = paidTop.map((x,i)=>`
      <article class="slide${i===0?' active':''}">
        <div class="slide-grid">
          <div class="copy">
            <h2>${esc(x.name)}</h2>
            <p class="subtle">${esc(x.description||'')}</p>
            <div class="cta">
              <a class="btn" href="/pricing.html">View Pricing</a>
              ${x.download_url?`<a class="btn btn-outline" href="${esc(x.download_url)}">Learn More</a>`:''}
            </div>
          </div>
          <div class="art">
            ${x.image?`<img class="hero-img" src="${esc(x.image)}" alt="${esc(x.name)}">`:""}
          </div>
        </div>
      </article>
    `).join('');

    host.innerHTML = `
      <div class="slides">${slides}</div>
      <button class="nav prev" aria-label="Previous">&#10094;</button>
      <button class="nav next" aria-label="Next">&#10095;</button>
      <div class="dots">${paidTop.map((_,i)=>`<button class="dot${i===0?' active':''}" data-i="${i}"></button>`).join('')}</div>
    `;

    let idx = 0, N = paidTop.length, timer;
    const go = (i)=>{
      idx = (i+N)%N;
      host.querySelectorAll('.slide').forEach((el,k)=> el.classList.toggle('active', k===idx));
      host.querySelectorAll('.dot').forEach((el,k)=> el.classList.toggle('active', k===idx));
    };
    const next = ()=> go(idx+1);
    const prev = ()=> go(idx-1);

    host.querySelector('.next').addEventListener('click', next);
    host.querySelector('.prev').addEventListener('click', prev);
    host.querySelectorAll('.dot').forEach(d=> d.addEventListener('click', e=> go(+e.currentTarget.dataset.i)));

    const start = ()=> timer = setInterval(next, 6000);
    const stop = ()=> timer && clearInterval(timer);
    host.addEventListener('mouseenter', stop);
    host.addEventListener('mouseleave', start);
    start();

    document.addEventListener('keydown', (e)=>{
      if(e.key==='ArrowRight') next();
      if(e.key==='ArrowLeft') prev();
    }, {passive:true});
  }).catch(()=>{});
})();
