#!/usr/bin/env python3

# app.py
# Heroku Minima
# implemented by by Terzo Technical
# Cooyright (c) 2024 Shannon Douglas Ware 

# DopamineMenu.net
# Copyright (c) 2026 Shannon Dougkas Ware

from flask import Flask
from datetime import datetime
from flask import render_template

# Python standard libraries
import json
import os
import sqlite3

# Third-party libraries
from flask import redirect, request, url_for
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from oauthlib.oauth2 import WebApplicationClient
import requests

# Internal imports
from db import init_db_command
from user import User

# Player G
from flask import g
import pprint

# Configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

class Player:
	page_title = "Index"
	date = datetime.now().strftime("%A, %d %B %Y")
	c_user_is_auth = False
	# c_user_type = type(current_user)
	c_user = current_user
	user_textarea = "Ready"


def write_t_log(log_update: str) -> bool:
	# Append local fike with text as provided
	f_name = f"logs/t_log_{datetime.now().strftime("%Y%m%d")}.txt"
	n_date = str(datetime.now().strftime("%d %B %Y %H:%M:%S\n"))
	t_log = n_date + log_update + "\n"
	if not os.path.exists(f_name):
		with open(f_name, "w") as fhandler:
			fhandler.write(t_log)
	else:
		with open(f_name, "a") as fhandler:
			fhandler.write(t_log)
	return True


app = Flask(__name__)
p = Player()
# Flask app setup
# app = Flask(__name__)


#app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)
try:
	app.secret_key = os.environ.get("SECRET_KEY")
	write_t_log("Secret key acquired.")
except Exception as e:
	failure_log = "Secret key acquisition\n" + e
	write_t_log(failure_log)


# User session management setup
# https://flask-login.readthedocs.io/en/latest
login_manager = LoginManager()
login_manager.init_app(app)

# Naive database setup
"""try:
    init_db_command()
except sqlite3.OperationalError:
    # Assume it's already been created
    pass"""

# OAuth 2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)


# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()


@app.route("/login/callback")
def callback():
	t_log = str(datetime.now().strftime("%A, %d %B %Y - %H:%M:%S"))
	try:
		# Get authorization code Google sent back to you
		code = request.args.get("code")
		t_log += "\nCode acquired"

		# Find out what URL to hit to get tokens that allow you to ask for
		# things on behalf of a user
		google_provider_cfg = get_google_provider_cfg()
		token_endpoint = google_provider_cfg["token_endpoint"]
		t_log += "\nProvider configuration and token endpoint acquired"

		# Prepare and send a request to get tokens! Yay tokens!
		token_url, headers, body = client.prepare_token_request(
			token_endpoint,
			authorization_response=request.url,
			redirect_url=request.base_url,
			code=code
		)
		t_log += "\nToken URL, headers anf body acquired"
		token_response = requests.post(
			token_url,
			headers=headers,
			data=body,
			auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
		)
		t_log += "\nToken response acquired"

		# Parse the tokens!
		client.parse_request_body_response(json.dumps(token_response.json()))
		t_log += "\nToken parsed"

		# Now that you have tokens (yay) let's find and hit the URL
		# from Google that gives you the user's profile information,
		# including their Google profile image and email
		userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
		uri, headers, body = client.add_token(userinfo_endpoint)
		userinfo_response = requests.get(uri, headers=headers, data=body)
		t_log += "\nUserinfo endpoint and response acquired"

		# You want to make sure their email is verified.
		# The user authenticated with Google, authorized your
		# app, and now you've verified their email through Google!
		if userinfo_response.json().get("email_verified"):
			unique_id = userinfo_response.json()["sub"]
			users_email = userinfo_response.json()["email"]
			picture = userinfo_response.json()["picture"]
			users_name = userinfo_response.json()["given_name"]
			t_log += "\nUser response email acquired"
		else:
			write_t_log(t_log)
			return "User email not available or not verified by Google.", 400

		# Create a user in your db with the information provided
		# by Google
		user = User(
			id_=unique_id, name=users_name, email=users_email, profile_pic=picture
		)
		t_log += "\nUser credentials assigned"

		# Doesn't exist? Add it to the database.
		if not User.get(unique_id):
			User.create(unique_id, users_name, users_email, picture)
			t_log += "\nUser details added to local DB"

		# Begin user session by logging the user in
		login_user(user)
		t_log += "\nUser login completed"

		# Send user back to homepage
		# return redirect(url_for("index"))
		t_log += "\nRedirecting to homepage"
		write_t_log(t_log)
		return redirect(url_for("user"))
	except Exception as e:
		t_log += "\nException caught"
		# write_t_log(t_log)
		return f"Error: {str(e)}", 500
	finally:
		# Write!
		# write_t_log(t_log)
		pass

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/user", methods=('GET', 'POST'))
@login_required
def user():
	#return "User input page"
	# user_textarea
	if request.method == 'POST':
		p.user_textarea = request.form['user_textarea']
	return render_template("user.html", p=p)


@app.route("/")
def home():
	#return f"Test 22 {datetime.now()}"
	p.page_title = "Welcome!"
	p.c_user_is_auth = current_user.is_authenticated
	write_t_log("DM.net index page loaded")
	return render_template('index.html', p=p)


@app.route("/login")
def login():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)


@app.route("/terms")
def terms():
	p.page_title = "Terms and Conditions"
	return render_template('terms.html', p=p)


@app.route("/privacy")
def privacy():
	p.page_title = "Privacy Policy"
	return render_template('index.html', p=p)


@app.route("/contact")
def contact():
	p.page_title = "Contact Us (Imprint)"
	return render_template('index.html', p=p)


@app.route("/settings")
def settings():
	p.page_title = "Settings"
	return render_template('index.html', p=p)


@app.route("/design")
def design():
	p.page_title = "Design"
	return render_template('design.html', p=p)


@app.route("/g")
def player_g():
	p.page_title = "Player G"
	test_dict = {"alpha": "Alpha", "beta": "Beta", "gamma": "Gamma", "delta": "Delta"}
	player_g = pprint.pformat(vars(g))
	#player_g = pprint.pformat(test_dict)
	return render_template('player_g.html', p=p, player_g=player_g)


if __name__ == '__main__':
    app.run() 
