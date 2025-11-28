from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, datetime
import datetime as dt
from dotenv import load_dotenv
import os
from flask_migrate import Migrate
# Initialize app

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = str(os.getenv('SECRET_KEY'))
# app.config['SQLALCHEMY_DATABASE_URI'] = str(os.getenv('SQLALCHEMY_DATABASE_URI'))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tasks.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# -------------------- MODELS --------------------

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    templates = db.relationship('TaskTemplate', backref='user', lazy=True)
    task_instances = db.relationship('TaskInstance', backref='user_instance', lazy=True)


class TaskTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))

    # frequency options:
    # daily, once, weekly, monthly, date
    frequency = db.Column(db.String(20), default='daily')

    weekdays = db.Column(db.String(50), nullable=True)   # e.g. "mon,wed,fri"
    day_of_month = db.Column(db.Integer, nullable=True)  # 1–31
    specific_date = db.Column(db.Date, nullable=True)    # fixed date


class TaskInstance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('task_template.id'), nullable=True)

    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))

    done = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)

    date = db.Column(db.Date, default=date.today)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# -------------------- DAILY TASK CREATION --------------------

def create_daily_tasks(user):
    today = date.today()
    weekday = today.strftime("%a").lower()[:3]  # mon, tue, wed...
    day_num = today.day

    # If already created, skip
    if TaskInstance.query.filter_by(user_id=user.id, date=today).first():
        return

    templates = TaskTemplate.query.filter_by(user_id=user.id).all()

    for tmpl in templates:

        # Daily tasks
        if tmpl.frequency == 'daily':
            pass

        # One-time - manually added only
        # elif tmpl.frequency == 'once':
        #     continue

        # Weekly tasks
        elif tmpl.frequency == 'weekly':
            if not tmpl.weekdays:
                continue
            days = tmpl.weekdays.split(",")
            if weekday not in days:
                continue

        # Monthly tasks
        elif tmpl.frequency == 'monthly':
            if tmpl.day_of_month != day_num:
                continue

        # Specific date tasks
        elif tmpl.frequency == 'date':
            if not tmpl.specific_date:
                continue
            if tmpl.specific_date != today:
                continue

        # Create task instance
        task = TaskInstance(
            user_id=user.id,
            template_id=tmpl.id,
            name=tmpl.name,
            description=tmpl.description,
            date=today
        )
        db.session.add(task)

    db.session.commit()


# -------------------- ROUTES --------------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        if User.query.filter_by(username=username).first():
            flash("Username already exists!")
            return redirect(url_for('register'))

        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()

        flash("Registration successful! Please login.")
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))

        flash("Invalid credentials!")
        return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# @app.route('/', methods=['GET', 'POST'])
# @login_required
# def index():
#     create_daily_tasks(current_user)

#     today = date.today()
#     tasks = TaskInstance.query.filter_by(user_id=current_user.id, date=today).all()

#     if request.method == 'POST':
#         for task in tasks:
#             # Check if user marked it as done in the form
#             if f'done-{task.id}' in request.form:
#                 if not task.done:  # only update if it wasn't done before
#                     task.done = True
#                     task.completed_at = datetime.now()
#                 # Always update description, even if previously done
#                 task.description = request.form.get(f'description-{task.id}', task.description)
#             else:
#                 # Optional: uncheck to mark incomplete (if you allow)
#                 # task.done = False
#                 # task.completed_at = None
#                 pass

#         db.session.commit()
#         return redirect(url_for('index'))

#     return render_template('index.html', tasks=tasks)



@app.route('/add_task', methods=['GET', 'POST'])
@login_required
def add_task():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']

        task = TaskInstance(
            user_id=current_user.id,
            name=name,
            description=description,
            date=date.today()
        )

        db.session.add(task)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template('add_task.html')


@app.route('/history')
@login_required
def history():
    all_tasks = TaskInstance.query.filter_by(
        user_id=current_user.id
    ).order_by(TaskInstance.date.desc()).all()

    tasks_by_day = {}
    for task in all_tasks:
        tasks_by_day.setdefault(task.date, []).append(task)

    return render_template('history.html', tasks_by_day=tasks_by_day)


@app.route('/create_template', methods=['GET', 'POST'])
@login_required
def create_template():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        frequency = request.form['frequency']

        weekdays = None
        day_of_month = None
        specific_date = None

        if frequency == 'weekly':
            selected_days = request.form.getlist('weekdays')
            weekdays = ",".join(selected_days)

        if frequency == 'monthly':
            day_of_month = int(request.form['day_of_month'])

        if frequency == 'date':
            specific_date = request.form['specific_date']
            specific_date = dt.datetime.strptime(specific_date, "%Y-%m-%d").date()

        tmpl = TaskTemplate(
            user_id=current_user.id,
            name=name,
            description=description,
            frequency=frequency,
            weekdays=weekdays,
            day_of_month=day_of_month,
            specific_date=specific_date
        )

        db.session.add(tmpl)
        db.session.commit()

        flash("Template created successfully!")
        return redirect(url_for('index'))

    return render_template('create_template.html')

def get_upcoming_tasks(user, days_ahead=7):
    today = date.today()
    upcoming = []

    templates = TaskTemplate.query.filter_by(user_id=user.id).all()

    for tmpl in templates:
        for offset in range(1, days_ahead + 1):
            d = today + dt.timedelta(days=offset)
            weekday = d.strftime("%a").lower()[:3]

            if tmpl.frequency == "daily":
                upcoming.append((d, tmpl))

            elif tmpl.frequency == "weekly":
                if tmpl.weekdays:
                    days = tmpl.weekdays.split(",")
                    if weekday in days:
                        upcoming.append((d, tmpl))

            elif tmpl.frequency == "monthly":
                if tmpl.day_of_month == d.day:
                    upcoming.append((d, tmpl))

            elif tmpl.frequency == "date":
                if tmpl.specific_date == d:
                    upcoming.append((d, tmpl))

    # Sort by date
    upcoming.sort(key=lambda x: x[0])
    return upcoming


@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    create_daily_tasks(current_user)

    today = date.today()
    tasks = TaskInstance.query.filter_by(
        user_id=current_user.id, 
        date=today
    ).all()

    # HISTORY (grouped by date)
    all_tasks = TaskInstance.query.filter_by(
        user_id=current_user.id
    ).order_by(TaskInstance.date.desc()).all()

    tasks_by_day = {}
    for t in all_tasks:
        tasks_by_day.setdefault(t.date, []).append(t)

    # TEMPLATES
    templates = TaskTemplate.query.filter_by(
        user_id=current_user.id
    ).all()

    # Handle marking tasks done
    if request.method == 'POST':
        for task in tasks:
            if f"done-{task.id}" in request.form:
                if not task.done:
                    task.done = True
                    task.completed_at = datetime.now()
            task.description = request.form.get(
                f"description-{task.id}",
                task.description,
            )
        db.session.commit()
        return redirect(url_for("index"))

    upcoming = get_upcoming_tasks(current_user)

    return render_template(
        'dashboard.html',
        tasks=tasks,
        templates=templates,
        tasks_by_day=tasks_by_day,
        upcoming=upcoming,
    )

if __name__ == '__main__':
    app.run()
