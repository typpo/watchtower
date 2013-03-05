var mod = angular.module('WatchtowerApp',[]);

$(function() {
  $('#login_form input[type="text"], #login_form input[type="password"]').on('click', function(e) {
    e.stopPropagation();
    return false;
  });
});
