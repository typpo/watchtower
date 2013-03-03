#!/usr/bin/env python

from flask import Flask, request, redirect, session, url_for, render_template, Response, g, flash, Markup, jsonify
from flask.ext.openid import OpenID
from flask.ext.sqlalchemy import SQLAlchemy
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
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/watchtower.db'
db = SQLAlchemy(app)

class Element(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  selector = db.Column(db.String(255), unique=True)
  page_id = db.Column(db.Integer, db.ForeignKey('page.id'))
  page = db.relationship('Page',
                         backref=db.backref('elements', lazy='dynamic'))

  def __init__(self, selector, page):
    self.selector = selector
    self.page = page

  def __repr__(self):
    return '<Element %r>' % self.selector

class Page(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  url = db.Column(db.String(1024))
  blob = db.Column(db.Text)
  
  def __init__(self, url, blob):
    self.url = url
    self.blob = blob

  def __repr__(self):
    return '<Page %r>' % self.url


@app.route("/")
def index():
  app.logger.debug(g.user)
  pages = Page.query.all()
  return render_template('index.html', user=g.user, pages=pages)

@app.route('/watch', methods=['POST'])
def watch():
  url = request.form.get('url')
  if url is None:
    return jsonify(error='missing url param')
  blob = request.form.get('blob')
  if blob is None:
    return jsonify(error='missing blob param')

  page = Page(url=url, blob=blob)

  selectors = request.form.getlist('selectors[]')
  if selectors is None:
    return jsonify(error='missing selectors params')
  
  elements = [Element(page=page, selector=selector) for selector in selectors]

  # save everything in the db
  db.session.add(page)
  for element in elements:
    db.session.add(element)

  return jsonify(success='ok')

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

db.create_all()

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', use_reloader=True)
