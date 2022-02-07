// mapping of our moods to bootstrap colors and emoji's
var moods = {
  "super" : {
    "color"  : "success",
    "header" : "&#128525;",
    "body"   : "I'm Super!<br>I'm feeling just fine.",
    "action" : "Super!"
  },
  "ok"    : {
    "color"  : "warning",
    "header" : "&#128512;",
    "body"   : "I'm Ok.<br>Everything is calm, normal.",
    "action" : "Ok"
  },
  "nok"   : {
    "color"  : "warning",
    "header" : "&#128528;",
    "body"   : "I'm Ok on the surface.<br>I hope things clear up a bit.",
    "action" : "Ok"
  },
  "down"  : {
    "color"  : "danger",
    "header" : "&#128530;",
    "body"   : "I'm Down.<br>I'm not feeling too good.",
    "action" : "Down"
  }
};

function show_mood_selectors() {
  // get current mood to intialize page
  $.get("/api/mood", function(mood) {
    var count = moods.length;
    $("#moods").removeClass("row-cols-md-2 mb-2 row-cols-md-3 mb-3 row-cols-md-4 mb-4");
    $("#moods").addClass(`row-cols-md-${count} mb-${count}`)
    $.each(moods, function(id, mood) {
      $("#moods").append(`
        <div id="${id}" class="col">
          <div class="card mb-4 rounded-3 shadow-sm border-${mood.color}">
            <div class="card-header py-3 border-${mood.color}">
              <h4 class="my-0 fw-normal">${mood.header}</h4>
              <button type="button" class="w-100 btn btn-lg btn-outline-${mood.color}">${mood.action}</button>
            </div>
          </div>
        </div>
      `);
      $(`#${id} button`).click(function() { set_mood(id) });
    });
    activate_mood(mood);
  });
}

function show_mood(id) {
  var mood = moods[id];
  $("#mood").html(`
    <div class="card mb-4 rounded-3 shadow-sm border-${mood.color} text-center">
      <div class="card-header py-3 text-white bg-${mood.color} border-${mood.color}">
        <h4 class="my-0 fw-normal">${mood.header}</h4>
      </div>
      <div class="card-body">
        ${mood.body}
      </div>
    </div>
  `);
}

function activate_mood(mood) {
  var panel = $("#" + mood),
      color = moods[mood].color;
  panel.find(".card-header").addClass("bg-" + color);

  var button = panel.find("button");
  button.prop("disabled", true);
  button.removeClass("btn-outline-" + color);
  button.addClass("btn-" + color);
}

function deactivate_mood(mood) {
  var panel = $("#" + mood),
      color = moods[mood].color;
  panel.find(".card-header").removeClass("bg-" + color);

  var button = panel.find("button");
  button.prop("disabled", false);
  button.addClass("btn-outline-" + color);
  button.removeClass("btn-" + color);
}

function set_mood(mood) {
  post("/api/mood", { "mood" : mood }, function() {
    $.each(moods, function(id, mood) {
      deactivate_mood(id);
    });
    activate_mood(mood);
  });
}
