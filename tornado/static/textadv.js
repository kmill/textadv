// handles communicating with the textadv server

$(document).ready(function() {
    update_contents();
    $("input#command").focus();
  });

send_command = function () {
  command = $("input#command").val();
  input_prompt = $("#input_text").text();
  $("#content").append("<p><b>"+input_prompt+" "+command+"</b></p>"); // should escape!
  
  $.ajax({
    type: "POST",
    url: "input",
    data: {command: command},
    dataType: "json"
  });

  $("input#command").val("");
  $("input#command").focus();
  container = $("html, body");
  scrollTo = $("input#command");
  container.scrollTop(scrollTo.offset().top - container.offset().top);
}

print_result = function(r) {
  if(r["text"]) {
    $("#content").append(r["text"]);
  }
  if(r["prompt"]) {
    $("#input_text").text(r["prompt"]);
  }
  $("input#command").focus();
  container = $("html, body");
  scrollTo = $("input#command");
  container.scrollTop(scrollTo.offset().top - container.offset().top);
}

update_contents = function() {
  $.ajax({
    url: "output",
    type: "GET",
    dataType: "json",
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
}