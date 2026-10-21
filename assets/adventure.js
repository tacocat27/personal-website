// Shared by the pages in adventures/.

// Hover does the unit swap in CSS; touch has no hover, so a tap on the stats
// row latches the same state.
document.addEventListener('click', function (e) {
  const stats = e.target.closest('.adv-stats');
  if (stats) stats.classList.toggle('metric');
});

(function () {
  const box = document.getElementById('lightbox');
  const full = box.querySelector('img');
  const count = box.querySelector('.lightbox-count');
  const prevBtn = box.querySelector('.lightbox-prev');
  const nextBtn = box.querySelector('.lightbox-next');
  let group = [];
  let i = 0;
  let opener = null;

  function show(n) {
    i = (n + group.length) % group.length;
    full.src = group[i].src;
    full.alt = group[i].alt;
    // a single-photo entry has nothing to page through
    const many = group.length > 1;
    prevBtn.hidden = nextBtn.hidden = !many;
    count.textContent = many ? (i + 1) + ' / ' + group.length : '';
  }

  function open(img) {
    group = Array.from(img.closest('.adv-gallery').querySelectorAll('img'));
    opener = img;
    show(group.indexOf(img));
    box.hidden = false;
    document.body.style.overflow = 'hidden';
    box.querySelector('.lightbox-close').focus();
  }

  function close() {
    box.hidden = true;
    full.removeAttribute('src');
    document.body.style.overflow = '';
    if (opener) opener.focus();
  }

  document.addEventListener('click', function (e) {
    const img = e.target.closest('.adv-gallery img');
    if (img) { open(img); return; }
    if (box.hidden) return;
    // the backdrop closes; the arrows and the photo itself do not
    if (e.target.closest('.lightbox-prev')) show(i - 1);
    else if (e.target.closest('.lightbox-next')) show(i + 1);
    else if (e.target === full) show(i + 1);
    else if (e.target.closest('.lightbox')) close();
  });

  document.addEventListener('keydown', function (e) {
    if (box.hidden) return;
    if (e.key === 'Escape') close();
    else if (e.key === 'ArrowLeft') show(i - 1);
    else if (e.key === 'ArrowRight') show(i + 1);
  });
})();
