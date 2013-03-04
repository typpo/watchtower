import requests
import socket
from functools import wraps
from flask import g, request, redirect, url_for, flash

def get_blob(url):
  return requests.get(url).text

def is_production():
  return socket.gethostname().endswith('gowatchtower.com')

def login_required(f):
  @wraps(f)
  def decorated_function(*args, **kwargs):
    if g.user is None:
      return redirect(url_for('login', next=request.url))
    return f(*args, **kwargs)
  return decorated_function

def must_own_page(f):
  @wraps(f)
  @login_required
  def decorated_function(page_id):
    if page_id not in [page.id for page in g.user.pages]:
      flash('You do not have permission to access this page')
      return redirect(request.referrer)
    return f(page_id)
  return decorated_function
