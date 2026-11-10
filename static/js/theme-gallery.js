(() => {
  const root = document.documentElement;
  const themeToggle = document.getElementById("theme-toggle");

  if (themeToggle) {
    const syncThemeButton = () => {
      themeToggle.setAttribute("aria-pressed", String(root.dataset.theme === "dark"));
      themeToggle.setAttribute(
        "aria-label",
        root.dataset.theme === "dark" ? "Yorug' rejimga o'tish" : "Qorong'i rejimga o'tish",
      );
    };

    syncThemeButton();
    themeToggle.addEventListener("click", () => {
      const nextTheme = root.dataset.theme === "dark" ? "light" : "dark";
      root.dataset.theme = nextTheme;
      localStorage.setItem("maktab46-theme", nextTheme);
      syncThemeButton();
    });
  }

  const lightbox = document.getElementById("gallery-lightbox");
  if (!lightbox) return;

  const lightboxImage = lightbox.querySelector(".lightbox-image");
  const closeButton = lightbox.querySelector(".lightbox-close");
  let previouslyFocused = null;

  const closeLightbox = () => {
    if (lightbox.hidden) return;
    lightbox.hidden = true;
    document.body.style.overflow = "";
    if (previouslyFocused) previouslyFocused.focus();
  };

  document.querySelectorAll(".gallery-open").forEach((button) => {
    button.addEventListener("click", () => {
      const image = button.querySelector("img");
      if (!image) return;
      previouslyFocused = button;
      lightboxImage.src = button.dataset.fullImage || image.currentSrc || image.src;
      lightboxImage.alt = image.alt;
      lightbox.hidden = false;
      document.body.style.overflow = "hidden";
      closeButton.focus();
    });
  });

  closeButton.addEventListener("click", closeLightbox);
  lightbox.addEventListener("click", (event) => {
    if (event.target === lightbox) closeLightbox();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeLightbox();
  });
})();
