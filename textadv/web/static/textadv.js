// handles communicating with the textadv server

$(document).ready(function() {
    update_contents();
    $("input#command").focus();
    window.setTimeout(send_ping, 10000);
    $("input#command").keydown(command_key_handler);
  });

send_command = function () {
  command = $("input#command").val();
  run_action(command)
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

print_result = function(r) {
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
  $("input#command").focus();
  container = $("html, body");
  scrollTo = $("input#command");
  container.scrollTop(scrollTo.offset().top - container.offset().top);
};

update_contents = function() {
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
        print_result("<p><i>Connection lost</i></p>");
      }
    }
  });
};

send_ping = function() {
  $.ajax({
    url: "/ping",
    type: "POST",
    dataType: "json",
    data: {session: $("input#session").val()},
  });
  window.setTimeout(send_ping, 10000);
};

run_action = function(command) {
  input_prompt = $("#input_text").text();
  $("#content").append('<p class="user_response">'+input_prompt+" "+command+"</p>"); // should escape!
  
  $.ajax({
    type: "POST",
    url: "/input",
    data: {command: command, session: $("input#session").val()},
    dataType: "json"
  });

  history_add(command);
  $("input#command").val("");
  $("input#command").focus();
  container = $("html, body");
  scrollTo = $("input#command");
  container.scrollTop(scrollTo.offset().top - container.offset().top);
  return false;
};

command_key_handler = function(event) {
  if(event.keyCode == 38) {
    history_up();
    event.preventDefault();
  }
  if(event.keyCode == 40) {
    history_down();
    event.preventDefault();
  }
};

command_history = new Array();
command_index = 0;
current_command = "";

history_add = function(command) {
  command_index = command_history.push(command);
  current_command = ""
};

history_up = function() {
  if(command_index > 0) {
    if(command_index == command_history.length) {
      current_command = $("input#command").val();
    }
    command_index -= 1;
    $("input#command").val(command_history[command_index]);
  }
};

history_down = function() {
  if(command_index < command_history.length) {
    command_index += 1;
    if(command_index == command_history.length) {
      $("input#command").val(current_command);
    } else {
      $("input#command").val(command_history[command_index]);
    }
  }
}
