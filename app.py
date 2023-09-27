import sqlite3
from dotenv import load_dotenv
from flask import Flask, render_template, request
import os
import requests


app = Flask(__name__)


conn = sqlite3.connect("weather.db", check_same_thread=False)
db = conn.cursor()

db.execute(
    '''CREATE TABLE IF NOT EXISTS cities ( 
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    weather TEXT NOT NULL, 
    description TEXT NOT NULL, 
    icon TEXT NOT NULL, 
    temperature NUMERIC NOT NULL, 
    temperature_feels_like NUMERIC NOT NULL, 
    humidity NUMERIC NOT NULL, 
    wind_speed NUMERIC NOT NULL, 
    wind_direction NUMERIC NOT NULL, 
    country TEXT NOT NULL, 
    city TEXT NOT NULL)'''
)
conn.commit()


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template("index.html")


@app.route("/remove", methods=["GET", "POST"])
def remove():
    if request.method == "POST":
        for key, value in request.form.items():
            history = delete(value)
            return render_template("locations.html", history=history)


@app.route("/location", methods=["GET", "POST"])
def location():
    configure()

    if request.method == "GET":
        db = conn.cursor()
        db.execute("SELECT * FROM cities ORDER BY id DESC")
        history = db.fetchall()
        # db.close()
        return render_template("locations.html", history=history)

    if request.method == "POST":

        # get location from input
        location = request.form.get("location").title()

        # get data from API
        data = get_location(location)

        # get stored locations from SQL
        db = conn.cursor()
        db.execute("SELECT * FROM cities ORDER BY id DESC")
        history = db.fetchall()

        # display message for not valid city
        if (data['cod'] == '404'):
            return render_template("locations.html", message=">>>Not a valid city<<<", history=history)

        store_location_to_SQL(data)
        db = conn.cursor()
        db.execute("SELECT * FROM cities ORDER BY id DESC")
        history = db.fetchall()

        if not location:
            return render_template("locations.html", message=">>>Enter location<<<", history=history)
        else:
            return render_template("locations.html", history=history)
    else:
        return render_template("locations.html", history=history)


def get_location(location):
    response = requests.get(
        f"https://api.openweathermap.org/data/2.5/weather?q={location}&units=metric&appid={os.getenv('API_KEY')}"
    )
    data = response.json()
    return data


def store_location_to_SQL(data):

    # store location data in SQL
    try:
        weather = data["weather"][0]["main"]
        description = data["weather"][0]["description"]
        icon = data["weather"][0]["icon"]
        temperature = round(data["main"]["temp"], 1)
        temperature_feels_like = round(data["main"]["feels_like"], 1)
        humidity = data["main"]["humidity"]
        wind_speed = round(data["wind"]["speed"], 1)
        wind_direction = data["wind"]["deg"]
        country = data["sys"]["country"].lower()
        city = data["name"]

        db = conn.cursor()
        db.execute(
            '''INSERT INTO cities (
            weather, description, icon, temperature, temperature_feels_like, humidity, wind_speed, wind_direction, country, city
            ) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (weather,
             description,
             icon,
             temperature,
             temperature_feels_like,
             humidity,
             wind_speed,
             wind_direction,
             country,
             city)
        )
        conn.commit()

        return
    except KeyError as e:
        conn.rollback()
        return render_template("locations.html", message=">>>Not a valid city<<<")


def delete(value):
    db = conn.cursor()
    db.execute("DELETE FROM cities WHERE id = ?", value)
    conn.commit()
    db.execute("SELECT * FROM cities ORDER BY id DESC")
    new_base = db.fetchall()

    return new_base

# .env file configuration
def configure():
    load_dotenv()
