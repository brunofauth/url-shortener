import secrets
import sqlite3
import flask
import os
import re


REGEX_URL = re.compile(r"^https?://[^\s/$.?#].[^\s]*$", re.I | re.S)


def get_db(db_path="shortener.db", schema_path="schema.sqlite"):
    if not hasattr(get_db, "db"):
        get_db._db = sqlite3.connect(db_path)
        with open(schema_path) as schema:
            get_db._db.execute(schema.read())
    return get_db._db


def validate_url(text):
    return REGEX_URL.match(text)


def insert_url_entry(url):
    INSERT_CMD = "INSERT INTO urls VALUES (?, ?, ?);"
    with get_db() as db:
        db.execute(INSERT_CMD, (secrets.token_urlsafe(8), url, 0))


app = flask.Flask(__name__)


@app.route('/', methods=["GET", "POST"])
def home():

    if flask.request.method == "GET":
        return flask.render_template("index.html", table_info=get_db().execute("SELECT * FROM urls;"))

    url = flask.request.form["url"]
    if validate_url(url):
        insert_url_entry(url)
        # This redirect is needed so that the user doesn't keep adding
        # database entries when reloading the page
        return flask.redirect(flask.url_for(home.__name__))

    return flask.render_template("badurl.html", table_info=get_db().execute("SELECT * FROM urls;"))


@app.route("/<string:url_id>")
def redirect_to_website(url_id):

    if url_id == "favicon.ico":
        flask.abort(404)

    with get_db() as db:
        query = db.execute("SELECT url, clicks FROM urls WHERE id=?;", (url_id,)).fetchone()

    if query is not None:
        with get_db() as db:
            db.execute("UPDATE urls SET clicks=? WHERE id=?", (query[1] + 1, url_id))
        return flask.redirect(query[0])

    return flask.render_template("badurl.html", table_info=get_db().execute("SELECT * FROM urls;"))

