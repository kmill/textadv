// handles communicating with the textadv server

$(document).ready(function() {
  update_contents();
  $("#command").focus();
  $("#command").keydown(command_key_handler);
  window.setTimeout(send_ping, 10000);
});

function send_command() {
  var command = $("input#command").val();
  run_action(command);
};

var visible_container_listeners = Array();

function register_visible_container_listener(f) {
  visible_container_listeners.push(f);
}

function call_visible_container_listeners(vis_cont) {
  for (var i = 0; i < visible_container_listeners.length; i++) {
    visible_container_listeners[i](vis_cont);
  }
}

function print_result(r) {
  if(r["text"]) {
    $("#content").append(r["text"]);
  }
  if(r["prompt"]) {
    $("#input_text").text(r["prompt"]);
  }
  if(r["headline"]) {
    $("#headline").html(r["headline"]);
  }
  if(r["visible_container"]) {
    call_visible_container_listeners(r["visible_container"]);
  }
  $("#command").focus();
  $("#command")[0].scrollIntoView(true);
};

function update_contents() {
  $.ajax({
    url: "/output",
    type: "GET",
    dataType: "json",
    data: {session: $("input#session").val()},
    success: function(data) {
      print_result(data);
      update_contents();
    },
    error: function(jqXHR, textStatus, errorThrown) {
      if(errorThrown == "timeout") {
        update_contents();
      } else {
        print_result({text : "<p><i>Connection lost</i></p>"});
      }
    }
  });
};

function send_ping() {
  $.ajax({
    url: "/ping",
    type: "POST",
    data: {session: $("input#session").val()}
  }).error(function () {
    print_result({text : "<p><i>Connection lost</i></p>"});
  });
  window.setTimeout(send_ping, 10000);
};

function run_action(command) {
  var input_prompt = $("#input_text").text();
  var $response = $('<p class="user_response">').text(input_prompt + " " + command);
  $("#content").append($response);
  
  $.ajax({
    type: "POST",
    url: "/input",
    data: {command: command, session: $("input#session").val()}
  }).error(function () {
    console.log(arguments);
    print_result({text : "<p><i>Connection lost</i></p>"});
  });

  history_add(command);
  $("#command").val("").focus();
  $("#command")[0].scrollIntoView(true);
  return false;
};

function command_key_handler(event) {
  if(event.keyCode == 38) {
    history_up();
    event.preventDefault();
  }
  if(event.keyCode == 40) {
    history_down();
    event.preventDefault();
  }
};

var command_history = [];
var command_index = 0;
var current_command = "";

function history_add(command) {
  command_index = command_history.push(command);
  current_command = "";
};

function history_up() {
  if(command_index > 0) {
    if(command_index == command_history.length) {
      current_command = $("#command").val();
    }
    command_index -= 1;
    $("#command").val(command_history[command_index]);
  }
};

function history_down() {
  if(command_index < command_history.length) {
    command_index += 1;
    if(command_index == command_history.length) {
      $("#command").val(current_command);
    } else {
      $("#command").val(command_history[command_index]);
    }
  }
}
