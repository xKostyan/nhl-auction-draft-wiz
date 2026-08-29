from src.dashboard import build_dashboard


if __name__ == "__main__":
    app = build_dashboard()
    app.run(debug=True, host="0.0.0.0", port=8050)
