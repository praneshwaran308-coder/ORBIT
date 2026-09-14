const menuButton = document.querySelector(".menu-button");
const closeButton = document.querySelector(".close-menu");
const mobileMenu = document.querySelector(".mobile-menu");

function openMenu(){
  mobileMenu.classList.add("open");
}

function closeMenu(){
  mobileMenu.classList.remove("open");
}

menuButton?.addEventListener("click", openMenu);
closeButton?.addEventListener("click", closeMenu);

document.querySelectorAll(".mobile-menu a").forEach(link=>{
  link.addEventListener("click", closeMenu);
});

document.addEventListener("keydown", event=>{
  if(event.key === "Escape") closeMenu();
});

const video = document.querySelector(".bg-video");

if(video){
  video.play().catch(()=>{});
}
