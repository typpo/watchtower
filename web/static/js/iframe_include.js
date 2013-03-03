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
  var prev_border_css;
  console.log('hell');
  //$('body *').unbind('*');
  $('div').mouseover(function() {
    // mouseenter
    console.log('mouseenter');
    prev_border_css = $(this).css('border');
    $(this).css('border', '10px solid #000');
  }).mouseout(function() {
    // mouseleave
    console.log('mouseleave');
    $(this).css('border', prev_border_css);
  });
})();
