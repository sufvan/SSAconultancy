
document.addEventListener('click', function(e){
  const t = e.target;
  if(t.matches('[data-toggle="pw"]')){
    const inp = document.getElementById(t.getAttribute('data-target'));
    if(!inp) return;
    inp.type = (inp.type === 'password') ? 'text' : 'password';
    t.setAttribute('aria-pressed', t.getAttribute('aria-pressed')==='true' ? 'false':'true');
  }
});

// simple table search
const search = document.getElementById('search');
if(search){
  search.addEventListener('input', function(){
    const q = this.value.toLowerCase();
    document.querySelectorAll('tbody tr[data-row]').forEach(tr => {
      tr.style.display = tr.textContent.toLowerCase().includes(q) ? '' : 'none';
    });
  });
}
