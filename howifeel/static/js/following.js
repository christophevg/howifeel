function follow(username) {
  post("/api/me/following", username, function() {
    window.location.href = "/following";
  });
}

function unfollow(username) {
  dele("/api/me/following/" + username, function() {
    $("#followed-"+username).remove();
  });
}

function show_followed(followed) {
  var color = {
    "super" : "success",
    "ok"    : "warning",
    "down"  : "danger"
  }[followed.mood];
  var text = {
    "super" : "I'm Super!<br>I'm feeling just fine.",
    "ok"    : "I'm Ok.<br>Everything is calm, normal.",
    "down"  : "I'm Down.<br>I'm not feeling too good."
  }[followed.mood];
  $("#following").append(`
<div  id="followed-${followed.user}" class="card mb-4 rounded-3 shadow-sm border-${color} text-center">
  <div class="card-body d-flex justify-content-between align-items-center bg-${color} border-${color} text-white">
    <span>
      <img src="https://www.gravatar.com/avatar/${followed.gravatar}?d=mp" alt="mdo" width="32" height="32" class="bg-light rounded-circle">
      <br>
      ${followed.user}
    </span>
    <span>${text}
    </span>
    <button type="button" onclick="unfollow('${followed.user}');" class="pull-right text-white btn btn-lg">&times;</button>
  </div>
</div>
`);  
}

// get our following
$.get("/api/me/following", function(following) {
  $.each(following, function(index, followed) {
    show_followed(followed);
  });
});
