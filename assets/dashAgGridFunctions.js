var dagfuncs = window.dashAgGridFunctions = window.dashAgGridFunctions || {};

dagfuncs.actualGpSparkline = function (params) {
    var history = Array.isArray(params.value) ? params.value : [];
    var chart = document.createElement("div");
    chart.className = "actual-gp-sparkline";

    history.slice().reverse().forEach(function (season) {
        var gamesPlayed = Math.max(0, Math.min(84, Number(season.games_played) || 0));
        var bar = document.createElement("span");
        var percentage = gamesPlayed / 84 * 100;

        bar.className = "actual-gp-bar " + (
            gamesPlayed <= 50 ? "actual-gp-red" :
            gamesPlayed <= 60 ? "actual-gp-orange" :
            gamesPlayed <= 71 ? "actual-gp-yellow" : "actual-gp-green"
        );
        bar.style.height = Math.max(2, percentage) + "%";
        bar.title = season.year + ": " + gamesPlayed + " actual GP";
        chart.appendChild(bar);
    });

    return chart;
};
