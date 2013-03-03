function EditPageCtrl($scope, $http) {
  $scope.iframe_visible = false;
  $scope.url = 'http://google.com';
  $scope.name = 'home page';
  $scope.selectors = {};

  $scope.LoadIframe = function() {
    // TODO proper way is angular directive
    $('#proxy_frame').attr('src', '/proxy?url=' + $scope.url);
    $scope.iframe_visible = true;
    adjust_iframe(document.getElementById('proxy_frame'));
  }

  $scope.SavePage = function() {
    console.log($scope.selectors);

    var selectors = [];
    var names = [];
    for (var selector in $scope.selectors) {
      selectors.push(selector);
      names.push($scope.selectors[selector]);
    }
    $http({
        url: '/watch',
        method: "GET",
        params: {
          url: $scope.url,
          name: $scope.name,
          selectors: JSON.stringify(selectors),
          names: JSON.stringify(names)
        }
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
  // this is a terrible hack and I should be ashamed
  $(document).trigger('watchtower-selectors-updated');
}
