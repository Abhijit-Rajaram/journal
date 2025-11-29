from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
from datetime import datetime, date

from extensions import db
from models import User, TaskTemplate, TaskInstance
from services import create_daily_tasks, get_upcoming_tasks
from werkzeug.security import check_password_hash

def register_routes(app):

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']

            if User.query.filter_by(username=username).first():
                flash("Username already exists!")
                return redirect(url_for('register'))

            user = User(username=username, password=User.hash_password(password))
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


    @app.route('/', methods=['GET', 'POST'])
    @login_required
    def index():
        create_daily_tasks(current_user)

        today = date.today()
        tasks = TaskInstance.query.filter_by(
            user_id=current_user.id, date=today
        ).all()

        all_tasks = TaskInstance.query.filter_by(
            user_id=current_user.id
        ).order_by(TaskInstance.date.desc()).all()

        tasks_by_day = {}
        for t in all_tasks:
            tasks_by_day.setdefault(t.date, []).append(t)

        templates = TaskTemplate.query.filter_by(user_id=current_user.id).all()

        if request.method == 'POST':
            for task in tasks:
                if f"done-{task.id}" in request.form and not task.done:
                    task.done = True
                    task.completed_at = datetime.now()

                task.description = request.form.get(
                    f"description-{task.id}", task.description
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
                specific_date = datetime.strptime(specific_date, "%Y-%m-%d").date()

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

