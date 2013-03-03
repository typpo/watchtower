#!/usr/bin/env python

from flask import Flask, request, redirect, session, url_for, render_template, Response, g, flash, Markup, jsonify
from flask.ext.openid import OpenID
import urllib
import requests
from urlparse import urlparse, urljoin
from BeautifulSoup import BeautifulSoup
import json
import random
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from core.models import Element, Page, User
from core.database import db

app = Flask(__name__)
app.secret_key = 'not a secret key'
db.init_app(app)
oid = OpenID(app, 'temp/openid')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/watchtower.db'

@app.route("/")
def index():
  app.logger.debug(g.user)
  pages = Page.query.all()
  app.logger.debug(pages)
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
  db.session.commit()

  return jsonify(success='ok')

@app.route('/placeholder')
def placeholder():
  query = request.args.get('query')
  json_resp = json.dumps({'foo': 'bar'})
  return Response(json_resp, mimetype='application/json')

@app.route('/proxy')
def proxy():
  data = request.data
  url = request.args.get('url')
  parsed = urlparse(url)
  real_url = url
  if (parsed.netloc[:3] != 'www'):
    real_url = parsed.scheme + '://www.' + parsed.netloc
  html = getHtml(url)

  """
  soup = BeautifulSoup(html)
  for a in soup.findAll('a'):
    a['href'] = urljoin(a['href'], real_url)
  for img in soup.findAll('img'):
    img['src'] = urljoin(img['src'], real_url)

  return render_template('proxy.html', html=str(soup), root=real_url, )
  """
  watchtower_content_root = 'http://localhost:5000'   # TODO changeme
  return render_template('proxy.html', html=html, root=real_url, \
      watchtower_content_root=watchtower_content_root)

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

def getHtml(url):
  return requests.get(url).text

@app.route('/test')
def test():
  return render_template('test_goog.html',
      random=random.randint(50, 1000),
      randcolor=[random.randint(0, 255),random.randint(0, 255),random.randint(0, 255)])

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', use_reloader=True)
