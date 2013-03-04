from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from pyvirtualdisplay import Display
import time
import random
import json
import difflib
import os
import screenshots
import hashlib

NUM_AB_CHECKS = 5    # number of times we check the page for a different layout

# returns a list of fingerprints for each selector
def get_fingerprints(url, selectors):
  display = Display(visible=0, size=(1024, 768))
  display.start()
  browser = webdriver.Firefox() # fuck firefox
  browser.get(url) # Load page

  # inject jquery
  f = open(os.path.join(os.path.dirname(__file__), 'jquery.js'))
  jquery_js = f.read();
  f.close()
  browser.execute_script(jquery_js)

  # check all selectors
  ret = [get_fingerprint(browser, sel) for sel in selectors]

  # screenshot
  screenshot_local_path = '/tmp/%d%d' % (time.time(), random.randint(0, 1000))
  screenshot_url = ''
  if browser.save_screenshot(screenshot_local_path):
    print 'SCREENSHOT'
    screenshot_remote_path = 'images/'  \
      + hashlib.sha1(screenshot_local_path).hexdigest() + '.png'
    screenshots.upload_screenshot(screenshot_local_path, screenshot_remote_path)
    screenshot_url = screenshot_remote_path
    print 'Screenshot done'

  # all done
  browser.close()
  display.stop()

  return ret, screenshot_url

# returns the fingerprint of the first element corresponding to a
# given selector
def get_fingerprint(browser, selector):
  eval_js = """
  var $ = window.jQuery;
  var $el = $('{{ SELECTOR }}');
  if ($el.length < 1) {
    return {
      offset: {},
      innerHTML: '',
      outerHTML: '',
      computedStyle: {}
    }
  }
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

# returns a list of difference dicts
# a difference dict has:
#    - key: name of difference (eg. backgroundColor)
#    - diff_amount:  amount of difference, if applicable
#    - diff_unit:  unit of diff_amount, if applicable
def diff_fingerprints(f1, f2):
  diffs = []
  diffs.extend(diff_offsets(f1['offset'], f2['offset']))
  diffs.extend(diff_html(f1['outerHTML'], f2['outerHTML']))
  diffs.extend(diff_styles(f1['computedStyle'], f2['computedStyle']))
  return diffs

# diffs the result of jQuery .offset() on an element
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

# diffs html.  straight up string diff.  usually we are interested
# in outerhtml
def diff_html(h1, h2):
  print h1, h2
  diffs = []
  if h1 != h2:
    diffs.append(''.join(difflib.Differ().compare(h1, h2)))
  return diffs

# diffs the massaged results of getComputedStyle on elements
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

# attempts to detect a/b tests.  For now, just refresh the page
# a bunch of times with a new session each time
def detect_ab_test(url, selectors):
  prints = []
  for i in range(NUM_AB_CHECKS):
    prints.append(get_fingerprints(url, selectors))

  for i in range(len(selectors)):
    prev_print = None
    for selector_prints in prints:
      selector_fingerprint = selector_prints[i]
      if prev_print:
        diffs = diff_fingerprints(prev_print, selector_fingerprint)
        if len(diffs) > 0:
          print 'Detected a/b test'
          return diffs

      prev_print = selector_fingerprint

  print 'no a/b detected'
  return []

def test_fingerprint():
  print get_fingerprints('http://www.google.com', ['#lga', '#mngb'])

def test_diff():
  fp1 = get_fingerprints('http://localhost:5000/test', ['#lucky'])
  fp2 = get_fingerprints('http://localhost:5000/test', ['#lucky'])
  print diff_fingerprints(fp1[0], fp2[0])

def test_ab_detection():
  print detect_ab_test('http://localhost:5000/test', ['#lucky'])

def test_ab_bookingcom():
  print detect_ab_test('http://www.booking.com/city/us/new-york.en-us.html?sid=9d1b2e3670bdb8656e697473c451d44e;dcid=1', ['.promos tr:first'])

if __name__ == '__main__':
  test_fingerprint()
  #test_ab_detection()
  #test_ab_bookingcom()
