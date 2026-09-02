var dagcomponentfuncs = window.dashAgGridComponentFunctions =
    window.dashAgGridComponentFunctions || {};

dagcomponentfuncs.actualGpSparkline = function (props) {
    if (props.data && props.data.is_empty_slot) {
        return null;
    }
    var history = Array.isArray(props.value) ? props.value : [];
    var bars = history.slice().reverse().map(function (season) {
        var gamesPlayed = Math.max(0, Math.min(84, Number(season.games_played) || 0));
        var percentage = gamesPlayed / 84 * 100;
        var color = gamesPlayed <= 50 ? "#d32f2f" :
            gamesPlayed <= 60 ? "#ef6c00" :
            gamesPlayed <= 71 ? "#f9a825" : "#388e3c";

        return React.createElement("div", {
            key: season.year,
            title: season.year + ": " + gamesPlayed + " actual GP",
            style: {
                flex: "1 1 0",
                height: "100%",
                position: "relative"
            }
        }, [
            React.createElement("span", {
                key: "bar",
                style: {
                    backgroundColor: color,
                    bottom: "0",
                    height: percentage + "%",
                    left: "10%",
                    position: "absolute",
                    right: "10%"
                }
            }),
            React.createElement("span", {
                key: "label",
                style: {
                    bottom: "50%",
                    color: "#333",
                    fontSize: "9px",
                    left: "50%",
                    position: "absolute",
                    transform: "translate(-50%, 50%)",
                    whiteSpace: "nowrap",
                    zIndex: "2"
                }
            }, String(gamesPlayed))
        ]);
    });

    return React.createElement("div", {
        style: {
            alignItems: "end",
            boxSizing: "border-box",
            display: "flex",
            gap: "1px",
            height: "calc(100% - 10px)",
            justifyContent: "center",
            padding: "1px 4px"
        }
    }, bars);
};

dagcomponentfuncs.goalieGameStartsChart = function (props) {
    if (props.data && props.data.is_empty_slot) {
        return null;
    }
    var history = Array.isArray(props.value) ? props.value : [];
    var scaleMaximum = 70;
    var pointCount = history.length;
    var linePoints = history.map(function (season, index) {
        var projected = Math.max(0, Math.min(scaleMaximum, Number(season.projected) || 0));
        var x = pointCount > 1 ? index / (pointCount - 1) * 100 : 50;
        var y = 100 - projected / scaleMaximum * 100;
        return x + "," + y;
    });
    var lineDots = history.map(function (season, index) {
        var projected = Math.max(0, Math.min(scaleMaximum, Number(season.projected) || 0));
        var x = pointCount > 1 ? index / (pointCount - 1) * 100 : 50;
        var y = 100 - projected / scaleMaximum * 100;
        return React.createElement("circle", {
            cx: x,
            cy: y,
            fill: "#1565c0",
            key: season.year,
            r: "2"
        });
    });
    var bars = history.map(function (season) {
        var actual = Math.max(0, Math.min(scaleMaximum, Number(season.actual) || 0));
        var projected = Math.max(0, Math.min(scaleMaximum, Number(season.projected) || 0));
        var percentage = actual / scaleMaximum * 100;
        var color = actual < 30 ? "#d32f2f" : actual <= 42 ? "#f9a825" : "#388e3c";

        return React.createElement("div", {
            key: season.year,
            title: season.year + ": " + projected + " projected, " + actual + " actual game starts",
            style: {
                flex: "1 1 0",
                height: "100%",
                position: "relative"
            }
        }, [
            React.createElement("span", {
                key: "bar",
                style: {
                    backgroundColor: color,
                    bottom: "0",
                    height: percentage + "%",
                    left: "10%",
                    position: "absolute",
                    right: "10%"
                }
            }),
            React.createElement("span", {
                key: "label",
                style: {
                    bottom: "50%",
                    color: "#333",
                    fontSize: "9px",
                    left: "50%",
                    position: "absolute",
                    transform: "translate(-50%, 50%)",
                    whiteSpace: "nowrap",
                    zIndex: "2"
                }
            }, String(actual))
        ]);
    });

    return React.createElement("div", {
        style: {
            boxSizing: "border-box",
            display: "flex",
            gap: "1px",
            height: "calc(100% - 10px)",
            padding: "1px 4px",
            position: "relative",
            width: "100%"
        }
    }, [
        React.createElement("svg", {
            "aria-label": "Projected game starts",
            height: "100%",
            key: "projected-line",
            preserveAspectRatio: "none",
            style: { left: "4px", pointerEvents: "none", position: "absolute", top: "1px", width: "calc(100% - 8px)" },
            viewBox: "0 0 100 100",
            width: "100%"
        }, [
            React.createElement("polyline", {
                fill: "none",
                key: "line",
                points: linePoints.join(" "),
                stroke: "#1565c0",
                strokeWidth: "2"
            }),
            lineDots
        ]),
        bars
    ]);
};

dagcomponentfuncs.averagePerformanceChart = function (props) {
    if (props.data && props.data.is_empty_slot) {
        return null;
    }
    var history = Array.isArray(props.value) ? props.value : [];
    var scaleMaximum = props.scaleMaximum;
    var pointCount = history.length;
    var linePoints = history.map(function (season, index) {
        var projected = Math.max(0, Math.min(scaleMaximum, Number(season.projected) || 0));
        var x = pointCount > 1 ? index / (pointCount - 1) * 100 : 50;
        var y = 100 - projected / scaleMaximum * 100;
        return x + "," + y;
    });
    var lineDots = history.map(function (season, index) {
        var projected = Math.max(0, Math.min(scaleMaximum, Number(season.projected) || 0));
        var x = pointCount > 1 ? index / (pointCount - 1) * 100 : 50;
        var y = 100 - projected / scaleMaximum * 100;
        return React.createElement("circle", { cx: x, cy: y, fill: "#1565c0", key: season.year, r: "2" });
    });
    var bars = history.map(function (season) {
        var actual = Math.max(0, Math.min(scaleMaximum, Number(season.actual) || 0));
        var projected = Math.max(0, Math.min(scaleMaximum, Number(season.projected) || 0));
        var percentage = actual / scaleMaximum * 100;
        var color = scaleMaximum === 6
            ? actual <= 3.1 ? "#d32f2f" : actual <= 3.5 ? "#ef6c00" : actual <= 3.9 ? "#f9a825" : "#388e3c"
            : actual < 7 ? "#d32f2f" : actual <= 7.5 ? "#ef6c00" : actual <= 8 ? "#f9a825" : "#388e3c";

        return React.createElement("div", {
            key: season.year,
            title: season.year + ": " + projected + " projected, " + actual + " actual average fantasy points",
            style: { flex: "1 1 0", height: "100%", position: "relative" }
        }, [
            React.createElement("span", {
                key: "bar",
                style: { backgroundColor: color, bottom: "0", height: percentage + "%", left: "10%", position: "absolute", right: "10%" }
            }),
            React.createElement("span", {
                key: "label",
                style: {
                    bottom: "50%", color: "#333", fontSize: "9px", left: "50%",
                    position: "absolute", transform: "translate(-50%, 50%)",
                    whiteSpace: "nowrap", zIndex: "2"
                }
            }, actual.toFixed(1))
        ]);
    });

    return React.createElement("div", {
        style: {
            boxSizing: "border-box", display: "flex", gap: "1px",
            height: "calc(100% - 10px)", padding: "1px 4px",
            position: "relative", width: "100%"
        }
    }, [
        React.createElement("svg", {
            "aria-label": "Projected average fantasy points",
            height: "100%",
            key: "projected-line",
            preserveAspectRatio: "none",
            style: { left: "4px", pointerEvents: "none", position: "absolute", top: "1px", width: "calc(100% - 8px)" },
            viewBox: "0 0 100 100",
            width: "100%"
        }, [
            React.createElement("polyline", {
                fill: "none", key: "line", points: linePoints.join(" "),
                stroke: "#1565c0", strokeWidth: "2"
            }),
            lineDots
        ]),
        bars
    ]);
};

dagcomponentfuncs.playerTagsRenderer = function (props) {
    var selectedTags = Array.isArray(props.value) ? props.value : [];
    var availableTags = Array.isArray(props.availableTags) ? props.availableTags : [];
    var tagColors = props.tagColors || {};
    var isEmptySlot = Boolean(props.data && props.data.is_empty_slot);
    var editingState = React.useState(false);
    var editing = editingState[0];
    var setEditing = editingState[1];

    var tagChip = function (tag, selected, onClick, fontSize) {
        var tagColor = tagColors[tag] || "yellow";
        var colors = tagColor === "green"
            ? { active: "#a5d6a7", border: "#66bb6a" }
            : tagColor === "red"
                ? { active: "#ef9a9a", border: "#e57373" }
                : { active: "#fff59d", border: "#fbc02d" };
        return React.createElement("button", {
            "aria-label": (selected ? "Remove " : "Add ") + tag + " tag",
            "aria-pressed": selected,
            key: tag,
            onClick: onClick,
            style: {
                backgroundColor: selected ? colors.active : "#f5f5f5",
                border: "1px solid " + colors.border,
                borderRadius: "3px",
                color: "#333",
                cursor: "pointer",
                fontSize: fontSize || "9px",
                padding: "1px 3px"
            },
            title: selected ? "Remove " + tag : "Add " + tag,
            type: "button"
        }, tag);
    };

    if (isEmptySlot) {
        return null;
    }

    return React.createElement("div", {
        onClick: function (event) {
            event.stopPropagation();
            setEditing(true);
        },
        style: {
            display: "flex",
            flexWrap: "wrap",
            gap: "2px",
            justifyContent: "flex-start",
            minHeight: "16px",
            position: "relative",
            width: "100%"
        }
    }, editing
        ? React.createElement("div", {
            onClick: function (event) { event.stopPropagation(); },
            style: {
                backgroundColor: "#fff",
                border: "1px solid #bbb",
                borderRadius: "4px",
                boxShadow: "0 2px 6px rgba(0, 0, 0, 0.2)",
                display: "flex",
                flexWrap: "wrap",
                gap: "3px",
                left: "0",
                padding: "4px",
                position: "absolute",
                top: "50%",
                transform: "translateY(-50%)",
                width: "150px",
                zIndex: "3"
            }
        }, availableTags.map(function (tag) {
            var selected = selectedTags.indexOf(tag) !== -1;
            return tagChip(tag, selected, function (event) {
                event.stopPropagation();
                props.setValue(selected
                    ? selectedTags.filter(function (selectedTag) { return selectedTag !== tag; })
                    : selectedTags.concat(tag));
            });
        }).concat(React.createElement("button", {
            "aria-label": "Close tag editor",
            key: "close",
            onClick: function (event) {
                event.stopPropagation();
                setEditing(false);
            },
            style: {
                backgroundColor: "#fff",
                border: "1px solid #999",
                borderRadius: "3px",
                cursor: "pointer",
                fontSize: "9px",
                padding: "1px 3px"
            },
            type: "button"
        }, "Done")))
        : selectedTags.length
            ? selectedTags.map(function (tag) {
                return tagChip(tag, true, function (event) {
                    event.stopPropagation();
                    setEditing(true);
                }, "11px");
            })
            : React.createElement("span", {
                style: { color: "#bbb", cursor: "pointer", fontSize: "12px" }
            }, "+"));
};

dagcomponentfuncs.playerNameContextMenuRenderer = function (props) {
    var menuState = React.useState(false);
    var menuOpen = menuState[0];
    var setMenuOpen = menuState[1];
    var menuPositionState = React.useState({ left: 0, top: 0 });
    var menuPosition = menuPositionState[0];
    var setMenuPosition = menuPositionState[1];
    var menuRef = React.useRef(null);
    var allowAddToMyTeam = Boolean(props.allowAddToMyTeam);
    var isEmptySlot = Boolean(props.data && props.data.is_empty_slot);
    var addToMyTeamError = props.data && props.data.my_team_add_error;

    React.useEffect(function () {
        if (!menuOpen) {
            return undefined;
        }

        var closeOnOutsideLeftClick = function (event) {
            if (event.button === 0 && menuRef.current && !menuRef.current.contains(event.target)) {
                setMenuOpen(false);
            }
        };
        document.addEventListener("mousedown", closeOnOutsideLeftClick);
        return function () {
            document.removeEventListener("mousedown", closeOnOutsideLeftClick);
        };
    }, [menuOpen]);

    var runAction = function (action, event) {
        event.preventDefault();
        event.stopPropagation();
        if (action === "select-player") {
            props.node.setSelected(true, true);
        }
        if (action === "add-to-my-team" || action === "remove-from-my-team") {
            props.node.setData(Object.assign({}, props.data, {
                on_my_team: action === "add-to-my-team"
            }));
        }
        // setData emits Dash AG Grid's cellRendererData prop with this row's id.
        props.setData({ action: action, timestamp: Date.now() });
        setMenuOpen(false);
    };
    var menuAction = function (label, action, disabled, title) {
        return React.createElement("button", {
            disabled: Boolean(disabled),
            key: action,
            onClick: function (event) { runAction(action, event); },
            style: {
                backgroundColor: disabled ? "#f2f2f2" : "#fff",
                border: "none",
                color: disabled ? "#888" : "#222",
                cursor: disabled ? "not-allowed" : "pointer",
                display: "block",
                padding: "6px 10px",
                textAlign: "left",
                width: "100%"
            },
            title: title || label,
            type: "button"
        }, label);
    };

    return React.createElement("div", {
        onContextMenu: function (event) {
            event.preventDefault();
            event.stopPropagation();
            if (isEmptySlot) {
                return;
            }
            setMenuPosition({ left: event.clientX, top: event.clientY });
            setMenuOpen(true);
        },
        style: { position: "relative", width: "100%" }
    }, [
        React.createElement("span", { key: "name" }, props.value),
        !isEmptySlot && menuOpen ? ReactDOM.createPortal(React.createElement("div", {
            key: "menu",
            ref: menuRef,
            role: "menu",
            onContextMenu: function (event) {
                event.preventDefault();
                event.stopPropagation();
            },
            style: {
                backgroundColor: "#fff",
                border: "1px solid #999",
                borderRadius: "4px",
                boxShadow: "0 2px 6px rgba(0, 0, 0, 0.2)",
                left: menuPosition.left + "px",
                minWidth: "155px",
                position: "fixed",
                top: menuPosition.top + "px",
                zIndex: "10000"
            }
        }, [
            menuAction("Highlight the player", "select-player"),
            menuAction("Clear Tags", "clear-tags"),
            menuAction("Clear Notes", "clear-notes"),
            allowAddToMyTeam ? menuAction(
                "Add to My Team", "add-to-my-team", Boolean(addToMyTeamError), addToMyTeamError
            ) : null,
            menuAction("Remove from My Team", "remove-from-my-team")
        ]), document.body) : null
    ]);
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

    if (props.data && props.data.is_empty_slot) {
        return null;
    }

    var onMyTeam = Boolean(props.data && props.data.on_my_team);
    return React.createElement("button", {
        "aria-label": selected
            ? "Player highlighted"
            : onMyTeam ? "Player is on My Team" : "Highlight player",
        "aria-pressed": selected,
        onClick: function (event) {
            event.stopPropagation();
            props.node.setSelected(true, true);
            props.setData({ action: "select-player", timestamp: Date.now() });
        },
        style: {
            backgroundColor: selected ? "#388e3c" : onMyTeam ? "#90caf9" : "#d3d3d3",
            border: "none",
            borderRadius: "50%",
            cursor: "pointer",
            height: "14px",
            padding: "0",
            width: "14px"
        },
        title: selected ? "Highlighted player" : onMyTeam ? "On My Team" : "Highlight player",
        type: "button"
    });
};
