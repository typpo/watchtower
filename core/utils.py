import re
import requests
import mechanize
from BeautifulSoup import BeautifulSoup, UnicodeDammit
from requests.exceptions import ConnectionError
from functools import wraps
from flask import g, request, redirect, url_for, flash
from core.models import Element, Version, Page, User
from core.database import db

def get_blob(url):
  """
  try:
    headers = {}
    headers['User-Agent'] = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.60 Safari/537.17"
    return requests.get(url, headers=headers).text
  except ConnectionError:
    return None
  """

  # mechanize instead of basic request because somne sites have more complex
  # cookie validation (such as amazon).  mechanize handles this.
  br = mechanize.Browser()
  br.set_handle_robots(False)
  br.addheaders = [('User-Agent', "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.60 Safari/537.17"),]
  html = br.open(url).read()
  # to use bs4 normally, workaround needed for https://bugs.launchpad.net/beautifulsoup/+bug/1105207
  # http://www.crummy.com/software/BeautifulSoup/bs3/documentation.html#Beautiful%20Soup%20Gives%20You%20Unicode,%20Dammit
  dammit = UnicodeDammit(html)  # guess encoding, handle mixed encoding, etc
  return dammit.unicode

def login_required(f):
  @wraps(f)
  def decorated_function(*args, **kwargs):
    if g.user is None:
      flash('You must log in to see that page')
      return redirect(request.referrer or '/')
    return f(*args, **kwargs)
  return decorated_function

def must_own_page(f):
  """
  check that a user is logged in
  check that the user owns this page
  if the page exists and is not owned by any one, make it owned by current user
  otherwise, flash a permission error
  passes page to function (instead of page_id)
  """
  @wraps(f)
  @login_required
  def decorated_function(page_id):
    page = Page.query.filter_by(id=page_id).first()
    if not page:
      flash('You do not have permission to access that page')
      print request.referrer
      return redirect(request.referrer or '/')
    elif not page.user_id:
      page.user_id = g.user.id
      db.session.add(page)
    elif page.user_id != g.user.id:
      flash('You do not have permission to access that page')
      print request.referrer
      return redirect(request.referrer or '/')
    return f(page)
  return decorated_function

def login_hashed(bcrypt, email, password):
  user = User.query.filter_by(email=email).first()
  if user and not user.openid: # don't allow username/pw login for users signed up with open id
    if (bcrypt.check_password_hash(user.password, password)):
      return user
  return None

def create_user(bcrypt, email, password, timezone, openid=None):
  if not '@' in email[1:-1]: # TODO: do this right
    raise ValueError('Invalid email address')
  pw = bcrypt.generate_password_hash(password,10) if password else None
  user = User(name='', email=email, password=pw, timezone=timezone, openid=openid)
  db.session.add(user)
  db.session.commit()
  return user
