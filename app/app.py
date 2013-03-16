#!/usr/bin/env python

from flask import Flask, request, redirect, session, url_for, render_template, Response, g, flash, Markup, jsonify, json
from flask.ext.openid import OpenID
from flask.ext.login import login_user, logout_user, current_user, login_required, LoginManager
from flaskext.bcrypt import Bcrypt
from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqlamodel import ModelView
from datetime import datetime
from urlparse import urlparse, urljoin
from threading import Thread
import twitter
#from twython import Twython
import time
import praw
import json
import random
import os
import sys
import bcrypt
import pytz
import templatetags
from operator import attrgetter, add

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.models import Element, Version, Twitter, Page, User
from core.database import db
from core.fingerprint import get_fingerprints
from core.utils import create_user, get_blob, is_production, login_required, must_own_page, login_hashed

def create_app():
  app = Flask(__name__)
  app.secret_key = 'not a secret key'
  app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////var/watchtower/watchtower.db'
  db.init_app(app)
  # admin setup
  admin = Admin(app)
  admin.add_view(ModelView(Page, db.session))
  class MyModelView(ModelView):
    def __init__(self, model, session, name=None, category=None, endpoint=None, url=None, **kwargs):
      for k, v in kwargs.iteritems():
          setattr(self, k, v)

      super(MyModelView, self).__init__(model, session, name=name, category=category, endpoint=endpoint, url=url)

    def is_accessible(self):
      # Logic
      return True
  #admin.add_view(MyModelView(Version, db.session, column_list=['id', 'foreign_key']))
  admin.add_view(ModelView(Version, db.session,))
  admin.add_view(ModelView(Element, db.session,))
  admin.add_view(ModelView(User, db.session,))
  return app

"""
class TwythonOld(Twython):
  def oldSearch(self, **kwargs):
    return self.get('https://search.twitter.com/search.json', params=kwargs)
    """

#reddit = praw.Reddit(user_agent='test')
twitter = twitter.Twitter(domain="search.twitter.com")
app = create_app()

oid = OpenID(app, '/tmp/openid')
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(id):
  db.create_all() # TODO remove this once db is stable
  g.user = User.query.filter_by(id=id).first()
  return g.user

app.jinja_env.filters['element_from_version'] = templatetags.filter_element_from_version
app.jinja_env.filters['page_from_element'] = templatetags.filter_page_from_element
app.jinja_env.filters['page_from_version'] = templatetags.filter_page_from_version
app.jinja_env.filters['to_local_datetime'] = templatetags.filter_to_local_datetime
app.jinja_env.globals['localize_with_tz'] = templatetags.fn_localize_with_tz


@app.route("/", methods=['GET', 'POST'])
def index():
  pages = Page.query.all()
  if g.user:
    app.logger.debug(pages)
    if (request.method =="POST"):
      app.logger.debug(g.user)
      add = request.form['addtweets']
      if (add[0] != '#'):
        add = '#' + add
      twitadd = Twitter(add, user_id=g.user.id)
      db.session.add(twitadd)
      request.form['addtweets'] == ''
      # save everything in the db
      db.session.commit()
    news_feed = []

    pages = g.user.pages
    all_versions = []
    elementid_to_element = {}
    for page in pages:
      page_versions = []
      for element in page.elements:
        elementid_to_element[element.id] = element
        page_versions.extend(element.versions)
      all_versions.extend(page_versions)
    all_versions = sorted(all_versions, key=attrgetter('when'), reverse=True)
    print elementid_to_element
    return render_template('dashboard.html', user=g.user, pages=pages, \
        all_versions=all_versions, element_map=elementid_to_element)
  else:
    return render_template('index.html', user=g.user)

@app.route('/about')
def about():
  return render_template('about.html')

@app.route('/pricing')
def pricing():
  return render_template('pricing.html')

@app.route('/page/<int:page_id>', methods=['GET'])
@must_own_page
def show_page(page):
  versions = reduce(add, [[version for version in element.versions] for element in page.elements], [])
  versions = sorted(versions, key=attrgetter('when'), reverse=True)
  app.logger.debug(page.last_view)
  unchanged_elements = [element for element in page.elements if len(list(element.versions)) <= 1]
  page.last_view = datetime.utcnow()
  db.session.add(page)
  db.session.commit()
  for version in versions:
    # unserialize json when we pass it to page
    try:
      version.diff = json.loads(version.diff)  # version.diff is actually an array of diffs
      version.diff = [diff for diff in version.diff \
          if not isinstance(diff, basestring) and diff['key'].strip() != '']
    except ValueError:
      version.diff = {}
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
  fingerprints, screenshot_url, screenshot_local = get_fingerprints(page.url, selectors, record_screenshot=True)
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

  watchtower_content_root = 'http://gowatchtower.com' if is_production() else 'http://localhost:5000'
  ts = time.time()
  return render_template('proxy.html', html=html, root=url, \
      watchtower_content_root=watchtower_content_root, timestamp=ts)

@app.before_request
def lookup_current_user():
  db.create_all() # TODO remove this once db is stable
  #todo add in other type
  g.user = None
  if (current_user and current_user.is_authenticated()):
    g.user = current_user
    return
  if 'openid' in session and session['openid']:
    g.user = User.query.filter_by(openid=session['openid']).first()


@oid.after_login
def create_or_login(resp):
  session['openid'] = resp.identity_url
  user = User.query.filter_by(openid=resp.identity_url).first()
  if user is None:
    g.user = create_user(bcrypt=bcrypt, email=resp.email, password=None, timezone=resp.timezone, openid=session['openid'])
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
                                          'nickname', 'timezone'])
  if request.method == 'POST':
    user_exists = User.query.filter_by(email=request.form['email']).first()
    if not user_exists:
      try:
        timezone = pytz.timezone(request.form['timezone']).zone
      except pytz.exceptions.UnknownTimeZoneError:
        timezone = 'America/Los_Angeles'
      try:
        g.user = create_user(bcrypt=bcrypt, email=request.form['email'], password=request.form['password'], timezone=timezone)
      except ValueError as e:
        flash(e.message)
        return render_template('login.html', next=oid.get_next_url(),
                               error=oid.fetch_error())
      login_user(g.user) #, remember=request.form.get("remember", "no") == "yes")
      flash('Account created')
    else:
      g.user = login_hashed(bcrypt, request.form['email'], request.form['password'])
      if not g.user:
        flash('Incorrect password')
        return redirect(url_for('login'))
      else:
        login_user(g.user) #, remember=request.form.get("remember", "no") == "yes")
    return redirect(url_for('index'))
  return render_template('login.html', next=oid.get_next_url(),
              error=oid.fetch_error())

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
  form = dict(name=g.user.name, email=g.user.email)
  if request.method == 'POST':
    add = request.form['addtweets']
    if (add[0] != '#'):
      add = '#' + add
    twitadd = Twitter(add, user_id=g.user.id)
    db.session.add(twitadd)
    request.form['addtweets'] == ''
    # save everything in the db
    db.session.commit()
  return render_template('profile.html', form=form, next=oid.get_next_url())

@app.route('/news', methods=['GET', 'POST'])
@login_required
def news():
  return jsonify({})
  feed = []
  for tweet in g.user.twitters:
    feed.append(twitter.search(q='#' + tweet.handle))
  fb = [] #get_blob('https://graph.facebook.com/google/feed')
  reddits = {}
  threads = []
  for page in g.user.pages:
    reddits[page.name] = {}
    for sub in ['technology', 'news', 'worldnews' ]:
      thread = Thread(target=get_sub_reddit, args=(reddits[page.name], sub, page.name))
      thread.start()
      threads.append(thread)
  for thread in threads:
    thread.join()
  for page_name, subreddits in reddits.items():
    reddits[page_name] = reduce(add, subreddits.values(), [])
  #news=get_blob('https://api.usatoday.com/open/articles/topnews?search=google&api_key=asgn54b69rg7699v5skf8ur9')
  return jsonify(reddit=reddits, fb=fb, feed=feed)

def get_sub_reddit(results, name, search):
  results[name] = []
  submissions = reddit.get_subreddit(name).search(search, limit = 5)
  for sub in submissions:
    results[name].append( (sub.url, sub.title ))

@app.route('/logout')
def logout():
  g.user = None
  logout_user()
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
