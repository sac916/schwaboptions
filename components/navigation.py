"""
ConvexValue-style module navigation grid
"""
import dash_bootstrap_components as dbc
from dash import html, dcc
from config import MODULES, THEME_CONFIG

def create_module_grid():
    """Create ConvexValue-style module grid navigation with enhanced UI"""
    
    module_cards = []
    for module in MODULES:
        # Create enhanced card with status indicators
        card = dbc.Card([
            dbc.CardHeader([
                dbc.Row([
                    dbc.Col([
                        html.Span(module["name"], className="fw-bold")
                    ], width="auto"),
                    dbc.Col([
                        html.Div([
                            html.Span("●", className="status-indicator me-1", 
                                    style={"color": THEME_CONFIG["accent_color"]}),
                            html.Small("Ready", className="text-muted small")
                        ])
                    ], width="auto", className="ms-auto")
                ], align="center")
            ], className="py-2"),
            dbc.CardBody([
                html.P(module["description"], className="card-text text-center small mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Button(
                            [html.I(className="fas fa-play me-1"), "Launch"],
                            id=f"{module['id']}-btn",
                            color="primary",
                            size="sm",
                            className="w-100 module-launch-btn",
                            n_clicks=0
                        )
                    ], width=12),
                ], className="mb-2"),
                # Module stats/info row
                html.Div([
                    dbc.Row([
                        dbc.Col([
                            html.Small([
                                html.I(className="fas fa-clock me-1"),
                                "Never used"
                            ], className="text-muted")
                        ], width=6),
                        dbc.Col([
                            html.Small([
                                html.I(className="fas fa-chart-line me-1"),
                                "Real-time"
                            ], className="text-success")
                        ], width=6, className="text-end")
                    ])
                ], className="mt-2")
            ])
        ], 
        className="module-card h-100 shadow-sm",
        style={
            "backgroundColor": THEME_CONFIG["paper_color"],
            "border": f"1px solid {THEME_CONFIG['accent_color']}",
            "transition": "all 0.3s ease",
            "borderRadius": "8px"
        })
        
        module_cards.append(
            dbc.Col(card, width=12, md=6, lg=4, xl=3, className="mb-4")
        )
    
    return dbc.Row(module_cards, className="g-4")

def create_header():
    """Create application header"""
    return dbc.Navbar([
        dbc.Row([
            dbc.Col([
                html.Img(src="/assets/logo.png", height="40px", className="me-2"),
                dbc.NavbarBrand("SchwaOptions Analytics", className="ms-2")
            ], width="auto"),
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button("Dashboard", id="nav-dashboard-btn", color="outline-light", size="sm", className="me-2"),
                    dbc.Button("Settings", id="nav-settings-btn", color="outline-light", size="sm")
                ])
            ], width="auto", className="ms-auto")
        ], align="center", className="g-0 w-100")
    ], 
    color="dark", 
    dark=True, 
    className="mb-4",
    style={"backgroundColor": THEME_CONFIG["background_color"]})

def create_ticker_input():
    """Create enhanced ticker symbol input section"""
    return dbc.Card([
        dbc.CardHeader([
            html.Div([
                html.I(className="fas fa-search me-2"),
                html.Span("Symbol Search", className="fw-bold")
            ])
        ], className="py-2"),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.InputGroup([
                        dbc.InputGroupText([
                            html.I(className="fas fa-chart-line")
                        ]),
                        dbc.Input(
                            id="ticker-input",
                            placeholder="Enter ticker symbol (e.g., SPY, AAPL, TSLA)",
                            value="SPY",
                            type="text",
                            className="ticker-input",
                            debounce=True
                        )
                    ], className="mb-2")
                ], width=8),
                dbc.Col([
                    dbc.Button(
                        [html.I(className="fas fa-sync me-1"), "Update"], 
                        id="update-ticker-btn", 
                        color="success",
                        className="w-100 update-btn"
                    )
                ], width=4)
            ]),
            html.Hr(className="my-2"),
            # Quick access popular tickers
            html.Div([
                html.Small("Popular: ", className="text-muted me-2"),
                dbc.ButtonGroup([
                    dbc.Button("SPY", id={"type": "quick-ticker", "ticker": "SPY"}, 
                             color="outline-primary", size="sm"),
                    dbc.Button("QQQ", id={"type": "quick-ticker", "ticker": "QQQ"}, 
                             color="outline-primary", size="sm"),
                    dbc.Button("AAPL", id={"type": "quick-ticker", "ticker": "AAPL"}, 
                             color="outline-primary", size="sm"),
                    dbc.Button("NVDA", id={"type": "quick-ticker", "ticker": "NVDA"}, 
                             color="outline-primary", size="sm"),
                    dbc.Button("TSLA", id={"type": "quick-ticker", "ticker": "TSLA"}, 
                             color="outline-primary", size="sm")
                ], size="sm")
            ], className="mb-2"),
            html.Div(id="ticker-info", className="small")
        ])
    ], 
    className="mb-4 ticker-input-card",
    style={"backgroundColor": THEME_CONFIG["paper_color"]})

def create_status_bar():
    """Create enhanced status bar for connection/data updates"""
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.I(className="fas fa-key me-2", id="auth-status-icon", style={"color": "#ff6b6b"}),
                        html.Span("Auth: ", className="me-1 small"),
                        dbc.Badge([
                            html.Span("●", className="me-1"),
                            "Not Connected"
                        ], color="danger", id="auth-status-badge", className="terminal-badge"),
                        dbc.Button([
                            html.I(className="fas fa-sign-in-alt me-1"),
                            "Login"
                        ],
                        id="auth-login-btn",
                        color="outline-primary",
                        size="sm",
                        className="ms-2",
                        style={"display": "none"})
                    ])
                ], width="auto"),
                dbc.Col([
                    html.Div([
                        html.I(className="fas fa-wifi me-2", style={"color": "#5fb85f"}),
                        html.Span("API: ", className="me-1 small"),
                        dbc.Badge([
                            html.Span("●", className="me-1"),
                            "Ready"
                        ], color="success", id="api-status", className="terminal-badge")
                    ])
                ], width="auto"),
                dbc.Col([
                    html.Div([
                        html.I(className="fas fa-clock me-2", style={"color": "#8be9fd"}),
                        html.Span("Updated: ", className="me-1 small"),
                        html.Span("Just now", id="last-update", className="text-info small")
                    ])
                ], width="auto"),
                dbc.Col([
                    html.Div([
                        html.I(className="fas fa-database me-2", style={"color": "#ff79c6"}),
                        html.Span("Records: ", className="me-1 small"),
                        html.Span("0", id="data-count", className="text-warning small")
                    ])
                ], width="auto"),
                dbc.Col([
                    html.Div([
                        html.I(className="fas fa-chart-line me-2", style={"color": "#bd93f9"}),
                        html.Span("Active: ", className="me-1 small"),
                        html.Span("SPY", id="current-symbol", className="text-primary small fw-bold")
                    ])
                ], width="auto", className="ms-auto")
            ], align="center", className="g-2")
        ], className="py-2")
    ], 
    className="status-bar mb-3",
    style={
        "backgroundColor": THEME_CONFIG["paper_color"],
        "border": f"1px solid {THEME_CONFIG['accent_color']}"
    })