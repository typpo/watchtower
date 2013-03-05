(function() {
  $.ajax('/news').done(function(data) {
    var $feed = $('#news');
    if (Object.keys(data.reddit).length) {
      $feed.append('<h3>Reddit</h3>')
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
        '<form id=twitter_form action="{{ url_for("index") }}" method="post">' +
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
