import os
from tkinter import W

from flask import Flask, redirect, render_template, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
    basedir, "registration.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullName = db.Column(db.String(100), nullable=False)
    phoneNumber = db.Column(db.String(10), nullable=False)
    emailId = db.Column(db.String(120), nullable=False)
    organization = db.Column(db.String(100), nullable=False)


@app.route("/")
def homepage():
    return render_template("index.html")


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/digiform", methods=["GET", "POST"])
def digiform():
    fullName = request.form["fullName"]
    phoneNumber = request.form["phoneNumber"]
    emailId = request.form["emailId"]
    organization = request.form["organization"]

    registration = Registration(
        fullName=fullName,
        phoneNumber=phoneNumber,
        emailId=emailId,
        organization=organization,
    )
    db.session.add(registration)
    db.session.commit()
    return redirect("http://127.0.0.1:7860/")


with app.app_context():
    print("Creating database tables...")
    db.create_all()
    print("Database tables created.")

if __name__ == "__main__":
    app.run(debug=True)
