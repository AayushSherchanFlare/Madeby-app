const adminMenuButton = document.querySelector(".admin-menu-button");
const adminMobileMenu = document.querySelector(".admin-mobile-menu");
const adminThemeButtons = document.querySelectorAll(".admin-theme-toggle");

function updateAdminThemeControls() {
  const darkModeEnabled = document.documentElement.dataset.theme === "dark";
  const label = darkModeEnabled ? "Light mode" : "Dark mode";
  const accessibleLabel = darkModeEnabled
    ? "Switch to light mode"
    : "Switch to dark mode";

  adminThemeButtons.forEach((button) => {
    button.setAttribute("aria-pressed", String(darkModeEnabled));
    button.setAttribute("aria-label", accessibleLabel);
    const icon = button.querySelector(".admin-theme-icon");
    const text = button.querySelector(".admin-theme-label");
    if (icon) icon.textContent = darkModeEnabled ? "\u2600" : "\u263e";
    if (text) text.textContent = label;
  });
}

adminThemeButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const nextTheme =
      document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = nextTheme;
    try {
      localStorage.setItem("madeby-theme", nextTheme);
    } catch (_error) {
      // The selected theme still applies if storage is unavailable.
    }
    updateAdminThemeControls();
  });
});

updateAdminThemeControls();

if (adminMenuButton && adminMobileMenu) {
  adminMenuButton.addEventListener("click", () => {
    const open = adminMenuButton.getAttribute("aria-expanded") !== "true";
    adminMenuButton.setAttribute("aria-expanded", String(open));
    adminMobileMenu.classList.toggle("is-open", open);
  });
}

document.querySelectorAll("form[data-confirm]").forEach((form) => {
  form.addEventListener("submit", (event) => {
    if (!window.confirm(form.dataset.confirm)) event.preventDefault();
  });
});

const suspensionMaximums = {
  hours: 8760,
  days: 3650,
  years: 10,
};

document.querySelectorAll(".suspension-duration").forEach((group) => {
  const duration = group.querySelector('input[name="duration"]');
  const unit = group.querySelector('select[name="unit"]');
  if (!duration || !unit) return;

  unit.addEventListener("change", () => {
    duration.max = String(suspensionMaximums[unit.value]);
    if (Number(duration.value) > suspensionMaximums[unit.value]) {
      duration.value = String(suspensionMaximums[unit.value]);
    }
  });
});
