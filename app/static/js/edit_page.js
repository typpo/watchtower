function EditPageCtrl($scope, $http) {
  $scope.pageid = pageid;
  $scope.iframe_visible = false;
  $scope.url = 'http://google.com';
  $scope.name = 'home page';
  $scope.selectors = {};
  $scope.deleted_element_ids = [];

  $scope.Init = function() {
    adjust_iframe(document.getElementById('proxy_frame'));

    $(document).bind('watchtower-iframe-loaded', function() {
      // mark elements
      for (var i=0; i < elements.length; i++) {
        var element = elements[i];
        document.getElementById('proxy_frame')
          .contentWindow.__watchtower_select_element(element.selector, element.name);
      }
    });
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
    $('#loader').show();
    $http({
        url: '/page/' + $scope.pageid + '/edit',
        method: "POST",
        params: {
          url: $scope.url,
          name: $scope.name,
          selectors: JSON.stringify(selectors),
          names: JSON.stringify(names),
          delete: JSON.stringify($scope.deleted_element_ids)
        }
     }).success(function(data) {
       $('#loader').hide();
       window.location.href = '/page/' + $scope.pageid;
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

function iframe_loaded() {
  $(document).trigger('watchtower-iframe-loaded');
}
