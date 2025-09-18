"""
Clean, simple Dash app with URL routing - NO callback conflicts
"""
import dash
import dash_bootstrap_components as dbc

from config import APP_HOST, APP_PORT, DEBUG_MODE

# Create app first
app = dash.Dash(
    __name__, 
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&display=swap",
        "https://fonts.googleapis.com/css2?family=Fira+Code:wght@300;400;500;600;700&display=swap"
    ],
    suppress_callback_exceptions=True,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}]
)

app.title = "SchwaOptions Analytics - Clean Navigation"

# Import navigation functions
from simple_navigation import create_navigation_layout, register_callbacks

# Register callbacks with this app instance
register_callbacks(app)

# Simple layout
app.layout = create_navigation_layout

if __name__ == "__main__":
    print("🚀 Starting CLEAN navigation app...")
    print(f"📍 URL: http://127.0.0.1:{APP_PORT}")
    app.run_server(host=APP_HOST, port=APP_PORT, debug=DEBUG_MODE)