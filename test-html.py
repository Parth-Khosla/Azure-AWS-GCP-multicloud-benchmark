from flask import Flask, render_template

# Initialize the Flask application.
# By setting template_folder='.', Flask will look for template files
# in the current working directory (the same folder as this file).
app = Flask(__name__, template_folder='.')

# Define the route for the home page.
@app.route('/')
def display_html_file():
    """
    Renders the 'index.html' file found in the same directory as app.py.
    This demonstrates serving an HTML file without using the conventional 
    'templates' subdirectory.
    """
    print("Serving index.html from the current working directory.")
    return render_template('regions.html')

# Run the application
if __name__ == '__main__':
    # You can access the app at http://127.0.0.1:5000/
    print("Starting Flask application. Ensure you have an 'index.html' file in the same directory.")
    app.run(debug=True)
