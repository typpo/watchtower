from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
import time

def get_fingerprints(url, selectors):
  browser = webdriver.Firefox() # Firefox for now
  browser.get(url) # Load page

  # TODO selector needs to be js escaped

  # inject jquery
  f = open('jquery.js')
  jquery_js = f.read();
  f.close()
  browser.execute_script(jquery_js)

  # check all selectors
  ret = [get_fingerprint(browser, sel) for sel in selectors]

  browser.close()

  return ret

def get_fingerprint(browser, selector):
  eval_js = """
  var $ = window.jQuery;
  var $el = $('{{ SELECTOR }}');
  return {
    offset: $el.offset(),
    innerHTML: $el.html(),
    outerHTML: $el.parent().html(),
    computedStyle: window.getComputedStyle($el.get(0))
  };
  """.replace('{{ SELECTOR }}', selector)
  return browser.execute_script(eval_js)

if __name__ == '__main__':
  print get_fingerprints('http://www.google.com', ['#lga', '#mngb'])
