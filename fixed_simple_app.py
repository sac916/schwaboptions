"""
FIXED SIMPLE navigation - no callback conflicts
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

app.title = "SchwaOptions Analytics - FIXED"

# Layout with everything inline - no recreation issues
app.layout = html.Div([
    # Stores
    dcc.Store(id="current-view", data="dashboard"),
    dcc.Store(id="current-ticker", data="SPY"),
    html.Link(rel="stylesheet", href="/assets/terminal.css"),
    
    # Fixed Header
    dbc.Navbar([
        dbc.Row([
            dbc.Col([
                html.Span("SchwaOptions Analytics", style={"fontSize": "1.5rem", "fontWeight": "700"})
            ]),
            dbc.Col([
                dbc.Button("🏠 Dashboard", id="home-btn", color="outline-light", size="sm")
            ], width="auto", className="ms-auto")
        ], align="center", className="w-100")
    ], color="dark", dark=True, className="mb-4"),
    
    # Fixed Ticker Section (always visible)
    dbc.Container([
        dbc.Card([
            dbc.CardBody([
                html.H5([
                    "Current Symbol: ",
                    html.Span(id="ticker-display", children="SPY", style={"color": "#50fa7b"})
                ]),
                dbc.Row([
                    dbc.Col([
                        dbc.Input(id="ticker-input", placeholder="Enter new ticker (e.g. NVDA)", debounce=True)
                    ], width=8),
                    dbc.Col([
                        dbc.Button("Update", id="ticker-btn", color="success", className="w-100")
                    ], width=4)
                ]),
                html.Div(id="ticker-status", className="mt-2")
            ])
        ], className="mb-4"),
        
        # Main content
        html.Div(id="main-content")
    ], fluid=True)
])

# Simple content callback
@callback(
    Output("main-content", "children"),
    [Input("current-view", "data"),
     Input("current-ticker", "data")]
)
def update_main_content(view, ticker):
    if view == "dashboard":
        # Dashboard content
        cards = []
        for i, module in enumerate(MODULES[:6]):
            card = dbc.Card([
                dbc.CardBody([
                    html.H5(module["name"], className="text-center"),
                    html.P(module["description"], className="small text-center text-muted"),
                    dbc.Button("Launch", 
                              id={"type": "module-btn", "index": module["id"]}, 
                              color="primary", 
                              size="sm", 
                              className="w-100")
                ])
            ], className="h-100 module-card")
            
            cards.append(dbc.Col(card, width=12, md=6, lg=4, className="mb-3"))
        
        return html.Div([
            html.H2("Welcome to SchwaOptions Analytics", className="text-center mb-4"),
            html.P(f"Ready to analyze {ticker} options data", className="text-center mb-4 text-muted"),
            dbc.Row(cards)
        ])
    
    else:
        # Module content
        module = next((m for m in MODULES if m["id"] == view), None)
        if not module:
            return html.Div("Module not found")
        
        return html.Div([
            dbc.Row([
                dbc.Col([
                    dbc.Button("← Back to Dashboard", id="back-btn", color="outline-primary", size="sm")
                ], width="auto"),
                dbc.Col([
                    html.H3(f"📊 {module['name']} - {ticker}")
                ])
            ], className="mb-4"),
            
            dbc.Card([
                dbc.CardBody([
                    html.H4(f"✅ {module['name']} Module", className="text-success"),
                    html.P(f"Real-time options analysis for {ticker} will load here", className="text-muted"),
                    html.Hr(),
                    html.P("🚀 Navigation: WORKING", className="text-success"),
                    html.P("📊 Terminal Theme: ACTIVE", className="text-info"),
                    html.P(f"📈 Current Ticker: {ticker}", className="text-primary"),
                    html.P("Click ← Back to Dashboard to test navigation!", className="small text-muted")
                ])
            ])
        ])

# Navigation callback
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
    print(f"🔍 Button clicked: {button_id}")
    
    if "home-btn" in button_id or "back-btn" in button_id:
        return "dashboard"
    
    if "module-btn" in button_id:
        import json
        button_info = json.loads(button_id)
        return button_info["index"]
    
    return "dashboard"

# Ticker callback - ONLY updates on button click or enter
@callback(
    [Output("current-ticker", "data"),
     Output("ticker-display", "children"),
     Output("ticker-status", "children"),
     Output("ticker-input", "value")],
    [Input("ticker-btn", "n_clicks"),
     Input("ticker-input", "n_submit")],
    State("ticker-input", "value"),
    prevent_initial_call=True
)
def update_ticker(btn_clicks, input_submit, ticker_input):
    if not ticker_input or ticker_input.strip() == "":
        return dash.no_update, dash.no_update, "Enter a ticker symbol", dash.no_update
    
    new_ticker = ticker_input.upper().strip()
    status = html.Span(f"✅ Updated to {new_ticker}", className="text-success")
    
    print(f"🔍 Ticker updated to: {new_ticker}")
    
    # Return: new ticker, display ticker, status, clear input
    return new_ticker, new_ticker, status, ""

if __name__ == "__main__":
    print("🚀 Starting FIXED SIMPLE app...")
    print(f"📍 URL: http://127.0.0.1:{APP_PORT}")
    print("✅ No callback conflicts!")
    app.run_server(host=APP_HOST, port=APP_PORT, debug=DEBUG_MODE)