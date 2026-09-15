import './vendor/model-viewer/model-viewer.min.js';

const viewer = document.querySelector('#room-model');
const rotateButton = document.querySelector('#scene-rotate');
const resetButton = document.querySelector('#scene-reset');
const loading = document.querySelector('#scene-loading');
const error = document.querySelector('#scene-error');
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
const narrowViewport = window.matchMedia('(max-width: 560px)');

function setRotation(enabled) {
  viewer.autoRotate = enabled;
  rotateButton.setAttribute('aria-pressed', String(enabled));
  rotateButton.textContent = enabled ? 'Pause rotation' : 'Resume rotation';
}

setRotation(!reducedMotion.matches);
reducedMotion.addEventListener('change', event => setRotation(!event.matches));
rotateButton.addEventListener('click', () => setRotation(!viewer.autoRotate));
async function resetView() {
  viewer.cameraOrbit = `140deg 57deg ${narrowViewport.matches ? '110%' : '95%'}`;
  viewer.cameraTarget = '0m 1m 0m';
  viewer.fieldOfView = '30deg';
  // Gestures change internal camera goals even when these property strings stay the same.
  viewer.requestUpdate('cameraOrbit');
  viewer.requestUpdate('cameraTarget');
  viewer.requestUpdate('fieldOfView');
  viewer.resetTurntableRotation();
  await viewer.updateComplete;
  viewer.jumpCameraToGoal();
}
resetButton.addEventListener('click', resetView);
narrowViewport.addEventListener('change', resetView);
if (narrowViewport.matches) resetView();

document.addEventListener('scene-stage-change', event => {
  const source = `assets/scenes/livingroom-${event.detail.stage}.glb`;
  if (viewer.src === source) return;
  error.hidden = true;
  loading.hidden = false;
  loading.textContent = 'Loading 3D scene…';
  viewer.src = source;
});

viewer.addEventListener('progress', event => {
  const percent = Math.round(event.detail.totalProgress * 100);
  loading.textContent = `Loading 3D scene… ${percent}%`;
});
viewer.addEventListener('load', () => {
  loading.hidden = true;
  error.hidden = true;
});
viewer.addEventListener('error', () => {
  loading.hidden = true;
  error.hidden = false;
});
document.querySelector('#scene-retry').addEventListener('click', () => {
  const source = viewer.src;
  viewer.removeAttribute('src');
  error.hidden = true;
  loading.hidden = false;
  requestAnimationFrame(() => { viewer.src = source; });
});
