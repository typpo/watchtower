#!/usr/bin/env python

from flask import Flask, request, redirect, session, url_for, render_template, Response, g, flash, Markup, jsonify, json
from flask.ext.openid import OpenID
from datetime import datetime
from urlparse import urlparse, urljoin
from BeautifulSoup import BeautifulSoup
from threading import Thread
#from twython import Twython
import time
import praw
import json
import random
import os
import sys
from operator import attrgetter, add

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from core.models import Element, Version, Twitter, Page, User
from core.database import db
from core.fingerprint import get_fingerprints
from core.utils import get_blob, is_production, login_required, must_own_page

def create_app():
  app = Flask(__name__)
  app.secret_key = 'not a secret key'
  app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/watchtower.db'
  db.init_app(app)
  return app

"""
class TwythonOld(Twython):
  def oldSearch(self, **kwargs):
    return self.get('https://search.twitter.com/search.json', params=kwargs)
    """

reddit = praw.Reddit(user_agent='test')
#twitter = Twython()
app = create_app()

oid = OpenID(app, '/tmp/openid')

@app.route("/")
def index():
  pages = Page.query.all()
  app.logger.debug(pages)
  if g.user:
    return render_template('dashboard.html', user=g.user, pages=list(g.user.pages))
  else:
    return render_template('index.html', user=g.user)

@app.route('/about')
def about():
  return render_template('about.html')

@app.route('/page/<int:page_id>', methods=['GET'])
@must_own_page
def show_page(page):
  versions = reduce(add, [[version for version in element.versions[1:]] for element in page.elements], [])
  versions = sorted(versions, key=attrgetter('when'))
  app.logger.debug(page.last_view)
  for version in versions:
    version.diff = json.loads(version.diff)
  unchanged_elements = [element for element in page.elements if len(list(element.versions)) <= 1]
  page.last_view = datetime.utcnow()
  db.session.add(page)
  db.session.commit()
  return render_template('page.html', page=page, versions=versions, unchanged_elements=unchanged_elements)

@app.route('/page/new', methods=['GET', 'POST'])
def new_page():
  if request.method == 'GET':
    url = request.args.get('url')
    return render_template('new_page.html', url=url)

  for p in ['url', 'name']:
    if p not in request.form:
      return jsonify(error='missing %s param' % p)

  url = request.form.get('url')
  if not url.startswith('http'):
    url = 'http://' + url   # otherwise links to this url are interpreted as relative
  page_name = request.form.get('name')
  page = Page(name=page_name, url=url, user_id=g.user.id if g.user else None)
  db.session.add(page)
  # save everything in the db
  db.session.commit()

  # redirect to page for this page
  return redirect('page/%s/edit' % page.id)

@app.route('/preview', methods=['GET'])
def preview():
  url = request.args.get('url')
  if g.user:
    return redirect(url_for('new_page', url=url))
  return render_template('edit_page.html', url=url, preview=True)

@app.route('/page/<int:page_id>/edit', methods=['GET', 'POST'])
@must_own_page
def edit_page(page):
  if request.method == 'GET':
    # Show page
    selectors = [el.selector for el in page.elements]
    names = [el.name for el in page.elements]
    elements = page.elements
    return render_template('edit_page.html', page=page, url=page.url,
                           elements=page.elements,
                           selectors=selectors, names=names)

  # Update page
  try:
    selectors = json.loads(request.args.get('selectors'))
    selector_names = json.loads(request.args.get('names'))
    delete = json.loads(request.args.get('delete', '[]'))
  except ValueError:
    return jsonify(error='invalid json')
  except TypeError:
    return jsonify(form=repr(request.form))

  # it's ok to delete but not add
  #if not selectors:
  #  return jsonify(error='must supply one or more selectors')
  if len(selector_names) != len(selectors):
    return jsonify(error='must have same number of names and selectors')

  # get fingerprints
  fingerprints, screenshot_url, screenshot_local = get_fingerprints(page.url, selectors)
  now = datetime.utcnow()

  # delete elements
  for element_id in delete:
    element = Element.query.filter_by(id=element_id).first()
    if not element:
      return jsonify(error='invalid element id')
    db.session.delete(element)

  # add new selections
  for name, selector, fingerprint in zip(selector_names, selectors, fingerprints):
    element = Element(name=name, selector=selector, page=page)
    version = Version(fingerprint=json.dumps(fingerprint), diff='', when=now,\
        element=element, screenshot=screenshot_url)
    db.session.add(element)
    db.session.add(version)
  db.session.commit()

  return redirect('/page/%d' % page.id)

@app.route('/page/<int:page_id>/delete', methods=['GET', 'POST', 'DELETE'])
@must_own_page
def delete_page(page):
  db.session.delete(page)
  db.session.commit()
  return redirect('/')


@app.route('/proxy')
def proxy():
  data = request.data
  url = request.args.get('url')
  if (url[:3] != 'htt'):
    url = 'http://' + url

  html = get_blob(url)

  if html is None:
    return 'Invalid url'

  """
  soup = BeautifulSoup(html)
  for a in soup.findAll('a'):
    a['href'] = urljoin(a['href'], real_url)
  for img in soup.findAll('img'):
    img['src'] = urljoin(img['src'], real_url)

  return render_template('proxy.html', html=str(soup), root=real_url, )
  """
  watchtower_content_root = 'http://gowatchtower.com' if is_production() else 'http://localhost:5000'
  ts = time.time()
  return render_template('proxy.html', html=html, root=url, \
      watchtower_content_root=watchtower_content_root, timestamp=ts)

@app.before_request
def lookup_current_user():
  db.create_all() # TODO remove this once db is stable
  g.user = None
  if 'openid' in session and session['openid']:
    g.user = User.query.filter_by(openid=session['openid']).first()

@oid.after_login
def create_or_login(resp):
    session['openid'] = resp.identity_url
    user = User.query.filter_by(openid=resp.identity_url).first()
    if user is None:
      g.user = User(resp.fullname or resp.nickname, resp.email, session['openid'])
      db.session.add(g.user)
      db.session.commit()
      user = g.user
    return redirect(oid.get_next_url())

@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
  if (g.user is not None):
    return redirect(oid.get_next_url())
  if 'openid' in request.args:
    openid = request.args['openid']
    return oid.try_login(openid, ask_for=['email', 'fullname',
                                          'nickname'])
  return render_template('login.html', next=oid.get_next_url(),
              error=oid.fetch_error())

def add_sub_reddit(reddits, sub, search):
  if (not search in reddits):
    reddits[search] = []
  submissions = reddit.get_subreddit(sub).search(search, limit = 5)
  for sub in submissions:
    reddits[search].append( (sub.url, sub.title ))
  return reddits


@app.route('/profile', methods=['GET', 'POST'])
def edit_profile():
  form = dict(name=g.user.name, email=g.user.email)
  feed = []
#  for tweet in g.user.twitters:
#    feed.append(twitter.getUserTimeline(screen_name=tweet.handle))
  fb = [] #get_blob('https://graph.facebook.com/google/feed')
  reddits = {}
  for red in g.user.pages:
    reddits = add_sub_reddit(reddits, 'worldnews', red.name)
    reddits = add_sub_reddit(reddits, 'technology', red.name)
    reddits = add_sub_reddit(reddits, 'news', red.name)
  #news=get_blob('https://api.usatoday.com/open/articles/topnews?search=google&api_key=asgn54b69rg7699v5skf8ur9')
  if request.method == 'POST':
    twitadd = Twitter(request.form['addtweets'], user_id=g.user.id)
    db.session.add(twitadd)
    request.form['addtweets'] == ''
    # save everything in the db
    db.session.commit()
  return render_template('edit_profile.html', reddit=reddits, fb=fb, feed=feed, form=form, next=oid.get_next_url)

@app.route('/logout')
def logout():
  g.user = None
  session['openid'] = None
  session.pop('openid', None)
  return redirect(url_for('index', user=None))

@app.route('/test')
def test():
  return render_template('test_goog.html',
      random=random.randint(50, 1000),
      randcolor=[random.randint(0, 255),random.randint(0, 255),random.randint(0, 255)])

if __name__ == "__main__":
  app.run(debug=True, host='0.0.0.0', use_reloader=True)
