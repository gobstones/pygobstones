
function update_input(id, description) {
    var elem = document.getElementById(id);
    if (elem.value == '') {
        elem.value = description;
    }
}

function set_focus(id) {
    var elem = document.getElementById(id);
    elem.focus();
    elem.select();
}

