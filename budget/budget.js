(() => {
  const byId = id => document.getElementById(id);
  const form = byId('budget-form');
  const cap = byId('cap'), paid = byId('paid'), lodging = byId('lodging');
  const key = 'honeymoon-atlas-budget-v1';
  const money = (cents, prefix = 'S$') => prefix + (cents / 100).toLocaleString('en-SG', {
    minimumFractionDigits: cents % 100 === 0 ? 0 : 2,
    maximumFractionDigits: 2
  });
  const costs = [...document.querySelectorAll('[data-cost]')].map(row => ({
    id: row.dataset.cost,
    unit: row.dataset.unit,
    amounts: [...row.querySelectorAll('data')].map(cell => Number(cell.value) * 100),
    cells: row.querySelectorAll('data')
  }));

  function validAmount(value, min) {
    return typeof value === 'number' && Number.isFinite(value) && value >= min && value <= 99999999;
  }
  let saved;
  try { saved = JSON.parse(localStorage.getItem(key)); } catch {}
  if (validAmount(saved?.cap, 0.01)) cap.value = saved.cap;
  if (validAmount(saved?.paid, 0)) paid.value = saved.paid;
  if (validAmount(saved?.lodging, 0)) lodging.value = saved.lodging;

  function save() {
    const record = {cap: cap.valueAsNumber, paid: paid.valueAsNumber, lodging: lodging.valueAsNumber};
    try { localStorage.setItem(key, JSON.stringify(record)); } catch {}
  }

  function render() {
    const limit = Math.round(cap.valueAsNumber * 100);
    const airfare = Math.round(paid.valueAsNumber * 100);
    const bookedRooms = Math.round(lodging.valueAsNumber * 100);
    const balance = limit - airfare;
    byId('cap-total').textContent = money(limit);
    byId('flight-total').textContent = money(airfare);
    byId('cash-left').textContent = (balance < 0 ? '−' : '') + money(Math.abs(balance));
    const target = byId('lodging-target');
    target.hidden = true;

    for (const [index, scenario] of ['plan', 'high'].entries()) {
      const fx = index === 0 ? 0.73 : 0.78;
      let nzd = 0, sgd = 0, roomCost = 0;
      for (const row of costs) {
        let amount = row.amounts[index];
        if (row.id === 'stays') {
          if (Number.isFinite(bookedRooms)) amount = bookedRooms;
          row.cells[index].textContent = money(amount, 'NZ$');
          roomCost = amount;
        }
        if (row.unit === 'NZD') nzd += amount;
        else sgd += amount;
      }
      const ground = Math.round(nzd * fx) + sgd;
      const margin = balance - ground;
      const card = document.querySelector('[data-case="' + scenario + '"]');
      card.querySelector('[data-ground]').textContent = money(ground);
      card.querySelector('[data-total]').textContent = money(ground + airfare);
      card.dataset.over = String(margin < 0);
      card.querySelector('[data-verdict]').textContent = margin === 0 ? 'Exactly on budget'
        : money(Math.abs(margin)) + (margin > 0 ? ' left over' : ' over budget');
      if (scenario === 'high' && margin < 0) {
        const ceiling = Math.floor((balance - sgd - (nzd - roomCost) * fx) / (100 * fx));
        target.textContent = ceiling > 0
          ? 'If other costs reach the higher estimates, keeping the 13 nights at or below ' + money(ceiling * 100, 'NZ$') + ' would keep the trip within budget.'
          : 'At the higher estimates, expenses outside accommodation already use the remaining budget.';
        target.hidden = false;
      }
    }
  }
  document.querySelector('.adjustments').hidden = false;
  render();
  form.addEventListener('submit', event => {
    event.preventDefault();
    save();
    render();
    byId('settings').open = false;
    byId('settings').querySelector('summary').focus();
  });
  byId('restore').addEventListener('click', () => {
    form.reset();
    form.requestSubmit();
  });
})();
