from flask import Flask, render_template, redirect, url_for
from fetch_env_data import main as generate_report
from datetime import datetime

app = Flask(__name__)

@app.route("/")
def index():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return render_template("index.html", timestamp=timestamp)

@app.route("/fetch")
def fetch():
    generate_report()
    return redirect(url_for("report"))

@app.route("/report")
def report():
    return render_template("report.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7432, debug=True)
