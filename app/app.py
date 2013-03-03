#!/usr/bin/env python

from flask import Flask, request, redirect, session, url_for, render_template, Response, g, flash, Markup, jsonify, json
from flask.ext.openid import OpenID
from datetime import datetime
from urlparse import urlparse, urljoin
from BeautifulSoup import BeautifulSoup
from threading import Thread
import time
import json
import random
import os
import sys
from operator import attrgetter, add

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from core.models import Element, Version, Page, User
from core.database import db
from core.fingerprint import get_fingerprints
from core.utils import get_blob

def create_app():
  app = Flask(__name__)
  app.secret_key = 'not a secret key'
  app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/watchtower.db'
  db.init_app(app)
  return app

app = create_app()

oid = OpenID(app, 'temp/openid')

@app.route("/")
def index():
  db.create_all()
  app.logger.debug(g.user)
  pages = Page.query.all()
  app.logger.debug(pages)
  return render_template('index.html', user=g.user, pages=pages, next=oid.get_next_url())

@app.route('/new_page', methods=['GET', 'POST'])
def new_page():
  if request.method == 'GET':
    return render_template('edit_page.html')

  for p in ['url', 'name', 'selectors', 'names']:
    if p not in request.form:
      return jsonify(error='missing %s param' % p)

  url = request.form.get('url')
  page_name = request.form.get('name')
  page = Page(name=page_name, url=url)
  db.session.add(page)
  selectors = json.loads(request.form.get('selectors'))
  selector_names = json.loads(request.form.get('names'))

  print url, page_name, selectors, selector_names

  if len(selector_names) != len(selectors):
    return jsonify(error='must have same number of names and selectors')

  thread = Thread(target=add_page, args=(page, selectors, selector_names))
  thread.start()

  # save everything in the db
  db.session.commit()

  # redirect to page for this page
  return redirect(url_for('page', page_id=page.id))
  #return json.dumps([url, page_name, selectors, selector_names])

def add_page(page, selectors, selector_names):
  fingerprints = get_fingerprints(page.url, selectors)
  now = datetime.utcnow()
  for name, selector, fingerprint in zip(selector_names, selectors, fingerprints):
    element = Element(name=name, selector=selector, page=page)
    version = Version(fingerprint=json.dumps(fingerprint), diff='', when=now, element=element)
    db.session.add(element)
    db.session.add(version)
  db.session.commit

@app.route('/page/<int:page_id>')
def page(page_id):
  page = Page.query.filter_by(id=page_id).first()
  if not page:
    return jsonify(error='invalid page id')
  versions = reduce(add, [[version for version in element.versions[1:]] for element in page.elements])
  versions = sorted(versions, key=attrgetter('when'))
  for version in versions:
    version.diff=json.loads(version.diff)
  return render_template('page.html', page=page, versions=versions)

@app.route('/proxy')
def proxy():
  data = request.data
  url = request.args.get('url')
  if (url[:3] != 'htt'):
    url = 'http://' + url
  if (url[7:10] != 'www'):
    url = url[:7] + 'www.' + url[7:]

  html = get_blob(url)

  """
  soup = BeautifulSoup(html)
  for a in soup.findAll('a'):
    a['href'] = urljoin(a['href'], real_url)
  for img in soup.findAll('img'):
    img['src'] = urljoin(img['src'], real_url)

  return render_template('proxy.html', html=str(soup), root=real_url, )
  """
  watchtower_content_root = 'http://localhost:5000'   # TODO changeme
  ts = time.time()
  return render_template('proxy.html', html=html, root=url, \
      watchtower_content_root=watchtower_content_root, timestamp=ts)

@app.before_request
def lookup_current_user():
  g.user = None
  if 'openid' in session:
    g.user = User.query.filter_by(openid=session['openid']).first()

@oid.after_login
def create_or_login(resp):
    session['openid'] = resp.identity_url
    user = User.query.filter_by(openid=resp.identity_url).first()
    if user is not None:
        flash(u'Successfully signed in')
        g.user = user
        g.user.name = resp.fullname or resp.nickname
        g.user.email = resp.email
        return redirect(url_for('edit_profile', name=resp.fullname or resp.nickname, email=resp.email, next=oid.get_next_url()))
    return redirect(url_for('create_profile', next=oid.get_next_url(),
                            name=resp.fullname or resp.nickname,
                            email=resp.email))

@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
  if (g.user is not None):
    return redirect(oid.get_next_url())
  if request.method == 'POST':
    openid = request.form['openid']
    if openid:
      return oid.try_login(openid, ask_for=['email', 'fullname',
                                            'nickname'])
  return render_template('login.html', next=oid.get_next_url(),
              error=oid.fetch_error())

@app.route('/create_profile', methods=['GET', 'POST'])
def create_profile():
  if request.method == 'POST':
    name = request.form['name']
    email = request.form['email']
    g.user = User(name,email,session['openid'])
    db.session.add(g.user)
    db.session.commit()
    return redirect(url_for('edit_profile', name=name, email=email, next=oid.get_next_url()))
  return render_template('create_profile.html', name=request.args.get('name'),
      email=request.args.get('email'), next=oid.get_next_url())

@app.route('/profile', methods=['GET', 'POST'])
def edit_profile():
  form = dict(name=request.args.get('name'), email = request.args.get('email'))
  if request.method == 'POST':
    if (form['name'] and form['email']):
      return redirect(oid.get_next_url())# url_for('edit_profile'))
  return render_template('edit_profile.html', form=form, next=oid.get_next_url)

@app.route('/logout')
def logout():
  g.user = None
  session.pop('openid', None)
  return redirect(oid.get_next_url())

@app.route('/test')
def test():
  return render_template('test_goog.html',
      random=random.randint(50, 1000),
      randcolor=[random.randint(0, 255),random.randint(0, 255),random.randint(0, 255)])

if __name__ == "__main__":
  app.run(debug=True, host='0.0.0.0', use_reloader=True)
