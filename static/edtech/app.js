document.addEventListener("DOMContentLoaded", () => {
  if (window.lucide) lucide.createIcons();
  const savedTheme = localStorage.getItem("tuitioncom-theme") || localStorage.getItem("dinuworld-theme");
  if (savedTheme === "dark") document.body.classList.add("dark");
  document.querySelector("#themeToggle")?.addEventListener("click", () => {
    document.body.classList.toggle("dark");
    localStorage.setItem("tuitioncom-theme", document.body.classList.contains("dark") ? "dark" : "light");
  });
  document.querySelectorAll("[data-count]").forEach(el => {
    const target = Number(el.dataset.count || 0);
    let current = 0;
    const step = Math.max(1, Math.ceil(target / 40));
    const timer = setInterval(() => {
      current = Math.min(target, current + step);
      el.textContent = current.toLocaleString();
      if (current >= target) clearInterval(timer);
    }, 25);
  });
  const observer = new IntersectionObserver(entries => entries.forEach(entry => {
    if (entry.isIntersecting) entry.target.classList.add("visible");
  }), { threshold: 0.12 });
  document.querySelectorAll(".reveal").forEach(el => observer.observe(el));
  document.querySelectorAll(".toast").forEach(el => setTimeout(() => el.remove(), 4500));
});
window.togglePassword = button => {
  const input = button.previousElementSibling;
  input.type = input.type === "password" ? "text" : "password";
};
