
function updateInput(id, description) {
    var elem = document.getElementById(id);
    if (elem.value == '') {
        elem.value = description;
    }
}
