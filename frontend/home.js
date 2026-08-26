const accountButton = document.getElementById("accountButton");
const loginModal = document.getElementById("loginModal");
const closeButton = document.getElementById("closeButton");
const loginForm = document.getElementById("loginForm");
const loginInput = document.getElementById("login");
const errorMessage = document.getElementById("errorMessage");


accountButton.addEventListener("click", () => {
    loginModal.classList.add("active");
});


closeButton.addEventListener("click", () => {
    loginModal.classList.remove("active");
    errorMessage.textContent = "";
});


loginModal.addEventListener("click", (event) => {
    if (event.target === loginModal) {
        loginModal.classList.remove("active");
        errorMessage.textContent = "";
    }
});


loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const login = loginInput.value.trim();

    errorMessage.textContent = "";

    if (!login) {
        errorMessage.textContent = "Введите логин.";
        return;
    }

    if (!login.includes("-")) {
        errorMessage.textContent = "Неверный формат логина.";
        return;
    }

    try {
        const response = await fetch(
            "http://127.0.0.1:8000/login",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    login: login
                })
            }
        );

        if (!response.ok) {
            throw new Error();
        }

        const data = await response.json();

        if (!data.success) {
            errorMessage.textContent = data.message;
            return;
        }

        sessionStorage.setItem(
            "userLogin",
            data.login
        );

        window.location.href = "account.html";

    } catch (error) {
        errorMessage.textContent =
            "Не удалось проверить логин. Проверьте соединение с сервером.";
    }
});