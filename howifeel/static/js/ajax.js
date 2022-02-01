// helper functions to post data to the API

function post(resource, data, callback) {
  $.ajax( {
    url: resource,
    type: "POST",
    data: JSON.stringify(data),
    dataType: "json",
    contentType: "application/json",
    success: function(response) {
      if(callback) { callback(response); }
    },
    error: function(response) {
      var msg = JSON.parse(response.responseText).message;
      $.notify("Whoops, someting went wrong:\n" + msg, {
        position: "top center",
        className: "error"
      });
    }
  });
}

function dele(resource, callback) {
  $.ajax( {
    url: resource,
    type: "DELETE",
    success: function(response) {
      if(callback) { callback(response); }
    },
    error: function(response) {
      var msg = JSON.parse(response.responseText).message;
      $.notify("Whoops, someting went wrong:\n" + msg, {
        position: "top center",
        className: "error"
      });
    }
  });
}
