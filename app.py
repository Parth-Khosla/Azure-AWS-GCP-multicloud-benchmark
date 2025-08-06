from flask import Flask, render_template, redirect, url_for
from fetch_env_data import main as generate_report
from fetch_os_images import fetch_all_os_images
from display_os_image import display_os_images
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

@app.route("/fetch_os_images")
def fetch_os():
    fetch_all_os_images()
    display_os_images()
    return redirect(url_for("view_os_images"))

@app.route("/os_images")
def view_os_images():
    return render_template("os_images.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7432, debug=True)
