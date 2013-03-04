(function() {
  if (typeof dashboard_loaded == 'undefined') {
    dashboard_loaded = true;

    $.ajax('/news').done(function(data) {
      $feed = $('#feed');
      $.each(data.reddit, function(page, posts) {
        $.each(posts, function(i, item) {
          if (i < 5) {
            $feed.append('<a href="' + item[0]  +'">' + item[1] + '</a><br>');
          }
        });
      });
    });
  }
})();
