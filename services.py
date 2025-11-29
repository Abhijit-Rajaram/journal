from datetime import date, datetime, timedelta
from models import TaskInstance, TaskTemplate
from extensions import db

def create_daily_tasks(user):
    today = date.today()
    existing = TaskInstance.query.filter_by(user_id=user.id, date=today).first()
    if existing:
        return

    weekday = today.strftime("%a").lower()[:3]
    templates = TaskTemplate.query.filter_by(user_id=user.id).all()

    for t in templates:
        if t.frequency == "daily":
            pass
        elif t.frequency == "weekly" and weekday not in (t.weekdays or "").split(","):
            continue
        elif t.frequency == "monthly" and t.day_of_month != today.day:
            continue
        elif t.frequency == "date" and t.specific_date != today:
            continue

        inst = TaskInstance(
            user_id=user.id,
            template_id=t.id,
            name=t.name,
            description=t.description
        )
        db.session.add(inst)

    db.session.commit()


def get_upcoming_tasks(user, days_ahead=7):
    today = date.today()
    future = []

    templates = TaskTemplate.query.filter_by(user_id=user.id).all()

    for t in templates:
        for offset in range(1, days_ahead + 1):
            d = today + timedelta(days=offset)
            weekday = d.strftime("%a").lower()[:3]

            if t.frequency == "daily":
                future.append((d, t))
            elif t.frequency == "weekly" and weekday in (t.weekdays or "").split(","):
                future.append((d, t))
            elif t.frequency == "monthly" and t.day_of_month == d.day:
                future.append((d, t))
            elif t.frequency == "date" and t.specific_date == d:
                future.append((d, t))

    return sorted(future, key=lambda x: x[0])
