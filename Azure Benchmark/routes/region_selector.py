from flask import Blueprint, render_template, request
import json, os

# Blueprint uses lowercase "templates" for shared templates (region_selector.html)
region_selector_bp = Blueprint("region_selector", __name__, template_folder="../templates")

# JSON paths
JSON_DIR = "JSON-data"
SELECTED_FILE = os.path.join(JSON_DIR, "selected_regions.json")
REGIONS_FILE = os.path.join(JSON_DIR, "regions.json")

def load_selected_regions():
    """Load selected regions from JSON file if it exists."""
    if os.path.exists(SELECTED_FILE):
        with open(SELECTED_FILE) as f:
            return json.load(f)
    return []

@region_selector_bp.route("/", methods=["GET", "POST"])
def index():
    """Show all regions with multi-select and save selection to JSON."""
    with open(REGIONS_FILE) as f:
        regions = json.load(f)

    preselected = load_selected_regions()
    saved = False

    if request.method == "POST":
        selected = request.form.getlist("selected_regions")
        with open(SELECTED_FILE, "w") as f:
            json.dump(selected, f, indent=2)
        saved = True
        preselected = selected

    return render_template(
        "region_selector.html",
        regions=regions,
        preselected=preselected,
        saved=saved,
        selected_file=SELECTED_FILE
    )

@region_selector_bp.route("/<name>")
def region_page(name):
    """
    Serve region-specific HTML from Templates/.
    If not found, generate a simple placeholder page.
    """
    selected_regions = load_selected_regions()

    if name not in selected_regions:
        return f"<h1>Region '{name}' is not selected.</h1>", 404

    try:
        # Because we configured ChoiceLoader in app.py,
        # Flask will look in both templates/ and Templates/
        return render_template(f"{name}.html")
    except Exception:
        # Fallback if HTML file doesn’t exist
        return f"""
        <h1>Welcome to {name}</h1>
        <p>No static HTML found in Templates/, so this was generated dynamically.</p>
        <a href='/'>Back to index</a>
        """
