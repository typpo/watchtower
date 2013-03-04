import requests
import socket
from functools import wraps
from flask import g, request, redirect, url_for, flash
from core.models import Element, Version, Page, User
from core.database import db

def get_blob(url):
  return requests.get(url).text

def is_production():
  return socket.gethostname().endswith('gowatchtower.com')

def login_required(f):
  @wraps(f)
  def decorated_function(*args, **kwargs):
    if g.user is None:
      flash('You must log in to see this page')
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
      flash('You do not have permission to access this page')
      print request.referrer
      return redirect(request.referrer or '/')
    elif not page.user_id:
      page.user_id = g.user.id
      db.session.add(page)
    elif page.user_id != g.user.id:
      flash('You do not have permission to access this page')
      print request.referrer
      return redirect(request.referrer or '/')
    return f(page)
  return decorated_function
