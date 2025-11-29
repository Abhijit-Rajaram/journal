from extensions import db, login_manager
from flask_login import UserMixin
from datetime import date

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    templates = db.relationship("TaskTemplate", backref="user", lazy=True)
    task_instances = db.relationship("TaskInstance", backref="user_instance", lazy=True)

class TaskTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    frequency = db.Column(db.String(20), default="daily")
    weekdays = db.Column(db.String(50))
    day_of_month = db.Column(db.Integer)
    specific_date = db.Column(db.Date)

class TaskInstance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey("task_template.id"))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    done = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    date = db.Column(db.Date, default=date.today)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
