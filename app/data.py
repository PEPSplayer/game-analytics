
from datetime import date, timedelta


# Демонстрационные игровые сессии.
# Это тестовые данные, а не реальные данные игроков.
SESSION_TEMPLATES = [
    (0, "P001", 1, 12, "completed"),
    (0, "P002", 1, 8, "failed"),
    (0, "P003", 2, 16, "completed"),
    (1, "P001", 2, 11, "completed"),
    (1, "P004", 1, 6, "quit"),
    (1, "P005", 3, 19, "failed"),
    (2, "P006", 1, 9, "completed"),
    (2, "P002", 2, 14, "failed"),
    (2, "P007", 3, 21, "completed"),
    (3, "P008", 1, 7, "quit"),
    (3, "P003", 2, 13, "completed"),
    (3, "P009", 3, 17, "failed"),
    (4, "P010", 1, 10, "completed"),
    (4, "P004", 2, 15, "completed"),
    (4, "P011", 3, 23, "failed"),
    (5, "P001", 1, 18, "completed"),
    (5, "P006", 2, 12, "quit"),
    (5, "P012", 3, 20, "completed"),
    (6, "P002", 1, 9, "completed"),
    (6, "P007", 2, 16, "failed"),
    (6, "P009", 3, 24, "quit"),
]


def get_sessions():
    """Возвращает демонстрационные сессии за последние 7 дней."""
    today = date.today()
    sessions = []

    for index, item in enumerate(SESSION_TEMPLATES, start=1):
        day_offset, player_id, level, duration, result = item
        session_date = today - timedelta(days=6 - day_offset)

        sessions.append({
            "session_id": index,
            "player_id": player_id,
            "date": session_date.isoformat(),
            "level": level,
            "duration_minutes": duration,
            "result": result
        })

    return sessions