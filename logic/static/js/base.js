function showToast(msg, duration = 5000) {
  document.getElementById('toast-body').textContent = msg;
  const el = document.getElementById('app-toast');
  const t = bootstrap.Toast.getOrCreateInstance(el, { delay: duration, autohide: true });
  t.show();
}


const btn = document.getElementById('lang');

console.log(':( :( :( :( :( :( :( :(');

btn.addEventListener('click', async () => {
  console.log(':( :( :( :( :( :( :( :(');
})