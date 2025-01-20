$(function () {
    if ($("#return_result").text() != "") {
        let video_file_name = $("#video_file_name").text();
        $("#myVideo").attr("src", "http://127.0.0.1:5001/static/data/"+video_file_name);
        $("#message").prop('disabled', false);
        $("#submit").prop('disabled', false);
    } else {
        console.log("No data");
    }
    $("#submit").click(chatWithData);
    $("#message").keypress(function (e) {
        if (e.which == 13) {
            chatWithData();
        }
    });

    $('#myform').submit(function () {
        $("#return_result").text("Please wait...");
    });

});

function chatWithData() {
    var message = $("#message").val();
    $("#dialog").append("我 : " + message + "\n");
    var data = {
        message: message
    };
    $.post("/call_gemini", data, function (data) {
        $("#dialog").append("AI : " + data + "\n");
        $("#dialog").scrollTop($("#dialog")[0].scrollHeight);
    });
    $("#message").val("");
    $("#dialog").scrollTop($("#dialog")[0].scrollHeight);
}