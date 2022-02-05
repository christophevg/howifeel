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
  $("#following").append(`
  <tr id="followed-${followed.user}">
    <td>${followed.user}</td>
    <td><span class="badge bg-${color}">${followed.mood}</span></td>
    <td width="1%"><button type="button" onclick="unfollow('${followed.user}');" class="btn btn-danger btn-sm">x</button></td>
  </tr>
`);  
}

// get our following
$.get("/api/me/following", function(following) {
  $.each(following, function(index, followed) {
    show_followed(followed);
  });
});
