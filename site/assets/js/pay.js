document.addEventListener('click', function(e){
  var btn = e.target.closest('[data-payment-link]');
  if(!btn) return;
  var url = btn.getAttribute('data-payment-link');
  if(!url || url==='#'){ alert('Set data-payment-link to your checkout URL'); return; }
  location.href = url;
});