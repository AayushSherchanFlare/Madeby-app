const menuButton = document.querySelector(".menu-button");
const navigation = document.querySelector(".nav-links");
const themeButton = document.querySelector(".theme-toggle");
const themeLabel = document.querySelector(".theme-label");
const favicon = document.querySelector("#site-favicon");
const systemTheme = window.matchMedia("(prefers-color-scheme: dark)");

function storedTheme() {
  try {
    return localStorage.getItem("madeby-theme");
  } catch (_error) {
    return null;
  }
}

function updateThemeControl(theme) {
  if (!themeButton || !themeLabel) return;

  const darkModeEnabled = theme === "dark";
  const label = darkModeEnabled ? "Switch to light mode" : "Switch to dark mode";
  themeButton.setAttribute("aria-pressed", String(darkModeEnabled));
  themeButton.setAttribute("aria-label", label);
  themeLabel.textContent = label;
}

function applyTheme(theme, rememberChoice = false) {
  const safeTheme = theme === "dark" ? "dark" : "light";
  document.documentElement.dataset.theme = safeTheme;
  updateThemeControl(safeTheme);

  if (favicon) {
    favicon.href = safeTheme === "dark" ? favicon.dataset.darkHref : favicon.dataset.lightHref;
  }

  if (rememberChoice) {
    try {
      localStorage.setItem("madeby-theme", safeTheme);
    } catch (_error) {
      // The selected theme still applies when browser storage is unavailable.
    }
  }
}

applyTheme(document.documentElement.dataset.theme);

if (themeButton) {
  themeButton.addEventListener("click", () => {
    const nextTheme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    applyTheme(nextTheme, true);
  });
}

systemTheme.addEventListener("change", (event) => {
  if (!storedTheme()) applyTheme(event.matches ? "dark" : "light");
});

window.addEventListener("storage", (event) => {
  if (event.key === "madeby-theme" && (event.newValue === "dark" || event.newValue === "light")) {
    applyTheme(event.newValue);
  }
});

document.querySelectorAll("[data-google-auth]").forEach((link) => {
  link.addEventListener("click", (event) => {
    if (
      event.button !== 0 ||
      event.metaKey ||
      event.ctrlKey ||
      event.shiftKey ||
      event.altKey
    ) {
      return;
    }

    event.preventDefault();
    link.classList.add("is-loading");
    link.setAttribute("aria-disabled", "true");
    const label = link.querySelector(".google-auth-label");
    if (label) label.textContent = "Connecting to Google…";
    requestAnimationFrame(() => window.location.assign(link.href));
  });
});

if (menuButton && navigation) {
  const menuLabel = menuButton.querySelector(".sr-only");

  function setMenuOpen(isOpen) {
    menuButton.setAttribute("aria-expanded", String(isOpen));
    navigation.classList.toggle("is-open", isOpen);
    if (menuLabel) menuLabel.textContent = isOpen ? "Close menu" : "Open menu";
  }

  menuButton.addEventListener("click", () => {
    const isOpen = menuButton.getAttribute("aria-expanded") === "true";
    setMenuOpen(!isOpen);
  });

  navigation.addEventListener("click", (event) => {
    if (event.target.closest("a")) setMenuOpen(false);
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && menuButton.getAttribute("aria-expanded") === "true") {
      setMenuOpen(false);
      menuButton.focus();
    }
  });
}
