import csv
import io
from datetime import date
from collections import defaultdict
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.data import get_sessions


BASE_DIR = Path(__file__).resolve().parent
print("Папка приложения:", BASE_DIR)
print("Путь к CSS:", BASE_DIR / "static" / "style.css")
print("CSS существует:", (BASE_DIR / "static" / "style.css").exists())
uploaded_sessions = None

REQUIRED_COLUMNS = {
    "player_id",
    "date",
    "level",
    "duration_minutes",
    "result"
}

VALID_RESULTS = {"completed", "failed", "quit"}

app = FastAPI(
    title="Game Analytics",
    description="Analytics dashboard for game sessions",
    version="0.2.0"
)

app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static"
)


def get_current_sessions():
    if uploaded_sessions is not None:
        return uploaded_sessions
    return get_sessions()


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(str(BASE_DIR / "templates" / "index.html"))


@app.get("/api/data-source")
def get_data_source():
    sessions = get_current_sessions()

    return {
        "mode": "uploaded" if uploaded_sessions is not None else "demo",
        "rows": len(sessions)
    }


@app.post("/api/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    global uploaded_sessions

    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Выберите файл с расширением .csv"
        )

    content = await file.read()

    if not content:
        raise HTTPException(status_code=400, detail="Файл пустой")

    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Сохраните CSV-файл в кодировке UTF-8"
        )

    reader = csv.DictReader(io.StringIO(text))

    if not reader.fieldnames:
        raise HTTPException(
            status_code=400,
            detail="В файле отсутствуют заголовки столбцов"
        )

    reader.fieldnames = [
        name.strip() if name else ""
        for name in reader.fieldnames
    ]

    missing = REQUIRED_COLUMNS - set(reader.fieldnames)

    if missing:
        raise HTTPException(
            status_code=400,
            detail="Не хватает столбцов: " + ", ".join(sorted(missing))
        )

    sessions = []

    for line_number, row in enumerate(reader, start=2):
        try:
            player_id = (row.get("player_id") or "").strip()
            session_date = (row.get("date") or "").strip()
            result = (row.get("result") or "").strip().lower()

            if not player_id:
                raise ValueError("player_id не может быть пустым")

            date.fromisoformat(session_date)

            level = int(row["level"])
            duration = float(row["duration_minutes"])

            if level < 1:
                raise ValueError("level должен быть не меньше 1")

            if duration <= 0:
                raise ValueError(
                    "duration_minutes должен быть больше 0"
                )

            if result not in VALID_RESULTS:
                raise ValueError(
                    "result должен быть completed, failed или quit"
                )

            sessions.append({
                "session_id": len(sessions) + 1,
                "player_id": player_id,
                "date": session_date,
                "level": level,
                "duration_minutes": duration,
                "result": result
            })

        except (ValueError, TypeError, KeyError) as error:
            raise HTTPException(
                status_code=400,
                detail="Ошибка в строке "
                + str(line_number)
                + ": "
                + str(error)
            )

    if not sessions:
        raise HTTPException(
            status_code=400,
            detail="В файле нет игровых сессий"
        )

    uploaded_sessions = sessions

    return {
        "message": "Данные успешно загружены",
        "rows": len(sessions)
    }


@app.post("/api/reset-data")
def reset_data():
    global uploaded_sessions
    uploaded_sessions = None

    return {
        "message": "Демонстрационные данные восстановлены"
    }


@app.get("/api/overview")
def get_overview():
    sessions = get_current_sessions()

    unique_players = len(set(
        session["player_id"] for session in sessions
    ))

    average_duration = (
        sum(session["duration_minutes"] for session in sessions)
        / len(sessions)
        if sessions else 0
    )

    completed = sum(
        1 for session in sessions
        if session["result"] == "completed"
    )

    failed = sum(
        1 for session in sessions
        if session["result"] == "failed"
    )

    quit_sessions = sum(
        1 for session in sessions
        if session["result"] == "quit"
    )

    return {
        "players": unique_players,
        "sessions": len(sessions),
        "average_duration_minutes": round(average_duration, 1),
        "completed": completed,
        "failed": failed,
        "quit": quit_sessions
    }


@app.get("/api/sessions-by-day")
def get_sessions_by_day():
    sessions = get_current_sessions()
    grouped = defaultdict(int)

    for session in sessions:
        grouped[session["date"]] += 1

    return [
        {"date": day, "sessions": count}
        for day, count in sorted(grouped.items())
    ]


@app.get("/api/levels")
def get_levels():
    sessions = get_current_sessions()
    grouped = {}

    for session in sessions:
        level = session["level"]

        if level not in grouped:
            grouped[level] = {
                "level": level,
                "sessions": 0,
                "completed": 0,
                "failed": 0,
                "quit": 0
            }

        grouped[level]["sessions"] += 1
        grouped[level][session["result"]] += 1

    return [
        grouped[level]
        for level in sorted(grouped)
    ]


@app.get("/api/sessions")
def get_all_sessions():
    return get_current_sessions()
