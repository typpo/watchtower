import requests
import socket

def get_blob(url):
  return requests.get(url).text

def is_production():
  return socket.gethostname().endswith('gowatchtower.com')

