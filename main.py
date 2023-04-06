import os

from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, session, url_for

from news import News, NewsFeed

load_dotenv(".env.dev")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))
app.config.from_object("config")

CONF_URL = "https://accounts.google.com/.well-known/openid-configuration"
oauth = OAuth(app)
oauth.register(
    name="google",
    server_metadata_url=CONF_URL,
    client_kwargs={"scope": "openid email profile"},
)


@app.route("/")
def homepage():
    user = session.get("user")
    newsfeed = NewsFeed().get_all_news()
    return render_template("home.html", user=user, newsfeed=newsfeed)


@app.route("/edit")
def editpage():
    user = session.get("user")
    newsfeed = NewsFeed().get_all_news()
    return render_template("home.html", user=user, newsfeed=newsfeed, editMode=True)


@app.route("/news/add", methods=["POST"])
def add_news():
    if session.get("user") is None:
        return redirect("/login")
    if (
        session.get("user", {"email": "anon@anon.net"})
        .get("email", "anon@anon.net")
        .split("@")[-1]
        != "artefact.com"
    ):
        return redirect("/logout")
    # get link from post param
    if request.form.get("link") is not None:
        news = News(request.form.get("link", ""), session.get("user", {}))
        news.save()
    return redirect("/")


@app.route("/news/search", methods=["POST"])
def search_news():
    if request.form.get("query") is not None:
        newsfeed = NewsFeed().search(request.form.get("query", ""))
        return render_template("home.html", newsfeed=newsfeed, user=session.get("user"), query=request.form.get("query", ""))
    return redirect("/")


@app.route("/news/delete", methods=["POST"])
def delete_news():
    if session.get("user") is None:
        return redirect("/login")

    print(NewsFeed().delete(request.form.get("link")))
    return redirect("/")


@app.route("/login")
def login():
    redirect_uri = url_for("auth", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@app.route("/auth")
def auth():
    token = oauth.google.authorize_access_token()
    session["user"] = token["userinfo"]
    return redirect("/")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")
