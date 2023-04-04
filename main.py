from flask import Flask, url_for, session, request
from flask import render_template, redirect
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv

import os

from news import News, NewsFeed

load_dotenv(".env.dev")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))
app.config.from_object('config')

CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'
oauth = OAuth(app)
oauth.register(
    name='google',
    server_metadata_url=CONF_URL,
    client_kwargs={
        'scope': 'openid email profile'
    }
)


@app.route('/')
def homepage():
    user = session.get('user')
    newsfeed = NewsFeed().get_all_news()
    return render_template('home.html', user=user, newsfeed=newsfeed)

@app.route('/news/add', methods=['POST'])
def add_news():
    if not session.get('user') or session.get('user')['email'].split("@")[-1] != "artefact.com":
        return redirect('/login')
    # get link from post param
    news = News(request.form.get("link"), session.get('user'))
    news.save()
    return redirect('/')

@app.route('/login')
def login():
    redirect_uri = url_for('auth', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@app.route('/auth')
def auth():
    token = oauth.google.authorize_access_token()
    session['user'] = token['userinfo']
    return redirect('/')


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')