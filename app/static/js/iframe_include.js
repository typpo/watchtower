jQuery.fn.getPath = function () {
  if (this.length != 1) throw 'Requires one element.';
  var path, node = this;
  while (node.length) {

    if (node.attr('id')) {
      path = '#' + node.attr('id') + (path ? ' ' + path : '');
      break;
    }

    var realNode = node[0], name = realNode.localName;
    if (!name) break;
    name = name.toLowerCase();

    var parent = node.parent();

    var siblings = parent.children(name);
    if (siblings.length > 1) {
      name += ':eq(' + siblings.index(realNode) + ')';
    }

    path = name + (path ? '>' + path : '');
    node = parent;
  }
  return path;
};

(function($) {
  var $currently_highlighting_element;
  var selected_selectors = {};
  $('body *').unbind('click')
             .unbind('mousedown')
  .live('mouseover', function(e) {
    var $el = $(this);
    if ($el.hasClass('watchtower-border-confirmed')) {
      $currently_highlighting_element = $el;
      return false;
    }
    var path = $el.getPath();
    var tagname = $el.prop('tagName');
    if ($currently_highlighting_element
        && $currently_highlighting_element.parents().length > $el.parents().length) {
      // not deeper in the DOM
      return false;
    }

    // mouseenter
    $('.watchtower-border-highlight').removeClass('watchtower-border-highlight');
    $el.addClass('watchtower-border-highlight');
    $el.css({
      'margin-left': $el.css('margin-left') - 1,
      'margin-top': $el.css('margin-top') - 1,
    });
    // did it work?
    if ($el.css('outline-width') === '0px') {
      // it didn't
      $el.children().addClass('watchtower-border-highlight');
      $el.children().children().addClass('watchtower-border-highlight');
    }
    else {
      $currently_highlighting_element = $el;
    }

    // allow bubbling
    e.stopPropagation();
    return false;

  }).live('mouseleave', function(e) {
    // mouseleave
    var $el = $(this);
    $('.watchtower-border-highlight').removeClass('watchtower-border-highlight');

    $currently_highlighting_element = null;
    // allow bubbling

  }).live('mousedown', function() {
    var path = $currently_highlighting_element.getPath();
    if ($currently_highlighting_element.hasClass('watchtower-border-confirmed')) {
      // TODO remove from list
      $currently_highlighting_element.removeClass('watchtower-border-confirmed');
      selected_selectors[path] = false;
      $(window.parent.document).trigger('watchtower-selectors-updated');
      parent.selectors_updated();
    }
    else {
      // TODO add to list
      $currently_highlighting_element.addClass('watchtower-border-confirmed');
      selected_selectors[path] = prompt('Enter a name for this element', 'element name, eg. Call to Action Box');
      $(window.parent.document).trigger('watchtower-selectors-updated');
      parent.selectors_updated();
    }
    return false;
  });

  window.__watchtower_get_selectors = function() {
    return selected_selectors;
  }

  // no navigating away
  window.onbeforeunload = function() {
    return "Watchtower doesn't support navigation in Change Tracking mode.  Are you sure you want to navigate away?";
  }
})(jQuery);
