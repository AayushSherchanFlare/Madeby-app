document.querySelectorAll(".comment-toggle").forEach((button) => {
  const comments = document.getElementById(button.getAttribute("aria-controls"));
  if (!comments) return;

  button.addEventListener("click", () => {
    const isOpen = comments.classList.toggle("is-open");
    button.setAttribute("aria-expanded", String(isOpen));
    if (isOpen) comments.querySelector("input")?.focus();
  });
});

document.querySelectorAll("input[data-preview-target]").forEach((input) => {
  const preview = document.getElementById(input.dataset.previewTarget);
  const image = preview?.querySelector("img");
  if (!preview || !image) return;
  let previewUrl = null;

  input.addEventListener("change", () => {
    const file = input.files?.[0];
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    if (!file) {
      preview.hidden = true;
      image.removeAttribute("src");
      previewUrl = null;
      return;
    }

    previewUrl = URL.createObjectURL(file);
    image.src = previewUrl;
    preview.hidden = false;
  });
});

document.querySelectorAll("select.ratio-select[data-preview-target]").forEach((select) => {
  const preview = document.getElementById(select.dataset.previewTarget);
  if (!preview) return;

  function updatePreviewRatio() {
    preview.dataset.ratio = select.value;
  }

  select.addEventListener("change", updatePreviewRatio);
  updatePreviewRatio();
});

document.querySelectorAll("textarea[data-post-preview-text]").forEach((textarea) => {
  const previewText = document.getElementById(textarea.dataset.postPreviewText);
  if (!previewText) return;

  function updatePreviewText() {
    const text = textarea.value.trim();
    previewText.textContent = text || "Your post text will appear here.";
    previewText.classList.toggle("is-empty", !text);
  }

  textarea.addEventListener("input", updatePreviewText);
  updatePreviewText();
});

const dashboardMenuButton = document.querySelector(".dashboard-menu-button");
const dashboardMobileMenu = document.querySelector(".dashboard-mobile-menu");

if (dashboardMenuButton && dashboardMobileMenu) {
  const menuLabel = dashboardMenuButton.querySelector(".sr-only");

  function setDashboardMenuOpen(isOpen) {
    dashboardMenuButton.setAttribute("aria-expanded", String(isOpen));
    dashboardMobileMenu.classList.toggle("is-open", isOpen);
    document.body.classList.toggle("dashboard-menu-open", isOpen);
    if (menuLabel) {
      menuLabel.textContent = isOpen ? "Close navigation menu" : "Open navigation menu";
    }
  }

  dashboardMenuButton.addEventListener("click", () => {
    setDashboardMenuOpen(
      dashboardMenuButton.getAttribute("aria-expanded") !== "true"
    );
  });

  dashboardMobileMenu.addEventListener("click", (event) => {
    if (event.target.closest("a")) setDashboardMenuOpen(false);
  });

  document.addEventListener("keydown", (event) => {
    if (
      event.key === "Escape" &&
      dashboardMenuButton.getAttribute("aria-expanded") === "true"
    ) {
      setDashboardMenuOpen(false);
      dashboardMenuButton.focus();
    }
  });
}

function closePostMenus(exceptButton = null) {
  document.querySelectorAll(".post-menu[aria-expanded='true']").forEach((button) => {
    if (button === exceptButton) return;
    button.setAttribute("aria-expanded", "false");
    document.getElementById(button.getAttribute("aria-controls"))?.classList.remove("is-open");
  });
}

document.querySelectorAll(".post-menu").forEach((button) => {
  const panel = document.getElementById(button.getAttribute("aria-controls"));
  if (!panel) return;

  button.addEventListener("click", (event) => {
    event.stopPropagation();
    const willOpen = button.getAttribute("aria-expanded") !== "true";
    closePostMenus(button);
    button.setAttribute("aria-expanded", String(willOpen));
    panel.classList.toggle("is-open", willOpen);
  });
});

document.addEventListener("click", (event) => {
  if (!event.target.closest(".post-menu-wrap")) closePostMenus();
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") closePostMenus();
});

document.querySelectorAll(".copy-post-link").forEach((button) => {
  button.addEventListener("click", async () => {
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(button.dataset.copyUrl);
      } else {
        const temporaryInput = document.createElement("textarea");
        temporaryInput.value = button.dataset.copyUrl;
        temporaryInput.setAttribute("readonly", "");
        temporaryInput.style.position = "fixed";
        temporaryInput.style.opacity = "0";
        document.body.appendChild(temporaryInput);
        temporaryInput.select();
        const copied = document.execCommand("copy");
        temporaryInput.remove();
        if (!copied) throw new Error("Clipboard copy was unavailable.");
      }
      button.textContent = "Link copied";
    } catch (_error) {
      button.textContent = "Copy failed";
    }
  });
});

document.querySelectorAll("form[data-confirm]").forEach((form) => {
  form.addEventListener("submit", (event) => {
    if (!window.confirm(form.dataset.confirm)) event.preventDefault();
  });
});

function updateEngagementCounts(card, data) {
  const likeCount = card.querySelector("[data-like-count]");
  const commentCount = card.querySelector("[data-comment-count]");
  if (likeCount && Number.isInteger(data.like_count)) {
    likeCount.textContent = `${data.like_count} ${data.like_count === 1 ? "like" : "likes"}`;
  }
  if (commentCount && Number.isInteger(data.comment_count)) {
    commentCount.textContent = `${data.comment_count} ${data.comment_count === 1 ? "comment" : "comments"}`;
  }
}

async function submitPostAction(form) {
  const response = await fetch(form.action, {
    method: "POST",
    body: new FormData(form),
    headers: {
      "Accept": "application/json",
      "X-Requested-With": "XMLHttpRequest",
    },
    credentials: "same-origin",
  });
  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json")
    ? await response.json()
    : { error: "Your session may have expired. Please log in again." };
  if (!response.ok) throw new Error(data.error || "The action could not be completed.");
  return data;
}

document.querySelectorAll(".like-form").forEach((form) => {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const card = form.closest(".feed-card");
    const button = form.querySelector("button");
    const status = card?.querySelector(".post-action-status");
    if (!card || !button || button.disabled) return;

    const previousText = button.textContent;
    button.disabled = true;
    if (status) status.textContent = "";
    try {
      const data = await submitPostAction(form);
      button.classList.toggle("is-liked", data.liked);
      button.textContent = data.liked ? "♥ Liked" : "♡ Like";
      updateEngagementCounts(card, data);
      if (status) status.textContent = data.liked ? "Post liked." : "Like removed.";
    } catch (error) {
      button.textContent = previousText;
      if (status) status.textContent = error.message;
    } finally {
      button.disabled = false;
    }
  });
});

document.querySelectorAll(".comment-form").forEach((form) => {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const card = form.closest(".feed-card");
    const input = form.querySelector("input[name='comment_text']");
    const button = form.querySelector("button[type='submit']");
    const status = card?.querySelector(".post-action-status");
    if (!card || !input || !button || button.disabled) return;

    button.disabled = true;
    if (status) status.textContent = "";
    try {
      const data = await submitPostAction(form);
      const comment = document.createElement("div");
      comment.className = "comment-row";

      const avatar = document.createElement("span");
      avatar.className = "comment-avatar";
      avatar.setAttribute("aria-hidden", "true");
      avatar.textContent = data.comment.full_name.charAt(0).toUpperCase();

      const copy = document.createElement("p");
      const author = document.createElement("strong");
      author.textContent = data.comment.full_name;
      copy.append(author, document.createTextNode(` ${data.comment.text}`));
      comment.append(avatar, copy);
      form.before(comment);

      input.value = "";
      updateEngagementCounts(card, data);
      if (status) status.textContent = "Comment posted.";
    } catch (error) {
      if (status) status.textContent = error.message;
    } finally {
      button.disabled = false;
      input.focus();
    }
  });
});
