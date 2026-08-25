const navigationItems = document.querySelectorAll(".nav-item");

navigationItems.forEach((item) => {
    item.addEventListener("click", () => {
        navigationItems.forEach((button) => {
            button.classList.remove("active");
        });

        item.classList.add("active");
    });
});