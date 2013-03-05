(function() {
    $.ajax('/news').done(function(data) {
      $('#feed_container').prepend('<p><h5>Social News on Sites You\'re Tracking</h5></p>');
      var $feed = $('#feed');
      $.each(data.reddit, function(page, posts) {
        $feed.append('<ul><p>' + page + '</p>');
        $.each(posts, function(i, item) {
          if (i < 5) {
            $feed.append('<li><a href="' + item[0]  +'">' + item[1] + '</a></li>');
          }
        });
        $feed.append('</ul>');
      });
    });
})();
