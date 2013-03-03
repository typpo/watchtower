#!/usr/bin/env python

from flask import Flask, request, redirect, session, url_for, render_template, Response, g, flash, Markup
from flask.ext.openid import OpenID
import urllib
import urlparse
import json
import random
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from core.models import User

app = Flask(__name__)
app.secret_key = 'not a secret key'
oid = OpenID(app, 'temp/openid')

@app.route("/")
def index():
  app.logger.debug(g.user)
  return render_template('index.html', user=g.user)

@app.route('/placeholder')
def placeholder():
  query = request.args.get('query')
  json_resp = json.dumps({'foo': 'bar'})
  return Response(json_resp, mimetype='application/json')

@app.route('/proxy')
def proxy():
  data = request.data
  google = 'www.google.com'
  response = urllib.urlopen('http://' + google)
  html = Markup(response.read())
  return render_template('proxy.html', html=html)

@app.before_request
def lookup_current_user():
  g.user = None
  if 'openid' in session:
    g.user = User.query.filter_by(openid=openid).first()

@oid.after_login
def create_or_login(resp):
    session['openid'] = resp.identity_url
    user = User.query.filter_by(openid=resp.identity_url).first()
    if user is not None:
        flash(u'Successfully signed in')
        g.user = user
        return redirect(oid.get_next_url())
    return redirect(url_for('create_profile', next=oid.get_next_url(),
                            name=resp.fullname or resp.nickname,
                            email=resp.email))

@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
  if g.user is not None:
    return redirect(oid.get_next_url())
  if request.method == 'POST':
    openid = request.form.get('openid')
    if openid:
      return oid.try_login(openid, ask_for=['email', 'fullname',
                                            'nickname'])
  return render_template('index.html', next=oid.get_next_url(),
              error=oid.fetch_error())

@app.route('/test')
def test():
  return render_template('test_goog.html',
      random=random.randint(50, 1000),
      randcolor=[random.randint(0, 255),random.randint(0, 255),random.randint(0, 255)])

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', use_reloader=True)
