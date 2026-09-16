const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
const sceneViews = [...document.querySelectorAll('.result-viewer')];

function setRotation(view, enabled) {
  const viewer = view.querySelector('.result-model');
  const button = view.querySelector('.result-rotate');
  viewer.toggleAttribute('auto-rotate', enabled);
  button.setAttribute('aria-pressed', String(enabled));
  button.textContent = enabled ? 'Pause rotation' : 'Resume rotation';
}

sceneViews.forEach(view => {
  const viewer = view.querySelector('.result-model');
  const button = view.querySelector('.result-rotate');
  const loading = view.querySelector('.result-loading');

  setRotation(view, !reducedMotion.matches);
  button.addEventListener('click', () => setRotation(view, !viewer.hasAttribute('auto-rotate')));

  viewer.addEventListener('progress', event => {
    const percent = Math.round(event.detail.totalProgress * 100);
    if (percent >= 100) {
      loading.hidden = true;
      view.classList.add('is-loaded');
    } else {
      loading.hidden = false;
      loading.textContent = `Loading 3D scene… ${percent}%`;
    }
  });
  viewer.addEventListener('load', () => {
    loading.hidden = true;
    view.classList.add('is-loaded');
  });
  viewer.addEventListener('error', () => {
    loading.hidden = false;
    loading.textContent = 'Unable to load 3D scene';
    loading.classList.add('is-error');
    button.disabled = true;
  });
  if (viewer.loaded) {
    loading.hidden = true;
    view.classList.add('is-loaded');
  }
});

reducedMotion.addEventListener('change', event => {
  sceneViews.forEach(view => setRotation(view, !event.matches));
});
