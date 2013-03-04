(function() {
    $.ajax('/news').done(function(data) {
      var $feed = $('#feed');
      $feed.append('<p><h5>Social News on Sites You\'re Tracking</h5></p>');
      $.each(data.reddit, function(page, posts) {
        $.each(posts, function(i, item) {
          if (i < 5) {
            $feed.append('<a href="' + item[0]  +'">' + item[1] + '</a><br>');
          }
        });
      });
    });
})();
