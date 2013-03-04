$.ajax('/news').done(function(data) {
  $feed = $('#feed');
  $.each(data.reddit, function(page, posts) {
    if (!$('.' + page.name).length) {
      $feed.append('<span class="' + page.name + '">');
      $.each(posts, function(i, item) {
        if (i < 5) {
          $feed.append('<a href="' + item[0]  +'">' + item[1] + '</a><br>');
        }
      });
      $feed.append('</span>');
    }
  });
});
