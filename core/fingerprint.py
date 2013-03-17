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
from threading import Thread

NUM_AB_CHECKS = 5    # number of times we check the page for a different layout

def start_display():
  print 'starting virtual display'
  display = Display(visible=0, size=(1024, 768))
  display.start()
  return display

def stop_display(display):
  display.stop()

def start_browser():
  print 'starting browser'
  browser = webdriver.Chrome() # fuck firefox
  return browser

def stop_browser(browser):
  browser.close()
  browser.quit()

# returns a list of fingerprints for each selector
def get_fingerprints(url, selectors, display=None, \
    browser=None, cleanup_at_end=True, record_screenshot=False):
  if not display:
    display = start_display()
  if not browser:
    browser = start_browser()

  print 'getting fingerprints'
  print 'load browser @ %s' % url
  browser.get(url) # Load page

  # inject jquery
  print 'inject jquery'
  f = open(os.path.join(os.path.dirname(__file__), 'jquery.js'))
  jquery_js = f.read();
  f.close()
  browser.execute_script(jquery_js)

  # check all selectors
  print 'check selectors'
  ret = [get_fingerprint(browser, sel) for sel in selectors]

  # screenshot

  # mask all non-elements, so chosen elements are highlighted
  print 'masking page for screenshot'
  mask_js = """
  jQuery.noConflict();
  (function($) {
    $('<div></div>').css({
      background: 'rgba(0,0,0,0.3)',
      width: '100%',
      position: 'fixed',
      top: 0,
      left: 0,
      'z-index': 99998,
    }).height($(document).height()).appendTo('body');  // necessary to get FULL height of page in selenium screenshot
    $('.watchtower-expose-for-screenshot').css({
      'z-index': 99999,
      'outline': '2px solid red',
    }).each(function() {
      var $el = $(this);
      if ($el.css('position') === 'static') {
        $el.css('position', 'relative');
      }
    });
  })(jQuery);
  """
  browser.execute_script(mask_js)

  # create tmp path
  if not os.path.isdir('/tmp/watchtower'):
    os.mkdir('/tmp/watchtower')
  screenshot_local_path = '/tmp/watchtower/%d%d.png' % (time.time(), random.randint(0, 1000))
  print 'screenshot to', screenshot_local_path
  screenshot_url = ''
  if browser.save_screenshot(screenshot_local_path) and __name__ != '__main__':
    screenshot_remote_path = 'images/'  \
      + hashlib.sha1(screenshot_local_path).hexdigest() + '.png'
    if record_screenshot:
      thread = Thread(target=screenshots.upload_screenshot, \
          args=(screenshot_local_path,screenshot_remote_path,True))
      thread.start()
    screenshot_url = screenshot_remote_path

  browser.delete_all_cookies()   # this only deletes cookies for the page that it's on, so it has to go here after the page is loaded

  #if cleanup_at_end:
  stop_browser(browser)
  stop_display(display)

  print 'ret'
  return ret, screenshot_url, screenshot_local_path

# returns the fingerprint of the first element corresponding to a
# given selector
def get_fingerprint(browser, selector):
  eval_js = """
  return (function($) {
    window.onerror = function() {
      console.log(arguments);
    }
    function eldetails($el) {
      var strs = [$.trim($el.clone().children().remove().end().text())];
      var srcs = $el.prop('tagName') === 'IMG' ? [$el.attr('src')] : [];
      $el.find('*').not('style,noscript,script').each(function () {
        var $child = $(this);
        if ($child.is(':visible')
          && $child.css('visibility') !== 'hidden'
          && $child.css('opacity') !== 0) {
          // note that visibility, opacity hidden still consume space in the layout
          var txt = $child.clone().children().remove().end().text();
          if ($.trim(txt) !== '') {
            strs.push(txt);
          }
          if ($child.prop('tagName') === 'IMG') {
            srcs.push($child.attr('src'));
          }
        }
      })
      return {
        'strs': strs,
        'srcs': srcs
      };
    }
    var $el = $('{{ SELECTOR }}');
    if ($el.length < 1 || !$el.is(':visible')) {
      return {
        offset: {},
        //innerHTML: '',
        outerHTML: '',
        computedStyle: {},
        text: '',
        srcs: '',
      }
    }
    $el.addClass('watchtower-expose-for-screenshot');    // add class to highlight this in screenshot
    var computed_style = window.getComputedStyle($el.get(0));
    var style = {};
    for (var s in computed_style) {
      if (!computed_style.hasOwnProperty(s)) {   // !hasOwnProperty is required because it's half array, half object
        style[s] = computed_style[s];
      }
    }
    var details = eldetails($el);
    return {
      offset: $el.offset(),   // TODO some edge cases in which offset is not accurate
      //innerHTML: $el.html(),
      outerHTML: $('<div>').append($el.clone()).html(),
      computedStyle: style,

      // TODO convert text and srcs to arrays, after diffing works well enough
      text: details.strs.join('|'),
      srcs: details.srcs.join('|'),
    };
  })(jQuery);
  """.replace('{{ SELECTOR }}', selector)
  ret = browser.execute_script(eval_js)

  print ret['text']

  return ret

# returns a list of difference dicts
# a difference dict has:
#    - key: name of difference (eg. backgroundColor, text content, etc.)
#    - diff_amount:  amount of difference, if applicable
#    - diff_unit:  unit of diff_amount, if applicable
def diff_fingerprints(f1, f2):
  diffs = []
  diffs.extend(diff_offsets(f1['offset'], f2['offset']))
  #diffs.extend(diff_html(f1['outerHTML'], f2['outerHTML']))  # disabled because text+srcs is better
  diffs.extend(diff_styles(f1['computedStyle'], f2['computedStyle']))
  if 'text' in f1 and 'text' in f2:   # backwards compatibility 3/7/13
    diffs.extend(diff_text(f1['text'], f2['text']))
  if 'srcs' in f1 and 'srcs' in f2:   # backwards compatibility 3/7/13
    diffs.extend(diff_srcs(f1['srcs'], f2['srcs']))
  if len(diffs) > 0:
    print 'change detected'
  return diffs

def diff_text(t1, t2):
  if t1.strip() != t2.strip():
    ratio = difflib.SequenceMatcher(None, t1, t2).ratio()
    #if ratio < .6:  # 40% different
    return [{ \
      'key': 'text content',
      'diff': '%s vs. %s' % (t1, t2), #''.join(difflib.context_diff(t1, t2)),
      'diff_amount': (1 - ratio) * 100,
      'diff_unit': '%',
    }]
  return []

def diff_srcs(s1, s2):
  if s1.strip() != s2.strip():
    ratio = difflib.SequenceMatcher(None, s1, s2).ratio()
    return [{ \
      'key': 'image content source',
      'diff': '%s vs. %s' % (s1, s2),
      'diff_amount': (1 - ratio) * 100,
      'diff_unit': '%',
    }]
  return []


# diffs the result of jQuery .offset() on an element
def diff_offsets(o1, o2):
  diffs = []
  # Assumes keys are the same
  for key in o1:
    if key not in o2:
      continue
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
  diffs = []
  if h1 != h2:
    ratio = difflib.SequenceMatcher(None, h1, h2).ratio()
    if ratio > .6:
      #diffs.append(''.join(difflib.Differ().compare(h1, h2)))
      diffs.append({ \
        'key': 'html content',
        'diff': ''.join(difflib.context_diff(h1, h2)),
        'diff_amount': (1 - ratio) * 100,
        'diff_unit': '%',
      })
    else:
      print 'change detected, but it is below uniqueness ratio threshold'
  return diffs

# diffs the massaged results of getComputedStyle on elements
def diff_styles(s1, s2):
  # Assumes keys are the same
  diffs = []
  for style in s1:
    if style not in s2:
      continue # TODO may need to do this differently
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
  #fp1 = get_fingerprints('http://localhost:5000/test', ['#lucky'])
  #fp2 = get_fingerprints('http://localhost:5000/test', ['#lucky'])
  fp1, screenshot_url, screenshot_path  = get_fingerprints('http://www.cnn.com', ['#cnn_maintt1imgbul div:eq(0)>div:eq(0)>div>a>img'])
  fp2, screenshot_url, screenshot_path  = get_fingerprints('http://www.cnn.com', ['#cnn_maintt1imgbul div:eq(0)>div:eq(0)>div>a>img'])
  print diff_fingerprints(fp1[0], fp2[0])

def test_ab_detection():
  print detect_ab_test('http://localhost:5000/test', ['#lucky'])

def test_ab_bookingcom():
  print detect_ab_test('http://www.booking.com/city/us/new-york.en-us.html?sid=9d1b2e3670bdb8656e697473c451d44e;dcid=1', ['.promos tr:first'])

if __name__ == '__main__':
  test_fingerprint()
  #test_diff()
  #test_ab_detection()
  #test_ab_bookingcom()
