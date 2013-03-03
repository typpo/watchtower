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
    console.log(oFrame);
}

adjust_iframe(document.getElementById('proxy_frame'));
