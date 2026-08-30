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
            padding: "0 4px"
        }
    }, bars);
};
