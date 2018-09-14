window.onload = function() {
    var select_all = document.getElementById("select_all");
    if (select_all) {
        select_all.addEventListener("click", function() {
            var checkboxes = document.getElementsByClassName("checkbox");
            if (select_all.checked) {
                for (var i = 0; i < checkboxes.length; i++) {
                    checkboxes[i].checked = true;
                }
            } else {
                for (var i = 0; i < checkboxes.length; i++) {
                    checkboxes[i].checked = false;
                }
            }
        });
    }
    var stage_button = document.getElementById("stage_button");
    if (stage_button) {
        stage_button.addEventListener("click", function() {
            var checkboxes = document.getElementsByClassName("project_checkbox");
            var ids = [];
            for (var i = 0; i < checkboxes.length; i++) {
                if (checkboxes[i].checked) {
                    ids.push(checkboxes[i].id);
                }
            }
            $.ajax({
                type: "POST",
                url: "stage",
                data: ids.toString(),
                success: function(data) {
                    console.log(data);
                }
            });
        });
    }
    var projects_table = document.getElementById("projects_table");
    if (projects_table) {
        $.ajax({
            type: "GET",
            url: "data/stage",
            success: function(data) {
                for (var i = 0; i < data.length; i++) {
                    document.getElementById(data[i].id).checked = true;
                }
            }
        });
    }
};