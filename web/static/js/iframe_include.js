jQuery.fn.getPath = function () {
  if (this.length != 1) throw 'Requires one element.';
  var path, node = this;
  while (node.length) {
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
  $('body *').unbind('click')
             .unbind('mousedown')
  .live('mouseover', function(e) {
    var $el = $(this);
    var path = $el.getPath();
    var tagname = $el.prop('tagName');
    if ($currently_highlighting_element
        && $currently_highlighting_element.parents().length > $el.parents().length) {
      // not deeper in the DOM
      return false;
    }

    // mouseenter
    //var $wrap = $el.wrap('<div></div>').addClass('watchtower-border-highlight');
    //$el.replaceWith($wrap);
    $('.watchtower-border-highlight').removeClass('watchtower-border-highlight');
    $el.addClass('watchtower-border-highlight');
    // did it work?
    if ($el.css('border-width') === '0px') {
      $el.children().addClass('watchtower-border-highlight');
      $el.children().children().addClass('watchtower-border-highlight');
      // it didn't
    }
    else {
      $currently_highlighting_element = $el;
    }

    // allow bubbling
    //e.stopPropagation();
    //return false;
  }).live('mouseleave', function(e) {
    // mouseleave
    var $el = $(this);
    //$el.parent().remove();
    $('.watchtower-border-highlight').removeClass('watchtower-border-highlight');

    $currently_highlighting_element = null;
    // allow bubbling
  }).live('mousedown', function() {
    console.log($(this).getPath());
    $currently_highlighting_element.addClass('watchtower-border-confirm');
    if (confirm('u want to add this?')) {

    }
    else {
      $currently_highlighting_element.removeClass('watchtower-border-confirm');
    }
    return false;
  });

  // no navigating away
  window.onbeforeunload = function() {
    return "Watchtower doesn't support navigation in Change Tracking mode.  Are you sure you want to navigate away?";
  }
})(jQuery);
