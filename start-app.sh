#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_PORT=8050
ACTION="${1:-start}"

if [[ "$ACTION" == "start" ]]; then
    if command -v gnome-terminal >/dev/null 2>&1; then
        gnome-terminal --working-directory="$SCRIPT_DIR" -- bash -lc "cd '$SCRIPT_DIR' && . .venv/bin/activate && python app.py"
    elif command -v x-terminal-emulator >/dev/null 2>&1; then
        x-terminal-emulator -e bash -lc "cd '$SCRIPT_DIR' && . .venv/bin/activate && python app.py"
    elif command -v konsole >/dev/null 2>&1; then
        konsole --workdir "$SCRIPT_DIR" -e bash -lc "cd '$SCRIPT_DIR' && . .venv/bin/activate && python app.py"
    else
        echo "No supported terminal emulator was found on this Ubuntu system."
        echo "Run manually: cd '$SCRIPT_DIR' && . .venv/bin/activate && python app.py"
        exit 1
    fi

    echo "Started NHL Auction Draft Wiz in a separate terminal window."
    exit 0
fi

if [[ "$ACTION" == "stop" ]]; then
    PIDS=()
    while IFS= read -r pid; do
        [[ -n "$pid" ]] && PIDS+=("$pid")
    done < <(lsof -ti tcp:"$APP_PORT" 2>/dev/null || true)

    if [[ ${#PIDS[@]} -eq 0 ]]; then
        echo "No app process is running on port $APP_PORT."
        exit 0
    fi

    for pid in "${PIDS[@]}"; do
        kill "$pid"
        echo "Stopped process PID $pid"
    done
    exit 0
fi

cat <<EOF
Usage: $0 [start|stop]

Examples:
  $0 start
  $0 stop
EOF
exit 1
