(function() {
    $.ajax('/news').done(function(data) {
      $('#feed_container').prepend('<p><h5>Social News on Sites You\'re Tracking</h5></p>');
      var $feed = $('#feed');
      if (data.reddit && data.reddit.length)
        $feed.append('<h6> Reddit Feed </h6>')
      $.each(data.reddit, function(page, posts) {
        $feed.append('<ul><p>' + page + '</p>');
        $.each(posts, function(i, item) {
          if (i < 5) {
            $feed.append('<li><a href="' + item[0]  +'">' + item[1] + '</a></li>');
          }
        });
        $feed.append('</ul>');
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
