// Each method has its own full-scene input/output pair, including sketch and bbox overlays.
// All images are bundled with the website under assets/edits/.
const editScenes = [
  { id: 'bedroom', name: 'Warm bedroom', prompts: ['A stool', 'A wardrobe', 'Turn the wardrobe into a dark solid wood style'] },
  { id: 'livingroom', name: 'Living room', prompts: ['A simple chair', 'Another brown leather sofa', 'Replace the bowl with a book'] },
  { id: 'study', name: 'Study', prompts: ['A laptop with the lid open', 'A portrait painting', 'Make this chair ergonomic'] },
  { id: 'studio', name: 'Music studio', prompts: ['A green armchair', 'A floor lamp', 'Make the room luxurious'] }
];
const editMethods = ['Freehand 3D Sketch Editing', 'Semantic 3D Bounding Box Editing', 'Language-guided Editing'];
const editMethodKeys = ['sketch', 'bbox', 'language'];
const sceneButtons = [...document.querySelectorAll('.edit-scene')];
const methodButtons = [...document.querySelectorAll('.edit-methods [role="tab"]')];
const comparison = document.querySelector('#edit-comparison');
const divider = document.querySelector('#edit-slider');
const beforeImage = document.querySelector('#edit-before-image');
const afterImage = document.querySelector('#edit-after-image');
const assetNote = document.querySelector('#edit-asset-note');
let selectedScene = 0;
let selectedMethod = 0;
let imageRequest = 0;

function updateDivider(value) {
  const percent = Math.max(0, Math.min(100, Math.round(value)));
  divider.value = percent;
  comparison.style.setProperty('--split', `${percent}%`);
  divider.setAttribute('aria-valuetext', `${percent}% before, ${100 - percent}% after`);
}

function loadEditImage(source) {
  return new Promise(resolve => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => resolve(null);
    image.src = source;
  });
}

async function showEdit() {
  const request = ++imageRequest;
  const scene = editScenes[selectedScene];
  const method = selectedMethod;
  sceneButtons.forEach((button, index) => button.setAttribute('aria-pressed', String(index === selectedScene)));
  methodButtons.forEach((button, index) => {
    button.setAttribute('aria-selected', String(index === method));
    button.tabIndex = index === method ? 0 : -1;
  });
  document.querySelector('#edit-panel').setAttribute('aria-labelledby', methodButtons[method].id);
  document.querySelector('#edit-method-label').textContent = editMethods[method].toUpperCase();
  document.querySelector('#edit-prompt').textContent = `“${scene.prompts[method]}”`;
  document.querySelector('#edit-scene-count').textContent = `SCENE 0${selectedScene + 1} / 04`;
  document.querySelector('#edit-current-scene').textContent = scene.name;
  beforeImage.alt = `${scene.name} before ${editMethods[method]}`;
  afterImage.alt = `${scene.name} after ${editMethods[method]}`;
  beforeImage.hidden = afterImage.hidden = true;
  beforeImage.removeAttribute('src');
  afterImage.removeAttribute('src');
  comparison.style.removeProperty('aspect-ratio');
  updateDivider(50);

  const sources = ['input', 'output'].map(side => `assets/edits/${scene.id}_${editMethodKeys[method]}_${side}.png`);
  comparison.setAttribute('aria-busy', 'true');
  document.querySelectorAll('.edit-image-status').forEach(label => {
    label.textContent = 'Loading scene images…';
  });
  assetNote.hidden = false;
  assetNote.textContent = 'Loading comparison…';

  const [before, after] = await Promise.all(sources.map(loadEditImage));
  if (request !== imageRequest) return;
  comparison.setAttribute('aria-busy', 'false');
  if (!before || !after) {
    document.querySelectorAll('.edit-image-status').forEach(label => { label.textContent = 'Image unavailable'; });
    assetNote.textContent = 'This comparison is temporarily unavailable. Please select another scene or editing method.';
    return;
  }
  // Keep the complete frame visible. Both layers use the same fixed canvas during dragging.
  comparison.style.aspectRatio = `${before.naturalWidth} / ${before.naturalHeight}`;
  beforeImage.src = before.src;
  afterImage.src = after.src;
  beforeImage.hidden = afterImage.hidden = false;
  assetNote.hidden = true;
}

sceneButtons.forEach((button, index) => button.addEventListener('click', () => {
  selectedScene = index;
  showEdit();
}));

methodButtons.forEach((button, index) => {
  button.addEventListener('click', () => {
    selectedMethod = index;
    showEdit();
  });
  button.addEventListener('keydown', event => {
    let next;
    if (event.key === 'ArrowRight') next = (index + 1) % methodButtons.length;
    if (event.key === 'ArrowLeft') next = (index + methodButtons.length - 1) % methodButtons.length;
    if (event.key === 'Home') next = 0;
    if (event.key === 'End') next = methodButtons.length - 1;
    if (next === undefined) return;
    event.preventDefault();
    selectedMethod = next;
    showEdit();
    methodButtons[next].focus();
  });
});

divider.addEventListener('input', () => updateDivider(divider.value));
function moveDivider(event) {
  const bounds = comparison.getBoundingClientRect();
  updateDivider((event.clientX - bounds.left) / bounds.width * 100);
}
divider.addEventListener('pointerdown', event => {
  if (!event.isPrimary || event.button !== 0) return;
  event.preventDefault();
  divider.focus({ preventScroll: true });
  divider.setPointerCapture(event.pointerId);
  moveDivider(event);
});
divider.addEventListener('pointermove', event => {
  if (divider.hasPointerCapture(event.pointerId)) moveDivider(event);
});
divider.addEventListener('pointerup', event => {
  if (divider.hasPointerCapture(event.pointerId)) {
    moveDivider(event);
    divider.releasePointerCapture(event.pointerId);
  }
});
showEdit();
