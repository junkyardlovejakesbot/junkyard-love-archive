(function () {
  var KEY = "jylp-theme";
  var root = document.documentElement;

  function current() {
    var t = root.getAttribute("data-theme");
    return t === "light" ? "light" : "dark";
  }

  function apply(theme) {
    root.setAttribute("data-theme", theme);
    var label = theme === "dark" ? "Light" : "Dark";
    document.querySelectorAll("[data-theme-toggle]").forEach(function (btn) {
      btn.textContent = label;
      btn.setAttribute("aria-pressed", theme === "dark" ? "true" : "false");
      btn.setAttribute(
        "aria-label",
        theme === "dark" ? "Switch to light mode" : "Switch to dark mode"
      );
    });
  }

  function stored() {
    try {
      var t = localStorage.getItem(KEY);
      if (t === "light" || t === "dark") return t;
    } catch (e) {}
    return null;
  }

  apply(stored() || "dark");

  document.addEventListener("click", function (e) {
    var btn = e.target.closest && e.target.closest("[data-theme-toggle]");
    if (!btn) return;
    var next = current() === "dark" ? "light" : "dark";
    try {
      localStorage.setItem(KEY, next);
    } catch (err) {}
    apply(next);
  });
})();
