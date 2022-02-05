// mapping of our moods to bootstrap colors
var mood_colors = {
  "super" : "success",
  "ok"    : "warning",
  "down"  : "danger"
};

function activate_mood(mood) {
  var panel = $("#" + mood);
  panel.find(".card-header").addClass("bg-" + mood_colors[mood]);

  var button = panel.find("button");
  button.prop("disabled", true);
  button.removeClass("btn-outline-" + mood_colors[mood]);
  button.addClass("btn-" + mood_colors[mood]);
}

function deactivate_mood(mood) {
  var panel = $("#" + mood);
  panel.find(".card-header").removeClass("bg-" + mood_colors[mood]);

  var button = panel.find("button");
  button.prop("disabled", false);
  button.addClass("btn-outline-" + mood_colors[mood]);
  button.removeClass("btn-" + mood_colors[mood]);
}

function set_mood(mood) {
  post("/api/mood", { "mood" : mood }, function() {
    deactivate_mood("super");
    deactivate_mood("ok");
    deactivate_mood("down");

    activate_mood(mood);
  });
}

// setup click event handlers for buttons
$("#super button").click(function() { set_mood("super") });
$("#ok    button").click(function() { set_mood("ok")    });
$("#down  button").click(function() { set_mood("down")  });

// get current mood to intialize page
$.get("/api/mood", function(mood) {
  activate_mood(mood);
});
