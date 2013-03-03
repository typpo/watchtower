def getBlob(url):
  return requests.get(url).text
