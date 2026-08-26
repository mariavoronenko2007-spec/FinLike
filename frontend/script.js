const input = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");
const messages = document.getElementById("messages");
const welcome = document.getElementById("welcome");
const chat = document.getElementById("chat");
const newChatButton = document.getElementById("newChatButton");
const historyList = document.getElementById("historyList");
const roleBadge = document.getElementById("roleBadge");


const userLogin =
    sessionStorage.getItem("userLogin");


function getRole(login) {
    if (!login) {
        return "anon";
    }

    return login
        .split("-")[0]
        .toLowerCase();
}


function getRoleName(role) {
    const roles = {
        stu: "Студент",
        tea: "Преподаватель",
        app: "Абитуриент",
        adm: "Администрация",
        anon: "FinLake"
    };

    return roles[role] || "FinLake";
}


const userRole =
    getRole(userLogin);


if (roleBadge) {
    roleBadge.textContent =
        getRoleName(userRole);
}


let chats = [];
let currentChatId = null;


function startNewChat() {
    currentChatId = null;

    messages.innerHTML = "";

    welcome.style.display =
        "block";

    input.value = "";

    input.focus();

    renderHistory();
}


async function loadHistory() {
    if (!userLogin) {
        chats = [];

        renderHistory();

        return;
    }

    try {
        const response = await fetch(
            "http://127.0.0.1:8000/chats",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    login: userLogin
                })
            }
        );

        const data =
            await response.json();

        if (data.success) {
            chats = data.chats;
        } else {
            chats = [];
        }

    } catch (error) {
        chats = [];
    }

    renderHistory();
}


function renderHistory() {
    historyList.innerHTML = "";

    if (!userLogin) {
        return;
    }

    chats.forEach((chatItem) => {
        const button =
            document.createElement(
                "button"
            );

        button.className =
            "history-item";

        button.textContent =
            chatItem.title;

        if (
            chatItem.id === currentChatId
        ) {
            button.classList.add(
                "active"
            );
        }

        button.addEventListener(
            "click",
            () => {
                openChat(
                    chatItem.id
                );
            }
        );

        historyList.appendChild(
            button
        );
    });
}


async function openChat(chatId) {
    if (!userLogin) {
        return;
    }

    currentChatId = chatId;

    messages.innerHTML = "";

    welcome.style.display =
        "none";

    renderHistory();

    try {
        const response = await fetch(
            "http://127.0.0.1:8000/chats/messages",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    login: userLogin,
                    chat_id: chatId
                })
            }
        );

        const data =
            await response.json();

        if (!data.success) {
            startNewChat();

            return;
        }

        data.messages.forEach(
            (message) => {

                if (
                    message.sender ===
                    "user"
                ) {
                    addUserMessageToPage(
                        message.content.text
                    );
                }

                if (
                    message.sender ===
                    "assistant"
                ) {
                    addAIAnswerToPage(
                        message.content
                    );
                }
            }
        );

        scrollToBottom();

    } catch (error) {
        startNewChat();
    }
}


async function createServerChat(
    firstMessage
) {
    const title =
        firstMessage.length > 35
            ? firstMessage.slice(
                0,
                35
            ) + "..."
            : firstMessage;

    const response = await fetch(
        "http://127.0.0.1:8000/chats/create",
        {
            method: "POST",

            headers: {
                "Content-Type":
                    "application/json"
            },

            body: JSON.stringify({
                login: userLogin,
                title: title
            })
        }
    );

    const data =
        await response.json();

    if (!data.success) {
        throw new Error(
            "Не удалось создать диалог"
        );
    }

    return data.chat_id;
}


async function saveServerMessage(
    sender,
    content
) {
    if (!userLogin) {
        return;
    }

    const response = await fetch(
        "http://127.0.0.1:8000/chats/message",
        {
            method: "POST",

            headers: {
                "Content-Type":
                    "application/json"
            },

            body: JSON.stringify({
                login: userLogin,
                chat_id: currentChatId,
                sender: sender,
                content: content
            })
        }
    );

    const data =
        await response.json();

    if (!data.success) {
        throw new Error(
            "Не удалось сохранить сообщение"
        );
    }
}


function addUserMessageToPage(
    message
) {
    const messageElement =
        document.createElement(
            "div"
        );

    messageElement.className =
        "message user-message";

    const bubble =
        document.createElement(
            "div"
        );

    bubble.className =
        "user-bubble";

    bubble.textContent =
        message;

    messageElement.appendChild(
        bubble
    );

    messages.appendChild(
        messageElement
    );
}


function createTable(
    columns,
    rows
) {
    if (
        !columns
        || !rows
        || !columns.length
        || !rows.length
    ) {
        return null;
    }

    const table =
        document.createElement(
            "table"
        );

    table.className =
        "result-table";

    const thead =
        document.createElement(
            "thead"
        );

    const headerRow =
        document.createElement(
            "tr"
        );

    columns.forEach(
        (column) => {

            const th =
                document.createElement(
                    "th"
                );

            th.textContent =
                column;

            headerRow.appendChild(
                th
            );
        }
    );

    thead.appendChild(
        headerRow
    );

    table.appendChild(
        thead
    );

    const tbody =
        document.createElement(
            "tbody"
        );

    rows.forEach(
        (row) => {

            const tableRow =
                document.createElement(
                    "tr"
                );

            row.forEach(
                (value) => {

                    const td =
                        document.createElement(
                            "td"
                        );

                    td.textContent =
                        value ?? "";

                    tableRow.appendChild(
                        td
                    );
                }
            );

            tbody.appendChild(
                tableRow
            );
        }
    );

    table.appendChild(
        tbody
    );

    return table;
}


function addAIAnswerToPage(
    data
) {
    const messageElement =
        document.createElement(
            "div"
        );

    messageElement.className =
        "message";

    const aiMessage =
        document.createElement(
            "div"
        );

    aiMessage.className =
        "ai-message";

    const title =
        document.createElement(
            "div"
        );

    title.className =
        "ai-title";

    title.textContent =
        "✦ FinLake";

    const answerText =
        document.createElement(
            "p"
        );

    answerText.textContent =
        data.answer;

    aiMessage.appendChild(
        title
    );

    aiMessage.appendChild(
        answerText
    );

    if (
        data.success
        && data.sql
    ) {
        const sqlLabel =
            document.createElement(
                "div"
            );

        sqlLabel.className =
            "sql-label";

        sqlLabel.textContent =
            "SQL-запрос";

        const sqlBlock =
            document.createElement(
                "div"
            );

        sqlBlock.className =
            "sql-block";

        sqlBlock.textContent =
            data.sql;

        aiMessage.appendChild(
            sqlLabel
        );

        aiMessage.appendChild(
            sqlBlock
        );
    }

    if (data.success) {
        const table =
            createTable(
                data.columns,
                data.rows
            );

        if (table) {
            aiMessage.appendChild(
                table
            );
        }
    }

    messageElement.appendChild(
        aiMessage
    );

    messages.appendChild(
        messageElement
    );
}


function showLoader() {
    const loader =
        document.createElement(
            "div"
        );

    loader.className =
        "message";

    loader.id =
        "loader";

    loader.innerHTML = `
        <div class="ai-message">
            <div class="loader">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;

    messages.appendChild(
        loader
    );
}


function removeLoader() {
    const loader =
        document.getElementById(
            "loader"
        );

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
    const message =
        input.value.trim();

    if (!message) {
        return;
    }

    try {
        if (
            userLogin
            && currentChatId === null
        ) {
            currentChatId =
                await createServerChat(
                    message
                );

            await loadHistory();
        }

        welcome.style.display =
            "none";

        addUserMessageToPage(
            message
        );

        input.value = "";

        sendButton.disabled =
            true;

        if (userLogin) {
            await saveServerMessage(
                "user",
                {
                    text: message
                }
            );
        }

        showLoader();

        scrollToBottom();

        const response =
            await fetch(
                "http://127.0.0.1:8000/ask",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({
                            question:
                                message,
                            login:
                                userLogin
                        })
                }
            );

        if (!response.ok) {
            throw new Error();
        }

        const data =
            await response.json();

        removeLoader();

        addAIAnswerToPage(
            data
        );

        if (userLogin) {
            await saveServerMessage(
                "assistant",
                data
            );
        }

    } catch (error) {
        removeLoader();

        const errorData = {
            success: false,
            answer:
                "Не удалось получить ответ. Проверьте соединение с сервером.",
            sql: "",
            columns: [],
            rows: []
        };

        addAIAnswerToPage(
            errorData
        );
    }

    sendButton.disabled =
        false;

    input.focus();

    scrollToBottom();
}


sendButton.addEventListener(
    "click",
    () => {
        sendMessage();
    }
);


input.addEventListener(
    "keydown",
    (event) => {

        if (
            event.key === "Enter"
            && !event.shiftKey
        ) {
            event.preventDefault();

            sendMessage();
        }
    }
);


newChatButton.addEventListener(
    "click",
    () => {
        startNewChat();
    }
);


async function startPage() {
    if (userLogin) {
        await loadHistory();
    } else {
        chats = [];
        renderHistory();
    }

    startNewChat();
}


startPage();