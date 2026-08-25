const input = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");
const messages = document.getElementById("messages");
const welcome = document.getElementById("welcome");
const chat = document.getElementById("chat");
const newChatButton = document.getElementById("newChatButton");
const historyList = document.getElementById("historyList");

let chats = JSON.parse(localStorage.getItem("finlakeChats")) || [];
let currentChatId = null;


function saveChats() {
    localStorage.setItem("finlakeChats", JSON.stringify(chats));
}


function createNewChat() {
    const chat = {
        id: Date.now(),
        title: "Новый диалог",
        messages: []
    };

    chats.unshift(chat);
    currentChatId = chat.id;

    saveChats();
    renderHistory();
    renderCurrentChat();
}


function getCurrentChat() {
    return chats.find((chat) => chat.id === currentChatId);
}


function renderHistory() {
    historyList.innerHTML = "";

    chats.forEach((chat) => {
        const button = document.createElement("button");

        button.className = "history-item";
        button.textContent = chat.title;

        if (chat.id === currentChatId) {
            button.classList.add("active");
        }

        button.addEventListener("click", () => {
            currentChatId = chat.id;
            renderHistory();
            renderCurrentChat();
        });

        historyList.appendChild(button);
    });
}


function renderCurrentChat() {
    messages.innerHTML = "";

    const currentChat = getCurrentChat();

    if (!currentChat || currentChat.messages.length === 0) {
        welcome.style.display = "block";
        return;
    }

    welcome.style.display = "none";

    currentChat.messages.forEach((message) => {
        if (message.role === "user") {
            addUserMessageToPage(message.text);
        }

        if (message.role === "assistant") {
            addAIAnswerToPage(message.data);
        }
    });

    scrollToBottom();
}


function addUserMessageToPage(message) {
    const messageElement = document.createElement("div");
    messageElement.className = "message user-message";

    const bubble = document.createElement("div");
    bubble.className = "user-bubble";
    bubble.textContent = message;

    messageElement.appendChild(bubble);
    messages.appendChild(messageElement);
}


function createTable(columns, rows) {
    if (!columns || !rows || !columns.length || !rows.length) {
        return null;
    }

    const table = document.createElement("table");
    table.className = "result-table";

    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");

    columns.forEach((column) => {
        const th = document.createElement("th");
        th.textContent = column;
        headerRow.appendChild(th);
    });

    thead.appendChild(headerRow);
    table.appendChild(thead);

    const tbody = document.createElement("tbody");

    rows.forEach((row) => {
        const tableRow = document.createElement("tr");

        row.forEach((value) => {
            const td = document.createElement("td");
            td.textContent = value ?? "";
            tableRow.appendChild(td);
        });

        tbody.appendChild(tableRow);
    });

    table.appendChild(tbody);

    return table;
}


function addAIAnswerToPage(data) {
    const messageElement = document.createElement("div");
    messageElement.className = "message";

    const aiMessage = document.createElement("div");
    aiMessage.className = "ai-message";

    const title = document.createElement("div");
    title.className = "ai-title";
    title.textContent = "✦ FinLake";

    const answerText = document.createElement("p");
    answerText.textContent = data.answer;

    aiMessage.appendChild(title);
    aiMessage.appendChild(answerText);

    if (data.success && data.sql) {
        const sqlLabel = document.createElement("div");
        sqlLabel.className = "sql-label";
        sqlLabel.textContent = "SQL-запрос";

        const sqlBlock = document.createElement("div");
        sqlBlock.className = "sql-block";
        sqlBlock.textContent = data.sql;

        aiMessage.appendChild(sqlLabel);
        aiMessage.appendChild(sqlBlock);
    }

    if (data.success) {
        const table = createTable(data.columns, data.rows);

        if (table) {
            aiMessage.appendChild(table);
        }
    }

    messageElement.appendChild(aiMessage);
    messages.appendChild(messageElement);
}


function showLoader() {
    const loader = document.createElement("div");

    loader.className = "message";
    loader.id = "loader";

    loader.innerHTML = `
        <div class="ai-message">
            <div class="loader">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;

    messages.appendChild(loader);
}


function removeLoader() {
    const loader = document.getElementById("loader");

    if (loader) {
        loader.remove();
    }
}


function scrollToBottom() {
    chat.scrollTo({
        top: chat.scrollHeight,
        behavior: "smooth"
    });
}


async function sendMessage() {
    const message = input.value.trim();

    if (!message) {
        return;
    }

    if (!currentChatId) {
        createNewChat();
    }

    const currentChat = getCurrentChat();

    if (currentChat.messages.length === 0) {
        currentChat.title =
            message.length > 35
                ? message.slice(0, 35) + "..."
                : message;
    }

    currentChat.messages.push({
        role: "user",
        text: message
    });

    saveChats();
    renderHistory();

    welcome.style.display = "none";

    addUserMessageToPage(message);

    input.value = "";
    sendButton.disabled = true;

    showLoader();
    scrollToBottom();

    try {
        const response = await fetch("http://127.0.0.1:8000/ask", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                question: message
            })
        });

        if (!response.ok) {
            throw new Error("Ошибка сервера");
        }

        const data = await response.json();

        removeLoader();

        currentChat.messages.push({
            role: "assistant",
            data: data
        });

        saveChats();

        addAIAnswerToPage(data);

    } catch (error) {
        removeLoader();

        const errorData = {
            success: false,
            answer: "Не удалось получить ответ. Проверьте соединение с сервером.",
            sql: "",
            columns: [],
            rows: []
        };

        currentChat.messages.push({
            role: "assistant",
            data: errorData
        });

        saveChats();

        addAIAnswerToPage(errorData);
    }

    sendButton.disabled = false;
    input.focus();

    scrollToBottom();
}


sendButton.addEventListener("click", () => {
    sendMessage();
});


input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
});


newChatButton.addEventListener("click", () => {
    createNewChat();
    input.value = "";
    input.focus();
});


if (chats.length === 0) {
    createNewChat();
} else {
    currentChatId = chats[0].id;
    renderHistory();
    renderCurrentChat();
}