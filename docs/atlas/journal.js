/* The printed day links are also the source of the native mobile picker. */
(() => {
  const index = document.querySelector(".day-index");
  const picker = document.querySelector("#day-picker");
  const links = Array.from(index.querySelectorAll("ol a"));
  const chapters = links.map((link) =>
    document.getElementById(link.hash.slice(1)),
  );

  links.forEach((link) => {
    const date = link.querySelector("time").textContent;
    const place = link.querySelector("span").textContent;
    picker.add(new Option(date + " · " + place, link.hash));
  });
  picker.hidden = false;
  index.classList.add("has-picker");
  picker.addEventListener("change", () => {
    const chapter = document.getElementById(picker.value.slice(1));
    location.hash = picker.value;
    chapter.focus({ preventScroll: true });
  });

  let active = -1;
  function markDay() {
    const sticky = getComputedStyle(picker).display !== "none";
    const guide = sticky ? index.offsetHeight + 20 : 40;
    let current = 0;
    for (let i = 1; i < chapters.length; i++) {
      if (chapters[i].getBoundingClientRect().top > guide) break;
      current = i;
    }
    if (current === active) return;
    if (active >= 0) links[active].removeAttribute("aria-current");
    active = current;
    links[active].setAttribute("aria-current", "location");
    picker.value = links[active].hash;
    if (!sticky) {
      const list = index.querySelector("ol");
      const bounds = list.getBoundingClientRect();
      const entry = links[active].getBoundingClientRect();
      if (entry.bottom > bounds.bottom)
        list.scrollTop += entry.bottom - bounds.bottom;
      if (entry.top < bounds.top) list.scrollTop -= bounds.top - entry.top;
    }
  }
  let pending = false;
  function schedule() {
    if (pending) return;
    pending = true;
    requestAnimationFrame(() => {
      pending = false;
      markDay();
    });
  }
  window.addEventListener("scroll", schedule, { passive: true });
  window.addEventListener("resize", schedule);
  window.addEventListener("pageshow", schedule);
  window.addEventListener("hashchange", schedule);
  markDay();
})();
