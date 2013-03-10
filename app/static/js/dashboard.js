(function() {
  var $screenshot_preview;
  $('i.screenshot-preview').mouseenter(function() {
    if ($screenshot_preview) $screenshot_preview.remove();
    var $el = $(this);
    var $img = $('<img></img>')
      .attr('src',
            'https://s3.amazonaws.com/watchtower-screenshots/'
              + $el.data('screenshot-url'))
      .css({
        width: 300,
        height: 'auto'
      });
    $screenshot_preview = $('<div></div>').append($img)
      .css({
        position: 'absolute',
        top: $el.offset().top,
        left: $el.offset().left + 30
      }).appendTo('body').show();

      console.log($el.offset().top);
      console.log($el.offset().right);

  }).mouseleave(function() {
    if ($screenshot_preview) $screenshot_preview.remove();
  });
  $.ajax('/news').done(function(data) {
    var $feed = $('#news');
    $('#social').show();
    if (Object.keys(data.reddit).length) {
      $feed.append('<h5>Reddit</h5>')
    }
    $.each(data.reddit, function(page, posts) {
      $feed.append(tmpl("news_page_tmpl", {
        parent: '#news',
        page: page,
        page_id: page.replace(' ', '_'),
        inner: $.map(posts, function(post) {
          return tmpl("news_story_tmpl", {
            link: post[0],
            headline: post[1]
          });
        }).join('')
      }));
    });

    $twitter = $('#twitter');
    $twitter.append(
      '<h3> Twitter Feed </h3>' +
        '<dl>' +
        '<form id=twitter_form action="/" method="post">' +
        '<input type="text" name=addtweets placeholder="Topic">' +
        '<input type="submit" class="btn" value="Add Topic">' +
        '</form>' +
        '</dl>');
    $.each(data.feed, function(i) {
      var interest = data.feed[i];
      var page =decodeURIComponent(interest.query);
      $twitter.append(tmpl("news_page_tmpl", {
        parent: '#twitter',
        page: page,
        page_id: page.replace(' ', '_').substring(1),
        inner: $.map(interest.results, function(t) {
          return tmpl("twitter_tmpl", {
            text: t.text
          });
        }).join('')
      }));
    });
  });
})();
