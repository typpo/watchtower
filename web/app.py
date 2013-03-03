#!/usr/bin/env python

from flask import Flask, request, redirect, session, url_for, render_template, Response, g, flash, Markup, jsonify
from flask.ext.openid import OpenID
from datetime import datetime
from urlparse import urlparse, urljoin
from BeautifulSoup import BeautifulSoup
import json
import random
import os
import sys
from operator import attrgetter, add

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from core.models import Element, Version, Page, User
from core.database import db
from core.fingerprint import get_fingerprints

app = Flask(__name__)
app.secret_key = 'not a secret key'
db.init_app(app)
oid = OpenID(app, 'temp/openid')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/watchtower.db'

@app.route("/")
def index():
  db.create_all()
  app.logger.debug(g.user)
  pages = Page.query.all()
  app.logger.debug(pages)
  return render_template('index.html', user=g.user, pages=pages)

@app.route('/watch', methods=['POST'])
def watch():
  for p in ['url', 'name', 'selectors[]', 'names[]']:
    if p not in request.form:
      return jsonify(error='missing %s param' % p)

  url = request.form.get('url')
  page_name = request.form.get('name')
  page = Page(name=page_name, url=url)
  db.session.add(page)
  selectors = request.form.getlist('selectors[]')
  selector_names = request.form.getlist('names[]')
  fingerprints = get_fingerprints(url, selectors)

  if len(selector_names) != len(selectors):
    return jsonify(error='must have same number of names and selectors')

  now = datetime.utcnow()
  for name, selector, fingerprint in zip(selector_names, selectors, fingerprints):
    element = Element(name=name, selector=selector, page=page)
    version = Version(fingerprint=fingerprint, diff='', when=now, element=element)
    db.session.add(element)
    db.session.add(version)

  # save everything in the db
  db.session.commit()

  return jsonify(success='ok')

@app.route('/page/<int:page_id>')
def page(page_id):
  page = Page.query.filter_by(id=page_id).first()
  if not page:
    return jsonify(error='invalid page id')
  versions = reduce(add, [[version for version in element.versions[1:]] for element in page.elements])
  versions = sorted(versions, key=attrgetter('when'))
  return render_template('page.html', page=page, versions=versions)

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
  html = getBlob(url)

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

@app.route('/test')
def test():
  return render_template('test_goog.html',
      random=random.randint(50, 1000),
      randcolor=[random.randint(0, 255),random.randint(0, 255),random.randint(0, 255)])

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', use_reloader=True)
