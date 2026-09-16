const menuButton = document.querySelector('.menu-toggle');
const navigation = document.querySelector('#navigation');

function closeMenu() {
  navigation.classList.remove('is-open');
  menuButton.setAttribute('aria-expanded', 'false');
}

menuButton.addEventListener('click', () => {
  const expanded = menuButton.getAttribute('aria-expanded') !== 'true';
  menuButton.setAttribute('aria-expanded', String(expanded));
  navigation.classList.toggle('is-open', expanded);
});

navigation.addEventListener('click', (event) => {
  if (event.target.closest('a')) closeMenu();
});

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && menuButton.getAttribute('aria-expanded') === 'true') {
    closeMenu();
    menuButton.focus();
  }
});

const navLinks = [...navigation.querySelectorAll('a')];
const sections = [...document.querySelectorAll('main section[id]')];
let scrollPending = false;

function updateNavigation() {
  const currentSection = sections.filter(section => section.getBoundingClientRect().top <= 150).at(-1);
  navLinks.forEach(link => {
    if (link.hash === `#${currentSection?.id}`) link.setAttribute('aria-current', 'location');
    else link.removeAttribute('aria-current');
  });
  scrollPending = false;
}

window.addEventListener('scroll', () => {
  if (!scrollPending) {
    scrollPending = true;
    requestAnimationFrame(updateNavigation);
  }
}, { passive: true });
updateNavigation();

const stages = {
  structure: {
    title: 'Structure',
    description: 'The room takes shape: dimensions, walls, floor, ceiling, doors, windows, and structural materials.',
    content: 'Room architecture and materials',
    badge: '01 / Room foundation'
  },
  attached: {
    title: 'Attached',
    description: 'Wall- and ceiling-mounted objects join the room, adding fixtures such as wall art and pendant lights.',
    content: 'Structure + wall and ceiling attachments',
    badge: '02 / Surface-mounted objects'
  },
  primary: {
    title: 'Primary',
    description: 'Major standalone objects populate the space, establishing the furniture arrangement and the main functional areas.',
    content: 'Structure + attachments + primary objects',
    badge: '03 / Main furnishings'
  },
  supported: {
    title: 'Supported',
    description: 'Smaller objects are placed on supporting surfaces. This final stage delivers the complete, cumulative scene.',
    content: 'All previous stages + supported objects',
    badge: '04 / Complete scene'
  }
};

const tabs = [...document.querySelectorAll('.stage-tab')];
function selectStage(tab) {
  const stage = stages[tab.dataset.stage];
  const index = tabs.indexOf(tab);
  tabs.forEach(item => {
    item.setAttribute('aria-selected', String(item === tab));
    item.tabIndex = item === tab ? 0 : -1;
  });
  document.querySelector('#stage-panel').setAttribute('aria-labelledby', tab.id);
  document.querySelector('#stage-title').textContent = stage.title;
  document.querySelector('#stage-description').textContent = stage.description;
  document.querySelector('#stage-content').textContent = stage.content;
  document.querySelector('#stage-badge').textContent = stage.badge;
  document.querySelector('#stage-progress').textContent = `Stage 0${index + 1} / 04`;
  document.querySelectorAll('.hierarchy-tree li').forEach((item, level) => {
    item.classList.toggle('is-pending', level > index);
    if (level === index) item.setAttribute('aria-current', 'step');
    else item.removeAttribute('aria-current');
  });
  document.dispatchEvent(new CustomEvent('scene-stage-change', { detail: { stage: tab.dataset.stage } }));
}

tabs.forEach((tab, index) => {
  tab.addEventListener('click', () => selectStage(tab));
  tab.addEventListener('keydown', (event) => {
    let next;
    if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
    if (event.key === 'ArrowLeft') next = (index + tabs.length - 1) % tabs.length;
    if (event.key === 'Home') next = 0;
    if (event.key === 'End') next = tabs.length - 1;
    if (next === undefined) return;
    event.preventDefault();
    selectStage(tabs[next]);
    tabs[next].focus();
  });
});

document.querySelector('#copy-citation').addEventListener('click', async () => {
  const code = document.querySelector('#bibtex');
  const status = document.querySelector('#copy-status');
  try {
    await navigator.clipboard.writeText(code.textContent);
    status.textContent = 'BibTeX copied to clipboard.';
  } catch {
    const selection = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(code);
    selection.removeAllRanges();
    selection.addRange(range);
    status.textContent = 'Copy unavailable. Citation selected — press Ctrl+C or ⌘C to copy.';
  }
});
