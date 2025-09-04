from flask import Flask, render_template
import os, json
from jinja2 import ChoiceLoader, FileSystemLoader

# Import your blueprints
from routes.region_selector import region_selector_bp

def create_app():
    app = Flask(__name__, template_folder="templates")  # main templates/

    # Add extra template folder (Templates/)
    app.jinja_loader = ChoiceLoader([
        app.jinja_loader,  # keep the default (templates/)
        FileSystemLoader(os.path.join(os.path.dirname(__file__), "Templates"))
    ])

    # Register blueprints
    app.register_blueprint(region_selector_bp, url_prefix="/regions")

    # Load regions from JSON-data/selected_regions.json
    JSON_FILE = os.path.join("JSON-data", "selected_regions.json")

    def load_regions():
        with open(JSON_FILE, "r") as f:
            return json.load(f)

    @app.route("/")
    def index():
        regions = load_regions()
        return render_template("index.html", regions=regions)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=80, debug=True)
