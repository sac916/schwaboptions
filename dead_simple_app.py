"""
DEAD SIMPLE navigation that just works
No fancy routing, no complex callbacks, just buttons that work
"""
import dash
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
from datetime import datetime

from config import APP_HOST, APP_PORT, DEBUG_MODE, MODULES

# Simple app
app = dash.Dash(
    __name__, 
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&display=swap"
    ],
    suppress_callback_exceptions=True
)

app.title = "SchwaOptions Analytics - WORKING Navigation"

# Simple stores
stores = html.Div([
    dcc.Store(id="current-view", data="dashboard"),
    dcc.Store(id="current-ticker", data="SPY"),
    html.Link(rel="stylesheet", href="/assets/terminal.css")
])

# Simple header
def create_header():
    return dbc.Navbar([
        dbc.Row([
            dbc.Col([
                html.Span("SchwaOptions Analytics", style={"fontSize": "1.5rem", "fontWeight": "700"})
            ]),
            dbc.Col([
                dbc.Button("🏠 Dashboard", id="home-btn", color="outline-light", size="sm")
            ], width="auto", className="ms-auto")
        ], align="center", className="w-100")
    ], color="dark", dark=True, className="mb-4")

# Simple ticker input
def create_ticker_input():
    return dbc.Card([
        dbc.CardBody([
            html.H5("Current Symbol"),
            dbc.Row([
                dbc.Col([
                    dbc.Input(id="ticker-input", placeholder="Enter ticker", debounce=True)
                ], width=8),
                dbc.Col([
                    dbc.Button("Update", id="ticker-btn", color="success", className="w-100")
                ], width=4)
            ]),
            html.Div(id="ticker-status", className="mt-2")
        ])
    ], className="mb-4")

# Simple module grid
def create_module_grid():
    cards = []
    for i, module in enumerate(MODULES[:6]):  # Only working modules
        card = dbc.Card([
            dbc.CardBody([
                html.H5(module["name"], className="text-center"),
                html.P(module["description"], className="small text-center"),
                dbc.Button("Launch", 
                          id={"type": "module-btn", "index": module["id"]}, 
                          color="primary", 
                          size="sm", 
                          className="w-100")
            ])
        ], className="h-100 module-card")
        
        cards.append(dbc.Col(card, width=12, md=6, lg=4, className="mb-3"))
    
    return dbc.Row(cards)

# Simple module page
def create_module_page(module_name, ticker):
    module = next((m for m in MODULES if m["id"] == module_name), None)
    if not module:
        return html.Div("Module not found")
    
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Button("← Back", id="back-btn", color="outline-primary", size="sm")
            ], width="auto"),
            dbc.Col([
                html.H3(f"📊 {module['name']} - {ticker}")
            ])
        ], className="mb-4"),
        
        dbc.Card([
            dbc.CardBody([
                html.H4(f"✅ {module['name']} Module"),
                html.P(f"Analysis for {ticker} would load here"),
                html.P("🚀 Navigation is working!"),
                html.P("Click ← Back to return to dashboard")
            ])
        ])
    ], fluid=True)

# Main layout
app.layout = html.Div([
    stores,
    create_header(),
    html.Div(id="main-content")
])

# Display current ticker
@callback(
    Output("ticker-input", "value"),
    Input("current-ticker", "data")
)
def show_current_ticker(ticker):
    return ticker

# SINGLE callback for everything
@callback(
    Output("main-content", "children"),
    [Input("current-view", "data"),
     Input("current-ticker", "data")]
)
def update_content(view, ticker):
    if view == "dashboard":
        return dbc.Container([
            create_ticker_input(),
            html.H2("Welcome to SchwaOptions Analytics", className="text-center mb-4"),
            html.P("Select a module:", className="text-center mb-4"),
            create_module_grid()
        ], fluid=True)
    else:
        return create_module_page(view, ticker)

# Navigation callbacks
@callback(
    Output("current-view", "data"),
    [Input("home-btn", "n_clicks"),
     Input("back-btn", "n_clicks"),
     Input({"type": "module-btn", "index": dash.ALL}, "n_clicks")],
    prevent_initial_call=True
)
def handle_navigation(home_clicks, back_clicks, module_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return "dashboard"
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if "home-btn" in button_id or "back-btn" in button_id:
        return "dashboard"
    
    if "module-btn" in button_id:
        import json
        button_info = json.loads(button_id)
        return button_info["index"]
    
    return "dashboard"

# Ticker callback
@callback(
    [Output("current-ticker", "data"),
     Output("ticker-status", "children")],
    [Input("ticker-btn", "n_clicks"),
     Input("ticker-input", "n_submit")],
    State("ticker-input", "value"),
    prevent_initial_call=True
)
def update_ticker(btn_clicks, input_submit, ticker):
    if not ticker:
        return dash.no_update, "Enter a ticker"
    
    ticker = ticker.upper().strip()
    status = html.Span(f"✅ Ready to analyze {ticker}", className="text-success")
    return ticker, status

if __name__ == "__main__":
    print("🚀 Starting DEAD SIMPLE app that actually works...")
    print(f"📍 URL: http://127.0.0.1:{APP_PORT}")
    app.run_server(host=APP_HOST, port=APP_PORT, debug=DEBUG_MODE)