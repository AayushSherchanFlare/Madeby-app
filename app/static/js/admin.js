const adminMenuButton = document.querySelector(".admin-menu-button");
const adminMobileMenu = document.querySelector(".admin-mobile-menu");

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
