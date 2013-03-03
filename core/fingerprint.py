from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
import time
import json
import difflib
import os

def get_fingerprints(url, selectors):
  browser = webdriver.Firefox() # Firefox for now
  browser.get(url) # Load page

  # TODO selector needs to be js escaped

  # inject jquery
  f = open(os.path.join(os.path.dirname(__file__), 'jquery.js'))
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
    if (!computed_style.hasOwnProperty(s)) {   // !hasOwnProperty is required because it's half array, half object
      style[s] = computed_style[s];
    }
  }
  return {
    offset: $el.offset(),   // TODO some edge cases in which offset is not accurate
    innerHTML: $el.html(),
    outerHTML: $el.parent().html(),
    computedStyle: style
  };
  """.replace('{{ SELECTOR }}', selector)
  ret = browser.execute_script(eval_js)

  return ret

def diff_fingerprints(f1, f2):
  diffs = []
  diffs.extend(diff_offsets(f1['offset'], f2['offset']))
  diffs.extend(diff_html(f1['outerHTML'], f2['outerHTML']))
  diffs.extend(diff_styles(f1['computedStyle'], f2['computedStyle']))
  return diffs

def diff_offsets(o1, o2):
  diffs = []
  # Assumes keys are the same
  for key in o1:
    if o1[key] != o2[key]:
      diffamnt = o2[key] - o1[key]
      if diffamnt > 10:
        # this check is necessary because webkit will find extremely
        # tiny differences from time to time
        diffs.append({ \
          'key': key,
          'diff_amount': diffamnt,
          'diff_unit': 'px',
        })
  return diffs

def diff_html(h1, h2):
  print h1, h2
  diffs = []
  if h1 != h2:
    diffs.append('\n'.join(difflib.unified_diff(h1, h2)))
  return diffs

def diff_styles(s1, s2):
  # Assumes keys are the same
  diffs = []
  for style in s1:
    if s1[style] != s2[style]:
      diffs.append({ \
        'key': style,
        'diff_amount': 'n/a',   # TODO detect units and provide amount if possible
        'diff_unit': 'n/a',
      })
  return diffs

if __name__ == '__main__':
  #print get_fingerprints('http://www.google.com', ['#lga', '#mngb'])
  fp1 = get_fingerprints('http://localhost:5000/test', ['#lucky'])
  fp2 = get_fingerprints('http://localhost:5000/test', ['#lucky'])
  print diff_fingerprints(fp1[0], fp2[0])
