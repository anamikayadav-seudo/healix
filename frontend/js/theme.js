const toggle = document.addEventListener("click", function(e){
  if(e.target.closest("#themeToggle")){
    document.body.classList.toggle("light");
  }
});
