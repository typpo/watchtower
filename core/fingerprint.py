from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
import time

def get_fingerprint(url, selector):
  browser = webdriver.Firefox() # Firefox for now
  browser.get(url) # Load page

# TODO selector needs to be escaped

  # inject jquery
  f = open('jquery.js')
  jquery_js = f.read();
  f.close()
  browser.execute_script(jquery_js)

  # eval some js
  eval_js = """
  var $ = window.jQuery;
  var $el = $('{{ SELECTOR }}');
  return {
    width: $el.width(),
    height: $el.height(),
    offset: $el.offset(),
    innerHTML: $el.html(),
    outerHTML: $el.parent().html(),
    computedStyle: window.getComputedStyle($el.get(0))
  };
  """.replace('{{ SELECTOR }}', selector)
  ret = browser.execute_script(eval_js)

  browser.close()

  return ret

if __name__ == '__main__':
  print get_fingerprint('http://www.google.com', '#lga')
