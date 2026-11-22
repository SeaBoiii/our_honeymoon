/* Move the existing controls, preserving player state and keyboard handlers on resize. */
function setupMapPanels(activities) {
  const get = (id) => document.getElementById(id);
  const mobile = matchMedia('(max-width: 820px)');
  const bar = get('bar'),
    side = get('side'),
    panel = get('map-options');
  const days = get('toggle'),
    more = get('options-toggle'),
    picker = get('activity-picker');
  const slots = [];

  function slot(node, container, before = null) {
    if (!node) return;
    const home = document.createComment(node.id || 'landmark picker');
    node.before(home);
    slots.push({ node, home, container, before });
  }
  slot(days, bar, more);
  for (const id of ['prev', 'next', 'speed', 'follow', 'overview'])
    slot(get(id), get('option-playback'));
  for (const id of ['journal-back', 'tour-switch'])
    slot(get(id), get('option-links'));
  for (const id of ['ctext', 'cstay', 'cfood'])
    slot(get(id), get('option-notes'));
  slot(side.querySelector('.landmark-picker'), get('option-places'));

  for (const scene of activities)
    picker.add(new Option('Day ' + scene.day + ' · ' + scene.title, scene.id));
  picker.addEventListener('change', () => {
    if (!picker.value) return;
    const hash = '#scene-' + picker.value;
    picker.selectedIndex = 0;
    closePanels(true);
    if (location.hash === hash)
      window.dispatchEvent(new HashChangeEvent('hashchange'));
    else location.hash = hash;
  });

  function closePanels(restoreFocus = false) {
    const returnTo = side.dataset.open === 'true' ? days : more;
    side.dataset.open = 'false';
    days.setAttribute('aria-expanded', 'false');
    panel.hidden = true;
    more.setAttribute('aria-expanded', 'false');
    if (restoreFocus && mobile.matches) returnTo.focus({ preventScroll: true });
  }
  function layout() {
    closePanels();
    if (mobile.matches) {
      for (const { node, container, before } of slots)
        container.insertBefore(node, before);
    } else {
      for (const { node, home } of slots) home.after(node);
    }
  }
  days.onclick = () => {
    const open = side.dataset.open !== 'true';
    closePanels();
    if (open) {
      side.dataset.open = 'true';
      days.setAttribute('aria-expanded', 'true');
      const selected =
        side.querySelector('[aria-current="true"]') ||
        side.querySelector('#days button');
      if (selected) {
        selected.focus({ preventScroll: true });
        selected.scrollIntoView({ block: 'nearest' });
      }
    }
  };
  more.onclick = () => {
    const open = panel.hidden;
    closePanels();
    if (open) {
      panel.hidden = false;
      more.setAttribute('aria-expanded', 'true');
      panel.focus({ preventScroll: true });
    }
  };
  get('days').addEventListener('click', (e) => {
    if (mobile.matches && e.target.closest('button')) {
      closePanels();
      days.focus({ preventScroll: true });
    }
  });
  get('option-playback').addEventListener('click', (e) => {
    if (e.target.closest('#overview,#prev,#next')) closePanels(true);
  });
  get('option-places').addEventListener('change', (e) => {
    if (e.target.id === 'places') closePanels(true);
  });
  document.addEventListener('keydown', (e) => {
    if (
      e.key === 'Escape' &&
      mobile.matches &&
      (!panel.hidden || side.dataset.open === 'true')
    ) {
      e.preventDefault();
      closePanels(true);
    }
  });
  document.addEventListener('pointerdown', (e) => {
    if (
      mobile.matches &&
      !bar.contains(e.target) &&
      !side.contains(e.target) &&
      !panel.contains(e.target)
    )
      closePanels();
  });
  mobile.addEventListener('change', layout);
  layout();
}
