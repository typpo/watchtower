from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
import time
import json

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
  var computed_style = window.getComputedStyle($el.get(0));
  var style = {};
  for (var s in computed_style) {
    if (!computed_style.hasOwnProperty(s)) {   // !hasOwnProperty is required
      style[s] = computed_style[s];
    }
  }
  return {
    offset: $el.offset(),
    innerHTML: $el.html(),
    outerHTML: $el.parent().html(),
    computedStyle: style
  };
  """.replace('{{ SELECTOR }}', selector)
  ret = browser.execute_script(eval_js)

  return ret

if __name__ == '__main__':
  print get_fingerprints('http://www.google.com', ['#lga', '#mngb'])
