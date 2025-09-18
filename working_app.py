"""
WORKING APP - Simple as possible
"""
import dash
from dash import html, dcc, callback, Input, Output, State, ALL
import dash_bootstrap_components as dbc

from config import APP_HOST, APP_PORT, DEBUG_MODE, MODULES

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
app.title = "SchwaOptions - Working"

app.layout = html.Div([
    dcc.Store(id="current-ticker", data="SPY"),
    html.Link(rel="stylesheet", href="/assets/terminal.css"),
    
    # Header
    dbc.Navbar([
        dbc.Container([
            dbc.Row([
                dbc.Col(html.H4("SchwaOptions Analytics", className="mb-0")),
                dbc.Col(dbc.Button("Dashboard", id="dashboard-btn", color="outline-light", size="sm"), width="auto")
            ])
        ])
    ], color="dark", dark=True, className="mb-4"),
    
    # Content
    dbc.Container([
        # Ticker Input
        dbc.Card([
            dbc.CardBody([
                html.H5("Ticker"),
                dbc.InputGroup([
                    dbc.Input(id="ticker", value="SPY"),
                    dbc.Button("Set", id="set-ticker", color="success")
                ]),
                html.Small(id="ticker-info", className="text-muted mt-1")
            ])
        ], className="mb-4"),
        
        # Main content
        html.Div(id="content")
    ], fluid=True)
])

@callback(
    [Output("current-ticker", "data"),
     Output("ticker-info", "children")],
    Input("set-ticker", "n_clicks"),
    State("ticker", "value"),
    prevent_initial_call=True
)
def set_ticker(n, ticker):
    if ticker:
        return ticker.upper(), f"Set to {ticker.upper()}"
    return "SPY", "Using SPY"

@callback(
    Output("content", "children"),
    [Input("dashboard-btn", "n_clicks"),
     Input({"type": "back", "index": ALL}, "n_clicks"),
     Input({"type": "module", "index": ALL}, "n_clicks"),
     Input("current-ticker", "data")]
)
def update_content(dash_clicks, back_clicks, module_clicks, ticker):
    ctx = dash.callback_context
    
    # Check what was clicked
    if ctx.triggered:
        trigger = ctx.triggered[0]["prop_id"]
        if "module" in trigger:
            import json
            module_id = json.loads(trigger.split(".")[0])["index"]
            module = next(m for m in MODULES if m["id"] == module_id)
            
            return html.Div([
                dbc.Row([
                    dbc.Col(dbc.Button("← Back", id={"type": "back", "index": "dash"}, color="outline-primary", size="sm"), width="auto"),
                    dbc.Col(html.H3(f"{module['name']} - {ticker}"))
                ], className="mb-3"),
                dbc.Alert(f"Module: {module['name']} for {ticker} would load here", color="success")
            ])
    
    # Default: show dashboard
    cards = []
    for module in MODULES[:6]:
        card = dbc.Card([
            dbc.CardBody([
                html.H5(module["name"]),
                html.P(module["description"], className="small"),
                dbc.Button("Open", id={"type": "module", "index": module["id"]}, color="primary", size="sm")
            ])
        ])
        cards.append(dbc.Col(card, md=4, className="mb-3"))
    
    return html.Div([
        html.H2(f"Dashboard - {ticker}", className="mb-4"),
        dbc.Row(cards)
    ])

if __name__ == "__main__":
    app.run_server(host=APP_HOST, port=APP_PORT, debug=DEBUG_MODE)