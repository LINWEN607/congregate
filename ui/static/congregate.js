window.onload = function() {
    register_events();
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
    var projects_table = document.getElementById("users_table");
    if (projects_table) {
        $.ajax({
            type: "GET",
            url: "data/staged_users",
            success: function(data) {
                for (var i = 0; i < data.length; i++) {
                    document.getElementById(data[i].username).checked = true;
                }
            }
        });
    }
    var projects_table = document.getElementById("groups_table");
    if (projects_table) {
        $.ajax({
            type: "GET",
            url: "data/staged_groups",
            success: function(data) {
                for (var i = 0; i < data.length; i++) {
                    document.getElementById(data[i].path).checked = true;
                }
            }
        });
    }
};

function register_events() {
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
    var stage_button = document.getElementById("stage_groups");
    if (stage_button) {
        stage_button.addEventListener("click", function() {
            var checkboxes = document.getElementsByClassName("group_checkbox");
            var ids = [];
            for (var i = 0; i < checkboxes.length; i++) {
                if (checkboxes[i].checked) {
                    ids.push(checkboxes[i].id);
                }
            }
            $.ajax({
                type: "POST",
                url: "append_groups",
                data: ids.toString(),
                success: function(data) {
                    console.log(data);
                }
            });
        });
    }

    var stage_button = document.getElementById("stage_users");
    if (stage_button) {
        stage_button.addEventListener("click", function() {
            var checkboxes = document.getElementsByClassName("users_checkbox");
            var ids = [];
            for (var i = 0; i < checkboxes.length; i++) {
                if (checkboxes[i].checked) {
                    ids.push(checkboxes[i].id);
                }
            }
            $.ajax({
                type: "POST",
                url: "append_users",
                data: ids.toString(),
                success: function(data) {
                    console.log(data);
                }
            });
        });
    }

    var stage_button = document.getElementById("update_config_button");
    if (stage_button) {
        stage_button.addEventListener("click", function() {
            var config_keys = document.getElementsByClassName("config_key");
            var config_values = document.getElementsByClassName("config_value");
            var conf_obj = {};
            for (var i = 0; i < config_keys.length; i++) {
                conf_obj[config_keys[i].innerHTML] = config_values[i].value;
            }
            $.ajax({
                type: "POST",
                url: "update_config",
                data: JSON.stringify(conf_obj),
                success: function(data) {
                    console.log(data);
                }
            });
        });
    }
}