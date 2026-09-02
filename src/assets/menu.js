(function () {
    "use strict";

    document.addEventListener("mousedown", function (event) {
        var menu = document.getElementById("app-menu");
        var panel = document.getElementById("app-menu-panel");
        if (!menu || !panel || menu.contains(event.target) || panel.style.display === "none") {
            return;
        }

        window.dash_clientside.set_props("app-menu-panel", {
            style: { display: "none" }
        });
    });
}());
