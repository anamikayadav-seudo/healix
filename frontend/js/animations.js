// Page fade in
document.body.style.opacity = 0;

window.addEventListener("load", () => {
  document.body.style.transition = "opacity 0.6s ease";
  document.body.style.opacity = 1;
});

// Scroll reveal
const reveals = document.querySelectorAll(".reveal");

const observer = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if(entry.isIntersecting){
      entry.target.classList.add("active");
    }
  });
});

reveals.forEach(el => observer.observe(el));
