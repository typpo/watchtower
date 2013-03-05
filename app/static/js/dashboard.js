(function() {
  $.ajax('/news').done(function(data) {
    var $feed = $('#news');
    $('#social').show();
    if (Object.keys(data.reddit).length) {
      $feed.append('<h5>Reddit</h5>')
    }
    $.each(data.reddit, function(page, posts) {
      $feed.append(tmpl("news_page_tmpl", {
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
      '<h6> Twitter Feed </h6>' +
        '<dl>' +
        '<form id=twitter_form action="{{ url_for("index") }}" method="post">' +
        '<input type="text" name=addtweets placeholder="Topic">' +
        '<input type="submit" class="btn" value="Add Topic">' +
        '</form>' +
        '</dl>');
    console.log(data);
    $.each(data.feed, function(i) {
      var interest = data.feed[i];
      $twitter.append('<ul><p>' + decodeURIComponent(interest.query) + '</p>');
      $.each(interest.results, function(t) {
        var tweet = interest.results[t];
        if (t < 5)
          $twitter.append('<li>' + tweet.text + '</li>');
      });
      $feed.append('</ul>');
    });
  });
})();
