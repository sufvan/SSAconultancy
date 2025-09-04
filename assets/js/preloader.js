
(function(){
  var ov = document.createElement('div');
  ov.className = 'preload-overlay';
  ov.innerHTML = '<img src="/assets/img/02.svg" alt="loading"/>';
  document.addEventListener('DOMContentLoaded', function(){
    document.body.appendChild(ov);
  });
  window.addEventListener('load', function(){
    setTimeout(function(){ ov.classList.add('hide'); setTimeout(function(){ ov.remove(); }, 400); }, 150);
  });
})();
