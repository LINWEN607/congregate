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
                    document.getElementById(data[i].id).checked = true;
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

            var output = document.getElementById('stage_log');
            var xhr = new XMLHttpRequest();
            xhr.open('GET', 'log');
            xhr.send();

            var updateLog = setInterval(function() {
                document.getElementById('stage_log').innerHTML = xhr.responseText;
            }, 1000);

            $.ajax({
                type: "POST",
                url: "stage",
                data: ids.toString(),
                success: function(data) {
                    console.log(data);
                    clearInterval(updateLog);
                    output.innerHTML = data;
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

            var output = document.getElementById('stage_log');
            var xhr = new XMLHttpRequest();
            xhr.open('GET', 'log');
            xhr.send();

            var updateLog = setInterval(function() {
                document.getElementById('stage_log').innerHTML = xhr.responseText;
            }, 1000);

            $.ajax({
                type: "POST",
                url: "append_groups",
                data: ids.toString(),
                success: function(data) {
                    console.log(data);
                    clearInterval(updateLog);
                    output.innerHTML = data;
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

            var output = document.getElementById('stage_log');
            var xhr = new XMLHttpRequest();
            xhr.open('GET', 'log');
            xhr.send();

            var updateLog = setInterval(function() {
                document.getElementById('stage_log').innerHTML = xhr.responseText;
            }, 1000);

            $.ajax({
                type: "POST",
                url: "append_users",
                data: ids.toString(),
                success: function(data) {
                    console.log(data);
                    clearInterval(updateLog);
                    output.innerHTML = data;
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
                    document.getElementById('stage_log').innerHTML = "Config updated";
                    console.log(data);
                },
                error: function(xhr, status, error) {
                    console.log(xhr);
                    console.log(status);
                    console.log(error);
                    document.getElementById('stage_log').innerHTML = error;
                }
            });
        });
    }

    var stage_button = document.getElementById("migrate_button");
    if (stage_button) {
        stage_button.addEventListener("click", function() {
            var migrationStatus = document.getElementById("migration-status");
            migrationStatus.style.display = "block";
            var output = document.getElementById('stage_log');
            var xhr = new XMLHttpRequest();
            xhr.open('GET', 'log');
            xhr.send();

            var updateLog = setInterval(function() {
                output.innerHTML = xhr.responseText;
            }, 1000);

            $.ajax({
                type: "GET",
                url: "migrate",
                success: function(data) {
                    console.log(data);
                    clearInterval(updateLog);
                    output.innerHTML = data;
                }
            });
        });
    }

    var filter_button = document.getElementById("filter_button");
    if (filter_button) {
        filter_button.addEventListener("click", function() {
            var number = document.getElementById("filter_number").value;
            var dropdown = document.getElementById("filter_dropdown").value;
            
            var checkbox = document.getElementById("active_checkbox").checked;
            var last_activity_at = document.getElementsByClassName("last_activity");
            var namespace = document.getElementsByClassName("namespace");
            var timestamp = new Date()
            if (dropdown == "days") {
                timestamp.setDate(timestamp.getDate() - parseInt(number))
            } else if (dropdown == "months") {
                timestamp.setMonth(timestamp.getMonth() - parseInt(number))
            }
            if (last_activity_at) {
                for (var i = 0; i < last_activity_at.length; i++) {
                    current_date_object = last_activity_at[i];
                    var d = new Date(current_date_object.innerHTML);
                    if (checkbox) {
                        if (d.getTime() >= timestamp) {
                            // current_date_object.style.color = "red";
                            var row = current_date_object.parentNode.getAttribute("data-thisid");
                            namespaceType = namespace[i].innerHTML.split("(");
                            // if (namespaceType[1].includes("user")) {
                                document.getElementById(row).checked = true;
                            // }
                        }
                    } else {
                        if (d.getTime() <= timestamp) {
                            // current_date_object.style.color = "red";
                            var row = current_date_object.parentNode.getAttribute("data-thisid");
                            namespaceType = namespace[i].innerHTML.split("(");
                            // if (namespaceType[1].includes("user")) {
                                document.getElementById(row).checked = true;
                            // }
                        }
                    }
                    
                    var n = d.toUTCString();
                    current_date_object.innerHTML = n;
                }
            }
        })
    }
}