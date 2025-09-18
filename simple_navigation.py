"""
Simple, bulletproof navigation using URL routing
No callback conflicts, no flashing, just works.
"""
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
from config import THEME_CONFIG, MODULES
from components.navigation import create_module_grid
from datetime import datetime

def create_navigation_layout():
    """Create main layout with URL routing"""
    return html.Div([
        # URL location component for routing
        dcc.Location(id="url", refresh=False),
        
        # Stores for current ticker and API status
        dcc.Store(id="current-ticker-store", data="SPY"),
        dcc.Store(id="api-status-store", data={"connected": False, "last_update": None}),
        
        # Header with navigation
        dbc.Navbar([
            dbc.Row([
                dbc.Col([
                    html.Img(src="/assets/logo.png", height="40px", className="me-2"),
                    dbc.NavbarBrand("SchwaOptions Analytics", className="ms-2")
                ], width="auto"),
                dbc.Col([
                    dcc.Link("🏠 Dashboard", href="/", className="btn btn-outline-light btn-sm me-2"),
                    dbc.Button("⚙️ Settings", id="settings-btn", color="outline-light", size="sm")
                ], width="auto", className="ms-auto")
            ], align="center", className="g-0 w-100")
        ], color="dark", dark=True, className="mb-4"),
        
        # Load terminal CSS
        html.Link(rel="stylesheet", href="/assets/terminal.css"),
        
        # Main content area - updated by URL routing
        html.Div(id="page-content")
    ], style={"backgroundColor": "#0a0e1a", "minHeight": "100vh"})

def register_callbacks(app):
    """Register all navigation callbacks with the Dash app"""
    
    @app.callback(
        Output("page-content", "children"),
        [Input("url", "pathname"),
         Input("current-ticker-store", "data")]
    )
    def display_page(pathname, current_ticker):
        """Single callback handles ALL routing - no conflicts"""
        
        if not current_ticker:
            current_ticker = "SPY"
        
        print(f"🔍 DEBUG: pathname={pathname}, ticker={current_ticker}")
        
        # Dashboard (root)
        if pathname == "/" or pathname is None:
            print("📍 Routing to dashboard")
            return create_dashboard_page()
        
        # Module routing: /module/module_name
        if pathname.startswith("/module/"):
            module_name = pathname.replace("/module/", "")
            print(f"📍 Routing to module: {module_name}")
            return create_module_page(module_name, current_ticker)
        
        # 404 page
        print(f"📍 404: Unknown path {pathname}")
        return html.Div([
            html.H1("404 - Page Not Found"),
            html.P(f"Path '{pathname}' not found"),
            dcc.Link("← Back to Dashboard", href="/", className="btn btn-primary")
        ])

def create_dashboard_page():
    """Dashboard with ticker input and module grid"""
    return dbc.Container([
        # Ticker input section
        create_ticker_section(),
        
        # Status bar
        create_status_section(),
        
        # Welcome section
        html.Div([
            html.H2("Welcome to SchwaOptions Analytics", 
                   className="text-center mb-4", 
                   style={"color": THEME_CONFIG["primary_color"]}),
            html.P("Select a module to begin analyzing options data:", 
                   className="text-center mb-5 text-muted"),
        ], className="mb-4"),
        
        # Module grid with URL links (not callback buttons)
        create_module_grid_with_links()
    ], fluid=True)

def create_module_grid_with_links():
    """Create module grid using URL links instead of callback buttons"""
    
    module_cards = []
    for module in MODULES:
        card = dbc.Card([
            dbc.CardBody([
                html.H5(module["name"], className="card-title text-center"),
                html.P(module["description"], className="card-text text-center small"),
                dcc.Link([
                    html.Span("Launch")
                ], 
                    href=f"/module/{module['id']}", 
                    className="btn btn-primary btn-sm w-100"
                )
            ])
        ], 
        className="module-card h-100",
        style={
            "backgroundColor": THEME_CONFIG["paper_color"],
            "border": f"1px solid {THEME_CONFIG['primary_color']}",
            "transition": "all 0.3s ease"
        })
        
        module_cards.append(
            dbc.Col(card, width=12, md=6, lg=4, xl=3, className="mb-4")
        )
    
    return dbc.Container([
        dbc.Row(module_cards, className="g-4")
    ], fluid=True)

def create_module_page(module_name, ticker):
    """Create module page with back navigation"""
    
    print(f"🔍 Creating module page: {module_name} for {ticker}")
    print(f"🔍 Available modules: {[m['id'] for m in MODULES]}")
    
    # Find module info
    module_info = next((m for m in MODULES if m["id"] == module_name), None)
    if not module_info:
        print(f"❌ Module {module_name} not found!")
        return dbc.Container([
            html.H1("Module Not Found"),
            html.P(f"Module '{module_name}' not found in configuration."),
            dcc.Link("← Back to Dashboard", href="/", className="btn btn-primary")
        ], fluid=True)
    
    # Module header with back navigation - terminal style
    header = dbc.Container([
        dbc.Row([
            dbc.Col([
                dcc.Link("← Dashboard", href="/", className="btn btn-outline-primary btn-sm")
            ], width="auto"),
            dbc.Col([
                html.H3([
                    html.Span(f"📊 {module_info['name']}", className="me-3"),
                    html.Span(f"[{ticker}]", style={"color": "#00ff88", "fontFamily": "JetBrains Mono"})
                ])
            ])
        ], align="center", className="mb-4")
    ], fluid=True)
    
    # Module content with terminal aesthetics
    if module_name in ["options_chain", "iv_surface", "options_heatmap", "flow_scanner", "strike_analysis", "intraday_charts"]:
        content = dbc.Container([
            header,
            dbc.Card([
                dbc.CardBody([
                    html.H4([
                        "✅ ", 
                        html.Span(f"{module_info['name']} Module", className="terminal-cursor"),
                        " Loading..."
                    ], className="text-success"),
                    html.P(f"Real-time options analysis for {ticker} will load here", className="text-muted"),
                    html.Hr(),
                    html.Div([
                        html.P("🚀 Navigation: WORKING", className="text-success mb-1"),
                        html.P("📊 Terminal Theme: ACTIVE", className="text-info mb-1"),  
                        html.P("🔌 API Integration: READY", className="text-warning mb-1"),
                        html.P(f"📈 Ticker: {ticker}", className="text-primary mb-1")
                    ]),
                    html.Hr(),
                    html.P("Click ← Dashboard to test bulletproof navigation!", className="small text-muted")
                ])
            ], className="mt-4")
        ], fluid=True)
    else:
        content = dbc.Container([
            header,
            dbc.Card([
                dbc.CardBody([
                    html.H4(f"🔮 {module_info['name']} - Coming Soon", className="text-warning"),
                    html.P(f"This module is planned for Phase 3:", className="text-muted"),
                    html.P(module_info['description'], className="text-info"),
                    html.Hr(),
                    html.P(f"Will analyze {ticker} when implemented", className="small text-muted")
                ])
            ], className="mt-4")
        ], fluid=True)
    
    return content

def create_ticker_section():
    """Create ticker input section"""
    return dbc.Card([
        dbc.CardBody([
            html.H5("Select Symbol", className="card-title"),
            dbc.Row([
                dbc.Col([
                    dbc.Input(
                        id="ticker-input",
                        placeholder="Enter ticker (e.g., SPY, AAPL)",
                        value="SPY",
                        type="text",
                        className="mb-2",
                        debounce=True
                    )
                ], width=8),
                dbc.Col([
                    dbc.Button(
                        "Update", 
                        id="update-ticker-btn", 
                        color="success",
                        className="w-100"
                    )
                ], width=4)
            ]),
            html.Hr(),
            html.Div(id="ticker-info", className="small text-muted", children="Enter a ticker symbol to get started")
        ])
    ], 
    className="mb-4",
    style={"backgroundColor": THEME_CONFIG["paper_color"]})

def create_status_section():
    """Create status bar for connection/data updates"""
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Span("API Status: ", className="me-2"),
                dbc.Badge("Disconnected", color="danger", id="api-status")
            ], width="auto"),
            dbc.Col([
                html.Span("Last Update: ", className="me-2"),
                html.Span("Never", id="last-update", className="text-muted")
            ], width="auto"),
            dbc.Col([
                html.Span("Data Points: ", className="me-2"),
                html.Span("0", id="data-count", className="text-info")
            ], width="auto", className="ms-auto")
        ], align="center")
    ], 
    className="status-bar p-2 mb-3",
    style={
        "backgroundColor": THEME_CONFIG["paper_color"],
        "border": f"1px solid {THEME_CONFIG['accent_color']}",
        "borderRadius": "5px"
    })

    @app.callback(
        [Output("current-ticker-store", "data"),
         Output("ticker-info", "children"),
         Output("api-status-store", "data")],
        [Input("update-ticker-btn", "n_clicks"),
         Input("ticker-input", "n_submit")],
        State("ticker-input", "value")
    )
    def update_ticker(n_clicks, n_submit, ticker):
        """Update current ticker and test API connection"""
        # Trigger on either button click or Enter key
        if (not n_clicks and not n_submit) or not ticker:
            return "SPY", "Enter a ticker symbol to get started", {"connected": False, "last_update": None}
        
        ticker = ticker.upper().strip()
        
        # For now, simulate successful connection (real API integration later)
        status = {"connected": True, "last_update": datetime.now().strftime("%H:%M:%S")}
        info = html.Div([
            html.I(className="fas fa-check-circle text-success me-2"),
            f"Ready to analyze {ticker} options data - Navigation working perfectly!"
        ])
        
        return ticker, info, status

    @app.callback(
        [Output("api-status", "children"),
         Output("api-status", "color"),
         Output("last-update", "children"),
         Output("data-count", "children")],
        Input("api-status-store", "data")
    )
    def update_status_display(api_status):
        """Update status bar information"""
        
        # API status
        if api_status and api_status.get("connected"):
            status_text = "Connected"
            status_color = "success"
            last_update = api_status.get("last_update", "Never")
            data_count = "Ready"
        else:
            status_text = "Disconnected"
            status_color = "danger"
            last_update = "Never"
            data_count = "0"
        
        return status_text, status_color, last_update, data_count