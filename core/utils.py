import requests
def get_blob(url):
  return requests.get(url).text
