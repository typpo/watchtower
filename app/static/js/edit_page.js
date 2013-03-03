function EditPageCtrl($scope, $http) {
  $scope.iframe_visible = false;
  $scope.url = 'http://google.com';
  $scope.name = 'home page';
  $scope.selectors = {};

  $scope.Init = function() {
    adjust_iframe(document.getElementById('proxy_frame'));
  }

  $scope.SavePage = function() {
    // ok to navigate away now
    // TODO only complain about unload if navigating in iframe
    document.getElementById('proxy_frame').contentWindow.onbeforeunload = function() {};

    var selectors = [];
    var names = [];
    for (var selector in $scope.selectors) {
      selectors.push(selector);
      names.push($scope.selectors[selector]);
    }

    /*
    var $cnp = $('#create_new_page');
    $cnp.find('input[name="url"]').val($scope.url);
    $cnp.find('input[name="name"]').val($scope.name);
    $cnp.find('input[name="selectors"]').val(JSON.stringify(selectors));
    $cnp.find('input[name="names"]').val(JSON.stringify(names));
    $cnp.submit();
    */
    // TODO show loader
    $http({
        url: '/edit_page',
        method: "POST",
        params: {
          url: $scope.url,
          name: $scope.name,
          selectors: JSON.stringify(selectors),
          names: JSON.stringify(names)
        }
     }).success(function(data) {
       window.location.href = '/';
     });
  }

  function adjust_iframe(oFrame) {
    if(!oFrame) return;
    var win_height;
    var frm_height;
    // Get page height Firefox/IE
    if(window.innerHeight) win_height = window.innerHeight;
     else if(document.body.clientHeight) win_height = document.body.clientHeight;
    // Determine new height
    frm_height = win_height - oFrame.offsetTop - 15; // replace 15 accordingly
    // Set iframe height
    oFrame.style.height = frm_height + "px";
  }

  $(document).bind('watchtower-selectors-updated', function() {
    $scope.selectors = document.getElementById('proxy_frame').contentWindow.__watchtower_get_selectors();
  });
}

function selectors_updated() {
  // pass up from iframe - this is a terrible hack
  $(document).trigger('watchtower-selectors-updated');
}
