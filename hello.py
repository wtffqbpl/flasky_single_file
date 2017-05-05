#!/usr/bin/env python
# coding:utf-8
# Author: Yuanjun Ren

import os
from threading import Thread
from flask import Flask, render_template, session, redirect, url_for, flash
from flask_script import Manager
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import Required
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message


# define forms.
class NameForm(FlaskForm):
    name = StringField("What is your name?", validators=[Required()])
    submit = SubmitField("Submit")


# define some attributes of app.
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)


app.config["SECRET_KEY"] = "hard to guess string"
# database
app.config["SQLALCHEMY_DATABASE_URI"] = \
    "sqlite:///" + os.path.join(basedir, "data.sqlite")
app.config["SQLALCHEMY_COMMIT_ON_TEARDOWN"] = True
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# mail
app.config["FLASKY_MAIL_SUBJECT_PREFIX"] = '[Flasky]'
app.config["FLASKY_MAIL_SENDER"] = "Flask Admin <ren8777153@126.com>"
app.config["MAIL_SERVER"] = "smtp.126.com"
app.config["MAIL_PORT"] = 25
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "ren8777153@126.com"
app.config["MAIL_PASSWORD"] = "ren513401873"
app.config["FLASKY_ADMIN"] = "ren8777153@126.com"

# app attributes.
manager = Manager(app)
bootstrap = Bootstrap(app)
moment = Moment(app)
db = SQLAlchemy(app)
mail = Mail(app)

# Define database model
class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship("User", backref="role", lazy="dynamic")

    def __repr__(self):
        return "<Role %r>" % self.name


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"))

    def __repr__(self):
        return "<User %r>" % self.username


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_mail(to, subject, template, **kwargs):
    msg = Message(app.config["FLASKY_MAIL_SUBJECT_PREFIX"] + subject,
                  sender=app.config["FLASKY_MAIL_SENDER"], recipients=[to])
    msg.body = render_template(template + ".txt", **kwargs)
    msg.html = render_template(template + ".html", **kwargs)
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr


# define routers.
@app.route("/", methods=["GET", "POST"])
def index():
    form = NameForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()
        if user is None:
            user = User(username=form.name.data)
            db.session.add(user)
            session['known'] = False
        else:
            session['known'] = True
        session['name'] = form.name.data
        form.name.data = ""
        return redirect(url_for("index"))
    return render_template("index.html",
                           form=form,
                           name=session.get("name"),
                           known=session.get("known", False))


@app.route("/sendmail", methods=["POST", "GET"])
def send_email():
    form = NameForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()
        if user is None:
            user = User(username=form.name.data)
            db.session.add(user)
            session['known'] = False
            if app.config["FLASKY_ADMIN"]:
                # send_mail(app.config["FLASKY_ADMIN"], "New User",
                send_mail(app.config["FLASKY_ADMIN"], "New User", "mail/new_user", user=user)
        else:
            session["known"] = True
        session['name'] = form.name.data
        form.name.data = ""
        return redirect(url_for("send_email"))
    return render_template("index.html", form=form, name=session.get("name"),
                           known=session.get("known", False))


@app.route("/user/<name>")
def user(name):
    return render_template("user.html", name=name)


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html"), 500


if __name__ == "__main__":
    manager.run()
