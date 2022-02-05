function invite() {
  var invitation = {
    "invited": $("#who").val()
  };
  post("/api/invitations", invitation, function(confirmation) {
    show_invitation(confirmation);
    $("#who").val("");
  });
}

function revoke(invitation) {
  dele("/api/invitation/" + invitation, function() {
    $("#invitation-"+invitation).remove();
  });
}

function show_invitation(invitation) {
  $("#invitations").append(`
  <tr id="invitation-${invitation.invitation}">
    <td>${invitation.invited}</td>
    <td><a href="/signup/${invitation.invitation}" target="_blank">${invitation.invitation}</a></td>
    <td><button type="button" onclick="revoke('${invitation.invitation}');" class="btn btn-danger btn-sm">x</button></td>
  </tr>
`);  
}

// get our invitations
$.get("/api/invitations", function(invitations) {
  $.each(invitations, function(index, invitation) {
    show_invitation(invitation);
  });
});
