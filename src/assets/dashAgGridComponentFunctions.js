var dagcomponentfuncs = window.dashAgGridComponentFunctions =
    window.dashAgGridComponentFunctions || {};

dagcomponentfuncs.actualGpSparkline = function (props) {
    var history = Array.isArray(props.value) ? props.value : [];
    var bars = history.slice().reverse().map(function (season) {
        var gamesPlayed = Math.max(0, Math.min(84, Number(season.games_played) || 0));
        var percentage = gamesPlayed / 84 * 100;
        var color = gamesPlayed <= 50 ? "#d32f2f" :
            gamesPlayed <= 60 ? "#ef6c00" :
            gamesPlayed <= 71 ? "#f9a825" : "#388e3c";

        return React.createElement("span", {
            key: season.year,
            title: season.year + ": " + gamesPlayed + " actual GP",
            style: {
                backgroundColor: color,
                display: "block",
                height: Math.max(2, percentage) + "%",
                minWidth: "10px"
            }
        });
    });

    return React.createElement("div", {
        style: {
            alignItems: "end",
            display: "flex",
            gap: "3px",
            height: "28px",
            justifyContent: "center",
            padding: "1px 4px"
        }
    }, bars);
};

dagcomponentfuncs.draftedSwitchRenderer = function (props) {
    var drafted = Boolean(props.value);
    var available = !drafted;

    return React.createElement("button", {
        "aria-label": available ? "Mark player as drafted" : "Mark player as available",
        "aria-pressed": available,
        onClick: function (event) {
            event.stopPropagation();
            props.setValue(available);
        },
        style: {
            backgroundColor: available ? "#388e3c" : "#bdbdbd",
            border: "none",
            borderRadius: "8px",
            cursor: "pointer",
            height: "14px",
            padding: "2px",
            width: "22px"
        },
        title: available ? "Available" : "Drafted",
        type: "button"
    }, React.createElement("span", {
        style: {
            backgroundColor: "#fff",
            borderRadius: "50%",
            display: "block",
            height: "10px",
            transform: available ? "translateX(8px)" : "translateX(0)",
            transition: "transform 120ms ease",
            width: "10px"
        }
    }));
};

dagcomponentfuncs.searchFocusCircleRenderer = function (props) {
    var selection = React.useState(props.node.isSelected());
    var selected = selection[0];
    var setSelected = selection[1];

    React.useEffect(function () {
        var updateSelection = function () {
            setSelected(props.node.isSelected());
        };

        props.node.addEventListener("rowSelected", updateSelection);
        updateSelection();
        return function () {
            props.node.removeEventListener("rowSelected", updateSelection);
        };
    }, [props.node]);

    return React.createElement("button", {
        "aria-label": selected ? "Player highlighted" : "Highlight player",
        "aria-pressed": selected,
        onClick: function (event) {
            event.stopPropagation();
            props.node.setSelected(!selected, true);
        },
        style: {
            backgroundColor: selected ? "#388e3c" : "#d3d3d3",
            border: "none",
            borderRadius: "50%",
            cursor: "pointer",
            height: "14px",
            padding: "0",
            width: "14px"
        },
        title: selected ? "Highlighted player" : "Highlight player",
        type: "button"
    });
};
