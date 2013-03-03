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

(function() {
  $('body *').unbind('*');
  var currently_highlighting = false;
  $('body *').live('mouseover', function(e) {
    if (currently_highlighting) return;
    // mouseenter
    console.log('mouseenter');
    var $el = $(this);
    $el.addClass('watchtower-border-highlight');
    currently_highlighting = true;

    // allow bubbling.  some elements don't support border styles
  }).live('mouseleave', function(e) {
    // mouseleave
    console.log('mouseleave');
    var $el = $(this);
    $('.watchtower-border-highlight').removeClass('watchtower-border-highlight');

    currently_highlighting = false;
    // allow bubbling
  }).live('click', function() {
    console.log($(this).getPath());
    return false;
  });

  // no navigating away
  window.onbeforeunload = function() {
    return "Watchtower doesn't support navigation in Change Tracking mode.  Are you sure you want to navigate away?";
  }
})();
