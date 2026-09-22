'use strict';
(() => {
  const hand = document.querySelector('.robot-hand-motion');
  if (!hand) return;

  const fingers = [...hand.querySelectorAll('.robot-finger')];
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const compactScreen = window.matchMedia('(max-width: 767px)');
  let frame = 0;

  function paint() {
    frame = 0;
    // Bounded travel works on short pages and long investigation histories alike.
    const travel = Math.min(Math.max(window.scrollY, 0) / 1400, 1);
    const progress = reducedMotion.matches ? 0 : travel;
    const scale = compactScreen.matches ? 0.45 : 1;
    hand.setAttribute('transform', `translate(${-24 * progress * scale} ${-100 * progress * scale}) rotate(${-18 + 14 * progress * scale} 320 540)`);
    fingers.forEach(finger => {
      finger.setAttribute('transform', `rotate(${Number(finger.dataset.flex) * progress * scale})`);
    });
  }

  function schedule() {
    if (!frame) frame = window.requestAnimationFrame(paint);
  }

  function setMotionPreference() {
    window.removeEventListener('scroll', schedule);
    if (!reducedMotion.matches) window.addEventListener('scroll', schedule, {passive: true});
    schedule();
  }

  reducedMotion.addEventListener('change', setMotionPreference);
  compactScreen.addEventListener('change', schedule);
  window.addEventListener('pageshow', schedule);
  setMotionPreference();
})();
