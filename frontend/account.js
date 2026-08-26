const userLogin =
    sessionStorage.getItem("userLogin");

const headerRole =
    document.getElementById("headerRole");

const miniAvatar =
    document.getElementById("miniAvatar");

const miniName =
    document.getElementById("miniName");

const miniRole =
    document.getElementById("miniRole");

const welcomeTitle =
    document.getElementById("welcomeTitle");

const welcomeText =
    document.getElementById("welcomeText");

const roleBadge =
    document.getElementById("roleBadge");

const bigAvatar =
    document.getElementById("bigAvatar");

const fullName =
    document.getElementById("fullName");

const profileSubtitle =
    document.getElementById("profileSubtitle");

const profileDetails =
    document.getElementById("profileDetails");

const stats =
    document.getElementById("stats");

const leftPanelTitle =
    document.getElementById("leftPanelTitle");

const leftPanelSubtitle =
    document.getElementById("leftPanelSubtitle");

const leftPanelContent =
    document.getElementById("leftPanelContent");

const rightPanelTitle =
    document.getElementById("rightPanelTitle");

const rightPanelSubtitle =
    document.getElementById("rightPanelSubtitle");

const rightPanelContent =
    document.getElementById("rightPanelContent");

const logoutButton =
    document.getElementById("logoutButton");


if (!userLogin) {
    window.location.href = "home.html";
}


function getRole(login) {
    return login
        .split("-")[0]
        .toUpperCase();
}


function getRoleName(role) {
    const roles = {
        STU: "Студент",
        TEA: "Преподаватель",
        APP: "Абитуриент",
        ADM: "Администрация"
    };

    return roles[role] || "Пользователь";
}


function getInitials(name) {
    if (!name) {
        return "U";
    }

    return name
        .split(" ")
        .slice(0, 2)
        .map((word) => word[0])
        .join("")
        .toUpperCase();
}


function getFirstName(name) {
    if (!name) {
        return "";
    }

    const parts = name.split(" ");

    return parts.length > 1
        ? parts[1]
        : parts[0];
}


function createDetails(items) {
    profileDetails.innerHTML = "";

    items.forEach((item) => {
        const element =
            document.createElement("div");

        element.className = "detail-item";

        element.innerHTML = `
            <span>${item.label}</span>
            <strong>${item.value ?? "—"}</strong>
        `;

        profileDetails.appendChild(element);
    });
}


function createStats(items) {
    stats.innerHTML = "";

    items.forEach((item) => {
        const card =
            document.createElement("div");

        card.className = "stat-card";

        card.innerHTML = `
            <div class="stat-icon">
                ${item.icon}
            </div>

            <div>
                <span>${item.label}</span>
                <strong>${item.value ?? "—"}</strong>
                <p>${item.description ?? ""}</p>
            </div>
        `;

        stats.appendChild(card);
    });
}


function createRows(container, rows) {
    container.innerHTML = "";

    if (!rows || rows.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                Данных пока нет
            </div>
        `;

        return;
    }

    rows.forEach((row) => {
        const element =
            document.createElement("div");

        element.className = "data-row";

        element.innerHTML = `
            <div>
                <strong>${row.title}</strong>
                <span>${row.subtitle ?? ""}</span>
            </div>

            ${
                row.value
                    ? `
                    <div class="data-value">
                        ${row.value}
                    </div>
                    `
                    : ""
            }
        `;

        container.appendChild(element);
    });
}


function renderCommon(profile) {
    const roleName =
        getRoleName(profile.role);

    const initials =
        getInitials(profile.full_name);

    const firstName =
        getFirstName(profile.full_name);

    headerRole.textContent =
        `Личный кабинет: ${roleName.toLowerCase()}`;

    miniAvatar.textContent = initials;
    bigAvatar.textContent = initials;

    miniName.textContent =
        profile.full_name;

    miniRole.textContent =
        roleName;

    roleBadge.textContent =
        roleName;

    fullName.textContent =
        profile.full_name;

    welcomeTitle.textContent =
        `Добро пожаловать, ${firstName}!`;
}


function renderStudent(profile) {
    renderCommon(profile);

    welcomeText.textContent =
        "Здесь собрана основная информация о вашем обучении.";

    profileSubtitle.textContent =
        profile.program || "Студент университета";

    createDetails([
        {
            label: "Факультет",
            value: profile.faculty
        },
        {
            label: "Год поступления",
            value: profile.enrollment_year
        },
        {
            label: "Статус",
            value: profile.is_expelled
                ? "Отчислен"
                : "Обучается"
        }
    ]);

    createStats([
        {
            icon: "📚",
            label: "Оценок",
            value: profile.grades_count,
            description: "в базе данных"
        },
        {
            icon: "📊",
            label: "Средний балл",
            value: profile.average_grade,
            description: "по всем оценкам"
        },
        {
            icon: "🎓",
            label: "Код студента",
            value: profile.login,
            description: "личный идентификатор"
        }
    ]);

    leftPanelTitle.textContent =
        "Последние оценки";

    leftPanelSubtitle.textContent =
        "Результаты по дисциплинам";

    createRows(
        leftPanelContent,
        profile.grades
    );

    rightPanelTitle.textContent =
        "Дисциплины";

    rightPanelSubtitle.textContent =
        "Учебная информация";

    createRows(
        rightPanelContent,
        profile.courses
    );
}


function renderTeacher(profile) {
    renderCommon(profile);

    welcomeText.textContent =
        "Здесь собрана информация о вашей преподавательской деятельности.";

    profileSubtitle.textContent =
        "Преподаватель университета";

    createDetails([
        {
            label: "Факультет",
            value: profile.faculty
        },
        {
            label: "Код преподавателя",
            value: profile.login
        },
        {
            label: "Статус",
            value: "Работает"
        }
    ]);

    createStats([
        {
            icon: "📚",
            label: "Дисциплины",
            value: profile.courses_count,
            description: "закреплено"
        },
        {
            icon: "🎓",
            label: "Факультет",
            value: profile.faculty_short,
            description: "основное подразделение"
        },
        {
            icon: "👨‍🏫",
            label: "Роль",
            value: "Преподаватель",
            description: "University Portal"
        }
    ]);

    leftPanelTitle.textContent =
        "Мои дисциплины";

    leftPanelSubtitle.textContent =
        "Закреплённые учебные курсы";

    createRows(
        leftPanelContent,
        profile.courses
    );

    rightPanelTitle.textContent =
        "Расписание";

    rightPanelSubtitle.textContent =
        "Занятия по вашим дисциплинам";

    createRows(
        rightPanelContent,
        profile.schedule
    );
}


function renderApplicant(profile) {
    renderCommon(profile);

    welcomeText.textContent =
        "Здесь находится информация о ваших заявлениях и поступлении.";

    profileSubtitle.textContent =
        "Абитуриент университета";

    createDetails([
        {
            label: "Код абитуриента",
            value: profile.login
        },
        {
            label: "Количество заявлений",
            value: profile.applications_count
        },
        {
            label: "Статус",
            value: profile.admitted
                ? "Зачислен"
                : "Участвует в конкурсе"
        }
    ]);

    createStats([
        {
            icon: "📄",
            label: "Заявления",
            value: profile.applications_count,
            description: "подано"
        },
        {
            icon: "📊",
            label: "Лучший балл",
            value: profile.best_score,
            description: "вступительные испытания"
        },
        {
            icon: "🎓",
            label: "Зачисление",
            value: profile.admitted
                ? "Да"
                : "Нет",
            description: "текущий статус"
        }
    ]);

    leftPanelTitle.textContent =
        "Мои заявления";

    leftPanelSubtitle.textContent =
        "Выбранные образовательные программы";

    createRows(
        leftPanelContent,
        profile.applications
    );

    rightPanelTitle.textContent =
        "Информация о поступлении";

    rightPanelSubtitle.textContent =
        "Текущий статус заявлений";

    createRows(
        rightPanelContent,
        profile.statuses
    );
}


function renderAdmin(profile) {
    renderCommon(profile);

    welcomeText.textContent =
        "Здесь собрана основная административная информация.";

    profileSubtitle.textContent =
        profile.position || "Администрация";

    createDetails([
        {
            label: "Должность",
            value: profile.position
        },
        {
            label: "Факультет",
            value: profile.faculty || "Общеуниверситетская администрация"
        },
        {
            label: "Код сотрудника",
            value: profile.login
        }
    ]);

    createStats([
        {
            icon: "🎓",
            label: "Студенты",
            value: profile.students_count,
            description: "в базе университета"
        },
        {
            icon: "📄",
            label: "Абитуриенты",
            value: profile.applicants_count,
            description: "в базе университета"
        },
        {
            icon: "🏛️",
            label: "Программы",
            value: profile.programs_count,
            description: "образовательных программ"
        }
    ]);

    leftPanelTitle.textContent =
        "Университет";

    leftPanelSubtitle.textContent =
        "Основные показатели";

    createRows(
        leftPanelContent,
        profile.overview
    );

    rightPanelTitle.textContent =
        "Администрация";

    rightPanelSubtitle.textContent =
        "Информация о подразделении";

    createRows(
        rightPanelContent,
        profile.department
    );
}


async function loadProfile() {
    try {
        const response = await fetch(
            "http://127.0.0.1:8000/profile",
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

        if (!response.ok) {
            throw new Error();
        }

        const data =
            await response.json();

        if (!data.success) {
            sessionStorage.removeItem(
                "userLogin"
            );

            window.location.href =
                "home.html";

            return;
        }

        const profile = data.profile;

        if (profile.role === "stu") {
            renderStudent(profile);
        }

        else if (profile.role === "tea") {
            renderTeacher(profile);
        }

        else if (profile.role === "app") {
            renderApplicant(profile);
        }

        else if (profile.role === "adm") {
            renderAdmin(profile);
        }

        else {
            window.location.href =
                "home.html";
        }

    } catch (error) {
        welcomeTitle.textContent =
            "Не удалось загрузить кабинет";

        welcomeText.textContent =
            "Проверьте соединение с сервером.";
    }
}


logoutButton.addEventListener(
    "click",
    () => {
        sessionStorage.removeItem(
            "userLogin"
        );

        window.location.href =
            "home.html";
    }
);


loadProfile();