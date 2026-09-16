import './vendor/model-viewer/model-viewer.min.js';

const viewer = document.querySelector('#room-model');
const rotateButton = document.querySelector('#scene-rotate');
const resetButton = document.querySelector('#scene-reset');
const loading = document.querySelector('#scene-loading');
const error = document.querySelector('#scene-error');
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
const narrowViewport = window.matchMedia('(max-width: 560px)');
const modeButtons = [...document.querySelectorAll('[data-view]')];
let stage = document.querySelector('.stage-tab[aria-selected="true"]').dataset.stage;
let representation = 'assets';
let sceneUpdate;

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

function updateScene() {
  cancelAnimationFrame(sceneUpdate);
  sceneUpdate = requestAnimationFrame(() => {
    const source = `assets/scenes/livingroom-${representation === 'layout' ? 'layout-' : ''}${stage}.glb`;
    if (viewer.src === source) return;
    error.hidden = true;
    loading.hidden = false;
    loading.textContent = 'Loading 3D scene…';
    viewer.alt = representation === 'layout'
      ? `Illustrative ${stage} layout bounds, colored by scene hierarchy`
      : `Living room with cumulative ${stage} assets`;
    viewer.src = source;
  });
}

document.addEventListener('scene-stage-change', event => {
  stage = event.detail.stage;
  updateScene();
});

modeButtons.forEach(button => button.addEventListener('click', () => {
  representation = button.dataset.view;
  modeButtons.forEach(item => item.setAttribute('aria-pressed', String(item === button)));
  document.querySelector('#scene-mode-label').textContent = representation === 'layout' ? '/ LAYOUT BOUNDS' : '/ ASSEMBLED SCENE';
  document.querySelector('#scene-representation-note').textContent = representation === 'layout'
    ? 'Illustrative spatial bounds from this example scene, colored by hierarchy. Layout planning uses positions, dimensions, and relations without rendered feedback.'
    : 'Switch to Layout to compare spatial bounds with the assembled assets. Both views show the same example scene.';
  updateScene();
}));

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
