
async function loadOverview() {
    const response = await fetch("/api/overview");
    if (!response.ok) throw new Error("Ошибка загрузки статистики");

    const data = await response.json();

    document.getElementById("players").textContent = data.players;
    document.getElementById("sessions").textContent = data.sessions;
    document.getElementById("average-duration").textContent =
        data.average_duration_minutes;
    document.getElementById("completed").textContent = data.completed;
}

async function loadChart() {
    const response = await fetch("/api/sessions-by-day");
    if (!response.ok) throw new Error("Ошибка загрузки графика");

    drawSessionsChart(await response.json());
}

async function loadLevels() {
    const response = await fetch("/api/levels");
    if (!response.ok) throw new Error("Ошибка загрузки уровней");

    const levels = await response.json();
    const table = document.getElementById("levels-table");
    table.innerHTML = "";

    levels.forEach(function (level) {
        const rate = level.sessions
            ? Math.round(level.completed / level.sessions * 100)
            : 0;

        const row = document.createElement("tr");

        row.innerHTML = `
            <td><span class="level-label">Уровень ${level.level}</span></td>
            <td>${level.sessions}</td>
            <td>${level.completed}</td>
            <td>${level.failed}</td>
            <td>${level.quit}</td>
            <td>
                <div class="rate">
                    <span>${rate}%</span>
                    <div class="rate-track">
                        <div class="rate-fill" style="width:${rate}%"></div>
                    </div>
                </div>
            </td>
        `;

        table.appendChild(row);
    });
}

function drawSessionsChart(data) {
    const canvas = document.getElementById("sessions-chart");
    const ctx = canvas.getContext("2d");
    const rect = canvas.getBoundingClientRect();

    if (!rect.width || !rect.height) return;

    const ratio = window.devicePixelRatio || 1;
    canvas.width = Math.round(rect.width * ratio);
    canvas.height = Math.round(rect.height * ratio);

    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    ctx.clearRect(0, 0, rect.width, rect.height);

    const width = rect.width;
    const height = rect.height;
    const left = 38;
    const right = 14;
    const top = 15;
    const bottom = 35;
    const chartWidth = width - left - right;
    const chartHeight = height - top - bottom;

    const maxValue = Math.max(
        4,
        Math.ceil(Math.max(...data.map(x => x.sessions), 0) / 2) * 2
    );

    ctx.font = "11px Segoe UI";
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";

    for (let value = 0; value <= maxValue; value++) {
        const y = top + chartHeight - value / maxValue * chartHeight;

        ctx.beginPath();
        ctx.strokeStyle = "#283144";
        ctx.moveTo(left, y);
        ctx.lineTo(width - right, y);
        ctx.stroke();

        ctx.fillStyle = "#8792a7";
        ctx.fillText(String(value), left - 10, y);
    }

    const points = data.map((item, index) => ({
        x: data.length === 1
            ? left + chartWidth / 2
            : left + index / (data.length - 1) * chartWidth,
        y: top + chartHeight - item.sessions / maxValue * chartHeight,
        item: item
    }));

    if (!points.length) return;

    ctx.beginPath();
    ctx.moveTo(points[0].x, top + chartHeight);

    points.forEach(point => ctx.lineTo(point.x, point.y));

    ctx.lineTo(points[points.length - 1].x, top + chartHeight);
    ctx.closePath();
    ctx.fillStyle = "#9c82ff18";
    ctx.fill();

    ctx.beginPath();
    points.forEach((point, index) => {
        if (index === 0) ctx.moveTo(point.x, point.y);
        else ctx.lineTo(point.x, point.y);
    });

    ctx.strokeStyle = "#a48aff";
    ctx.lineWidth = 2.5;
    ctx.stroke();

    points.forEach(point => {
        ctx.beginPath();
        ctx.arc(point.x, point.y, 4, 0, Math.PI * 2);
        ctx.fillStyle = "#b7a4ff";
        ctx.fill();
    });

    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    ctx.fillStyle = "#8792a7";

    points.forEach(point => {
        const parts = point.item.date.split("-");
        ctx.fillText(parts[2] + "." + parts[1], point.x, top + chartHeight + 12);
    });
}

async function loadDataSource() {
    const response = await fetch("/api/data-source");
    const data = await response.json();
    const status = document.getElementById("upload-status");

    status.textContent = data.mode === "uploaded"
        ? "Загруженный файл активен. Записей: " + data.rows
        : "Используются демонстрационные данные. Записей: " + data.rows;
}

async function refreshDashboard() {
    await Promise.all([
        loadOverview(),
        loadChart(),
        loadLevels(),
        loadDataSource()
    ]);
}

document.getElementById("upload-form").addEventListener("submit", async function (event) {
    event.preventDefault();

    const input = document.getElementById("csv-file");
    const status = document.getElementById("upload-status");
    const button = document.getElementById("upload-button");

    if (!input.files.length) {
        status.textContent = "Сначала выбери CSV-файл.";
        return;
    }

    const formData = new FormData();
    formData.append("file", input.files[0]);
    button.disabled = true;
    status.textContent = "Загрузка...";

    try {
        const response = await fetch("/api/upload-csv", {
            method: "POST",
            body: formData
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || "Ошибка загрузки файла");
        }

        await refreshDashboard();
        status.textContent = result.message + ". Записей: " + result.rows;
    } catch (error) {
        status.textContent = "Ошибка: " + error.message;
    } finally {
        button.disabled = false;
    }
});

document.getElementById("reset-button").addEventListener("click", async function () {
    const status = document.getElementById("upload-status");

    try {
        const response = await fetch("/api/reset-data", {
            method: "POST"
        });

        if (!response.ok) throw new Error("Не удалось вернуть демо-данные");

        await refreshDashboard();
        document.getElementById("csv-file").value = "";
        status.textContent = "Демонстрационные данные восстановлены.";
    } catch (error) {
        status.textContent = "Ошибка: " + error.message;
    }
});

async function initDashboard() {
    try {
        await refreshDashboard();
    } catch (error) {
        console.error(error);
        document.getElementById("levels-table").innerHTML =
            '<tr><td colspan="6">Ошибка загрузки. Проверь сервер.</td></tr>';
    }
}

initDashboard();

window.addEventListener("resize", function () {
    loadChart().catch(console.error);
});

