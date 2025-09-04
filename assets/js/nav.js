
(function(){
  function buildNavHTML(){
    const links = [
      ["index.html","Home"],
      ["products.html","Products"],
      ["download.html","Download"],
      ["pricing.html","Pricing"],
      ["/releases.html","Release Notes"],
      ["clients.html","Our Clients"],
      ["known-issues.html","Known Issues"],
      ["about.html","About"],
      ["contact.html","Contact Us"]
    ];
    const cur = location.pathname.split('/').pop() || 'index.html';
    return links.map(([href,label])=>`<a href="${href}" class="${cur===href?'active':''}">${label}</a>`).join(' ');
  }
  document.addEventListener('DOMContentLoaded', function(){
    var nav = document.querySelector('nav.nav-links');
    if(nav){ nav.innerHTML = buildNavHTML(); }
  });
})();
