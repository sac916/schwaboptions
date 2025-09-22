"""
Main Dash application - ConvexValue-inspired Schwab Options Dashboard
"""
import dash
from dash import html, dcc, callback, Input, Output, State, clientside_callback, ALL
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from datetime import datetime
import json
import pandas as pd

from config import THEME_CONFIG, APP_HOST, APP_PORT, DEBUG_MODE, DEFAULT_TICKERS, MODULES
from components.navigation import create_module_grid, create_header, create_ticker_input, create_status_bar
from data.schwab_client import schwab_client
from data.enhanced_schwab_client import enhanced_schwab_client
from data.module_data_adapter import ModuleDataAdapter
from components.auth_modal import create_auth_modal, create_auth_success_alert, create_auth_error_alert, create_auth_url_display
from components.data_quality import create_data_quality_alert, create_data_mode_buttons, create_module_data_controls
from data.processors import OptionsProcessor
from modules.options_chain import options_chain_module, create_enhanced_data_table, create_options_charts
from modules.iv_surface import iv_surface_module
from modules.options_heatmap import options_heatmap_module
from modules.flow_scanner import flow_scanner_module
from modules.strike_analysis import strike_analysis_module
from modules.intraday_charts import intraday_charts_module
from modules.dealer_surfaces import dealer_surfaces_module
from modules.ridgeline import ridgeline_module

# Initialize Dash app
app = dash.Dash(
    __name__, 
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap",
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
    ],
    suppress_callback_exceptions=True,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}]
)

app.title = "SchwaOptions Analytics - ConvexValue Style Dashboard"

# Main layout
def create_main_layout():
    """Create the main dashboard layout"""
    return html.Div([
        # Store components for data sharing
        dcc.Store(id="options-data-store"),
        dcc.Store(id="current-ticker-store", data="SPY"),
        dcc.Store(id="api-status-store", data={"connected": False, "last_update": None}),
        dcc.Store(id="auth-status-store", data={"authenticated": False}),

        # Auth modal
        create_auth_modal(),

        # Auth check interval
        dcc.Interval(
            id="auth-check-interval",
            interval=30*1000,  # Check every 30 seconds
            n_intervals=0
        ),

        # Alert container for auth messages
        html.Div(id="auth-alerts-container", className="position-fixed",
                style={"top": "20px", "right": "20px", "zIndex": "9999", "width": "400px"}),
        
        # Hidden components required by existing callbacks
        dbc.Button(id="fetch-options-btn", style={"display": "none"}),
        dbc.Button(id="show-unusual-btn", style={"display": "none"}),
        dbc.Button(id="show-charts-btn", style={"display": "none"}),
        dbc.Button(id="back-to-table-btn", style={"display": "none"}),
        dbc.Input(id="min-volume-input", type="number", value=0, style={"display": "none"}),
        html.Div(id="options-content", style={"display": "none"}),
        html.Div(id="data-status", style={"display": "none"}),

        
        # Interval components for real-time updates
        dcc.Interval(
            id="data-update-interval",
            interval=10000,  # 10 seconds
            n_intervals=0,
            disabled=True
        ),
        
        # CSS and scripts
        html.Link(rel="stylesheet", href="/assets/main.css"),
        html.Link(rel="stylesheet", href="/assets/performance.css"),
        html.Script("""
            // Fix Plotly canvas warnings
            window.PlotlyConfig = {plotlyServerURL: ""};
            window.addEventListener('load', function() {
                const canvases = document.querySelectorAll('canvas');
                canvases.forEach(canvas => {
                    canvas.setAttribute('willReadFrequently', true);
                });
            });
        """),
        
        # Header with inline navigation to ensure proper callback connection
        dbc.Navbar([
            dbc.Row([
                dbc.Col([
                    html.Img(src="/assets/logo.png", height="40px", className="me-2"),
                    dbc.NavbarBrand("SchwaOptions Analytics", className="ms-2")
                ], width="auto"),
                dbc.Col([
                    dbc.Button("🏠 Dashboard", id="dashboard-btn-simple", color="outline-light", size="sm", className="me-2"),
                    dbc.Button("⚙️ Settings", id="nav-settings-btn", color="outline-light", size="sm")
                ], width="auto", className="ms-auto")
            ], align="center", className="g-0 w-100")
        ], 
        color="dark", 
        dark=True, 
        className="mb-4",
        style={"backgroundColor": THEME_CONFIG["background_color"]}),
        
        # Main container
        dbc.Container([
            # Status bar
            create_status_bar(),
            
            # Ticker input section
            create_ticker_input(),
            
            # Main content area  
            html.Div(id="main-content", children=[
                # Welcome screen with module grid
                html.Div([
                    html.H2("Welcome to SchwaOptions Analytics", 
                           className="text-center mb-4", 
                           style={"color": THEME_CONFIG["primary_color"]}),
                    html.P("Select a module to begin analyzing options data:", 
                           className="text-center mb-5 text-muted"),
                    create_module_grid()
                ], id="welcome-screen")
            ])
        ], fluid=True)
    ], style={"backgroundColor": THEME_CONFIG["background_color"], "minHeight": "100vh"})

app.layout = create_main_layout

# Clientside callback for component cleanup
clientside_callback(
    """
    function(children) {
        // Clean up any existing timeouts/intervals on component change
        if (window.dashTimeouts) {
            window.dashTimeouts.forEach(id => clearTimeout(id));
            window.dashTimeouts = [];
        }
        if (window.dashIntervals) {
            window.dashIntervals.forEach(id => clearInterval(id));
            window.dashIntervals = [];
        }
        
        // Override setTimeout to track timeouts
        if (!window.originalSetTimeout) {
            window.originalSetTimeout = window.setTimeout;
            window.dashTimeouts = window.dashTimeouts || [];
            window.setTimeout = function(callback, delay) {
                const id = window.originalSetTimeout(callback, delay);
                window.dashTimeouts.push(id);
                return id;
            };
        }
        
        return window.dash_clientside.no_update;
    }
    """,
    Output("main-content", "style"),
    Input("main-content", "children"),
    prevent_initial_call=True
)

# Callback for ticker update
@callback(
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
    
    # Test API connection with visual feedback
    if schwab_client.authenticate():
        status = {"connected": True, "last_update": datetime.now().strftime("%H:%M:%S")}
        info = html.Div([
            html.I(className="fas fa-check-circle text-success me-2"),
            f"Ready to analyze {ticker} options data - Data will auto-refresh when switching modules"
        ])
    else:
        status = {"connected": False, "last_update": None}
        info = html.Div([
            html.I(className="fas fa-exclamation-triangle text-danger me-2"),
            "API connection failed - check credentials in .env file"
        ])
    
    return ticker, info, status

# Callback for API status display
@callback(
    [Output("api-status", "children"),
     Output("api-status", "color"),
     Output("last-update", "children"),
     Output("data-count", "children")],
    Input("api-status-store", "data"),
    Input("options-data-store", "data")
)
def update_status_bar(api_status, options_data):
    """Update status bar information"""
    
    # API status
    if api_status and api_status.get("connected"):
        status_text = "Connected"
        status_color = "success"
        last_update = api_status.get("last_update", "Never")
    else:
        status_text = "Disconnected"
        status_color = "danger"
        last_update = "Never"
    
    # Data count
    data_count = 0
    if options_data:
        try:
            import pandas as pd
            df = pd.read_json(options_data, orient='records')
            data_count = len(df)
        except:
            pass
    
    return status_text, status_color, last_update, f"{data_count:,}"

# Simple navigation callback (Phase 1 fix - no pattern matching)
@callback(
    Output("main-content", "children"),
    [
        Input("dashboard-btn-simple", "n_clicks"),
        Input("options_chain-btn", "n_clicks"),
        Input("iv_surface-btn", "n_clicks"),
        Input("options_heatmap-btn", "n_clicks"),
        Input("flow_scanner-btn", "n_clicks"),
        Input("strike_analysis-btn", "n_clicks"),
        Input("intraday_charts-btn", "n_clicks"),
        Input("dealer_surfaces-btn", "n_clicks"),
        Input("ridgeline-btn", "n_clicks"),
        Input("skew_analysis-btn", "n_clicks"),
        Input("implied_prob-btn", "n_clicks"),
        Input("earnings_cal-btn", "n_clicks"),
        Input("econ_cal-btn", "n_clicks")
    ],
    State("current-ticker-store", "data"),
    prevent_initial_call=True
)
def navigate_app(dashboard_clicks, options_chain_clicks, iv_surface_clicks,
                options_heatmap_clicks, flow_scanner_clicks, strike_analysis_clicks,
                intraday_charts_clicks, dealer_surfaces_clicks, ridgeline_clicks,
                skew_analysis_clicks, implied_prob_clicks, earnings_cal_clicks,
                econ_cal_clicks, ticker):
    """Simple navigation without pattern matching"""

    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if not ticker:
        ticker = "SPY"

    # Dashboard
    if button_id == "dashboard-btn-simple":
        return create_dashboard_content()

    # Working modules
    elif button_id == "options_chain-btn":
        return create_options_chain_module(ticker)
    elif button_id == "iv_surface-btn":
        return iv_surface_module.create_layout(ticker)
    elif button_id == "options_heatmap-btn":
        return options_heatmap_module.create_layout(ticker)
    elif button_id == "flow_scanner-btn":
        return flow_scanner_module.create_layout(ticker)
    elif button_id == "strike_analysis-btn":
        return strike_analysis_module.create_layout(ticker)
    elif button_id == "intraday_charts-btn":
        return intraday_charts_module.create_layout(ticker)
    elif button_id == "dealer_surfaces-btn":
        return dealer_surfaces_module.create_layout(ticker)
    elif button_id == "ridgeline-btn":
        return ridgeline_module.create_layout(ticker)

    # Placeholder modules
    elif button_id == "skew_analysis-btn":
        module_info = next((m for m in MODULES if m["id"] == "skew_analysis"), None)
        return create_module_placeholder(module_info, ticker)
    elif button_id == "implied_prob-btn":
        module_info = next((m for m in MODULES if m["id"] == "implied_prob"), None)
        return create_module_placeholder(module_info, ticker)
    elif button_id == "earnings_cal-btn":
        module_info = next((m for m in MODULES if m["id"] == "earnings_cal"), None)
        return create_module_placeholder(module_info, ticker)
    elif button_id == "econ_cal-btn":
        module_info = next((m for m in MODULES if m["id"] == "econ_cal"), None)
        return create_module_placeholder(module_info, ticker)

    return dash.no_update

def create_module_placeholder(module_info, ticker):
    """Create placeholder for future modules"""
    
    # Determine progress based on phase
    phase_progress = {
        "dealer_flow": ("Phase 3", 10, "Advanced 3D Analytics"),
        "ridgeline": ("Phase 3", 15, "Advanced Visualizations"), 
        "skew_analysis": ("Phase 3", 20, "Advanced Analytics"),
        "implied_prob": ("Phase 3", 25, "Advanced Analytics"),
        "earnings_cal": ("Phase 4", 5, "External Integrations"),
        "econ_cal": ("Phase 4", 5, "External Integrations")
    }
    
    phase_info = phase_progress.get(module_info["id"], ("Future", 0, "Development"))
    phase, progress, category = phase_info
    
    return dbc.Card([
        dbc.CardHeader([
            html.H4(f"{module_info['name']} - {ticker}", className="mb-0"),
            dbc.Button("← Back to Dashboard", 
                      id={"type": "back-button", "module": "error"}, 
                      color="outline-secondary", 
                      size="sm")
        ]),
        dbc.CardBody([
            html.H5(f"🔮 {module_info['name']} Module"),
            html.P(f"This module will implement: {module_info['description']}"),
            dbc.Badge(f"{phase} - {category}", color="info", className="mb-3"),
            html.P(f"Scheduled for {phase} development.", className="text-muted"),
            dbc.Progress(
                value=progress, 
                label=f"{progress}% Planned", 
                className="mt-3",
                color="info" if progress > 0 else "secondary"
            ),
            html.Hr(),
            html.Small([
                html.Strong("Phase 2 Complete! "), 
                "6 working modules now available. Phase 3 focuses on advanced 3D analytics."
            ], className="text-success")
        ])
    ], style={"backgroundColor": THEME_CONFIG["paper_color"]})

def create_options_chain_module(ticker):
    """Create enhanced options chain module (first working module)"""
    return options_chain_module.create_layout(ticker)

# Options Chain Callbacks - Now enabled with placeholder components
@callback(
    [Output("options-content", "children"),
     Output("data-status", "children"),
     Output("options-data-store", "data")],
    [Input("fetch-options-btn", "n_clicks"),
     Input("current-ticker-store", "data")],
    State("min-volume-input", "value"),
    prevent_initial_call=True
)
def fetch_options_data(n_clicks, ticker, min_volume):
    """Fetch and display options data"""
    # Check if we're actually in the right context (button exists)
    try:
        ctx = dash.callback_context
        print(f"🔍 Context triggered: {ctx.triggered}")
        if not ctx.triggered:
            return dash.no_update, dash.no_update, dash.no_update
    except:
        return dash.no_update, dash.no_update, dash.no_update
    
    # Trigger on either button click or ticker change
    if not ticker:
        return html.Div("No ticker selected"), "❌ No ticker", None
    
    # Fetch data from Schwab API with parameters to avoid overflow
    try:
        raw_data = schwab_client.get_option_chain(
            symbol=ticker,
            contractType="ALL",           # Get both calls and puts
            strikeCount=40,               # More strikes for better surface
            includeUnderlyingQuote=True,  # Include underlying stock data
            range="ALL",                  # All options (ITM, ATM, OTM) for full surface
            daysToExpiration=120          # 4 months for better time dimension
        )
        if not raw_data:
            return (
                html.Div("Failed to fetch data - check API connection", className="text-danger"),
                "❌ API Error",
                None
            )

        # Process data
        try:
            print("About to call OptionsProcessor.parse_option_chain")
            df = OptionsProcessor.parse_option_chain(raw_data)
            print(f"OptionsProcessor returned df with {len(df)} rows")
        except Exception as proc_error:
            import traceback
            print(f"Error in OptionsProcessor: {proc_error}")
            print(f"Processor traceback: {traceback.format_exc()}")
            raise
        if df.empty:
            return (
                html.Div("No options data available for this ticker", className="text-warning"),
                "⚠️ No Data",
                None
            )
        
        # Apply volume filter
        if min_volume and min_volume > 0:
            df = df[df.get('Volume', 0) >= min_volume]
        
        # Create data table
        data_table = create_enhanced_data_table(df)
        
        # Create summary stats
        total_contracts = len(df)
        total_volume = df.get('Volume', pd.Series([0])).sum()
        avg_iv = df.get('IV', pd.Series([0])).mean()
        unusual_count = len(df[df.get('UnusualScore', 0) > 50]) if 'UnusualScore' in df.columns else 0
        
        summary_card = dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.H6("Total Contracts"),
                        html.H4(f"{total_contracts:,}", className="text-primary")
                    ], md=3),
                    dbc.Col([
                        html.H6("Total Volume"),
                        html.H4(f"{int(total_volume):,}", className="text-success")
                    ], md=3),
                    dbc.Col([
                        html.H6("Avg IV"),
                        html.H4(f"{avg_iv:.1%}", className="text-info")
                    ], md=3),
                    dbc.Col([
                        html.H6("Unusual Activity"),
                        html.H4(f"{unusual_count}", className="text-warning")
                    ], md=3)
                ])
            ])
        ], className="mb-4")
        
        content = html.Div([
            summary_card,
            data_table
        ])
        
        status = f"✅ {total_contracts:,} contracts loaded"
        
        # Store processed data
        stored_data = df.to_json(orient='records')
        
        return content, status, stored_data
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Full error traceback: {error_details}")
        return (
            html.Div(f"Error processing data: {str(e)}", className="text-danger"),
            "❌ Processing Error", 
            None
        )

@callback(
    Output("options-content", "children", allow_duplicate=True),
    Input("show-unusual-btn", "n_clicks"),
    State("options-data-store", "data"),
    prevent_initial_call=True
)
def show_unusual_activity(n_clicks, stored_data):
    """Filter and show only unusual activity"""
    if not n_clicks or not stored_data:
        return dash.no_update
    
    try:
        df = pd.read_json(stored_data, orient='records')
        unusual_df = OptionsProcessor.detect_unusual_flow(df, threshold=50)
        
        if unusual_df.empty:
            return dbc.Alert("No unusual activity detected with current criteria.", color="info")
        
        data_table = create_enhanced_data_table(unusual_df)
        
        return html.Div([
            dbc.Alert(f"Showing {len(unusual_df)} contracts with unusual activity (Score ≥ 50)", 
                     color="warning", className="mb-3"),
            data_table
        ])
        
    except Exception as e:
        return dbc.Alert(f"Error filtering data: {str(e)}", color="danger")

@callback(
    Output("options-content", "children", allow_duplicate=True),
    Input("show-charts-btn", "n_clicks"),
    [State("options-data-store", "data"),
     State("current-ticker-store", "data")],
    prevent_initial_call=True
)
def show_options_charts(n_clicks, stored_data, ticker):
    """Show options visualization charts"""
    if not n_clicks or not stored_data:
        return dash.no_update
    
    try:
        df = pd.read_json(stored_data, orient='records')
        charts = create_options_charts(df, ticker)
        
        return html.Div([
            dbc.Button("← Back to Table", id="back-to-table-btn", color="outline-primary", size="sm", className="mb-3"),
            charts
        ])
        
    except Exception as e:
        return dbc.Alert(f"Error creating charts: {str(e)}", color="danger")

@callback(
    Output("options-content", "children", allow_duplicate=True),
    Input("back-to-table-btn", "n_clicks"),
    State("options-data-store", "data"),
    prevent_initial_call=True
)
def back_to_table(n_clicks, stored_data):
    """Return to data table view"""
    if not n_clicks or not stored_data:
        return dash.no_update
    
    try:
        df = pd.read_json(stored_data, orient='records')
        data_table = create_enhanced_data_table(df)
        return data_table
    except:
        return html.Div("Error loading table")

def create_dashboard_content():
    """Create the dashboard content (DRY principle)"""
    return html.Div([
        html.H2("Welcome to SchwaOptions Analytics", 
               className="text-center mb-4", 
               style={"color": THEME_CONFIG["primary_color"]}),
        html.P("Select a module to begin analyzing options data:", 
               className="text-center mb-5 text-muted"),
        create_module_grid()
    ])

## Test button callback
#@callback(
#    Output("main-content", "children"),
#    Input("test-btn", "n_clicks"),
#    prevent_initial_call=True
#)
#def test_button_click(n_clicks):
#    """Test if any callback works"""
#    print(f"🚨 TEST BUTTON CLICKED: n_clicks={n_clicks}")
#    if n_clicks and n_clicks > 0:
#        return html.Div([
#            html.H1("🚨 TEST BUTTON WORKS!", style={"color": "red", "text-align": "center"}),
#            html.P("Callbacks are functioning properly"),
#            create_module_grid()
#        ])
#    return dash.no_update
#
## Removed duplicate callback - now handled by single navigate_to_dashboard callback above
#
# ==================== DEALER SURFACES MODULE CALLBACKS ====================

@callback(
    [Output("dealer-content", "children"),
     Output("dealer-status", "children")],
    Input("fetch-dealer-btn", "n_clicks"),
    State("current-ticker-store", "data"),
    prevent_initial_call=True
)
def update_dealer_data(n_clicks, ticker):
    """Update dealer surfaces data"""
    if not n_clicks:
        return dash.no_update
    
    if not ticker:
        ticker = "SPY"
    
    try:
        # Update dealer module data
        data = dealer_surfaces_module.update_data(ticker)
        
        if data is None or data.empty:
            return (
                dbc.Alert("No dealer data available. Check API connection.", color="warning"),
                "❌ No Data"
            )
        
        # Create default view (delta surface)
        visualizations = dealer_surfaces_module.create_visualizations()
        
        summary_metrics = html.Div([
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.H6("📊 Dealer Positioning", className="mb-2"),
                            html.P([
                                html.Strong("Total Delta Exposure: "),
                                f"{data['Dealer_Delta_Exposure'].sum():.2f}"
                            ], className="mb-1 small"),
                            html.P([
                                html.Strong("Total Gamma Exposure: "),
                                f"{data['Dealer_Gamma_Exposure'].sum():.4f}"
                            ], className="mb-1 small"),
                            html.P([
                                html.Strong("Avg Hedging Pressure: "),
                                f"{data['Hedging_Pressure'].mean():.3f}"
                            ], className="mb-0 small")
                        ], md=4),
                        dbc.Col([
                            html.H6("🎯 Key Levels", className="mb-2"),
                            html.P([
                                html.Strong("Current Spot: "),
                                f"${dealer_surfaces_module.current_spot:.0f}" if dealer_surfaces_module.current_spot else "N/A"
                            ], className="mb-1 small"),
                            html.P([
                                html.Strong("Max Gamma Strike: "),
                                f"${data.loc[data['Dealer_Gamma_Exposure'].abs().idxmax(), 'Strike']:.0f}" if len(data) > 0 else "N/A"
                            ], className="mb-1 small"),
                            html.P([
                                html.Strong("Total Volume: "),
                                f"{data['Volume'].sum():,.0f}"
                            ], className="mb-0 small")
                        ], md=4),
                        dbc.Col([
                            html.H6("⚡ Market Impact", className="mb-2"),
                            html.P([
                                html.Strong("High Pressure Strikes: "),
                                f"{len(data[data['Hedging_Pressure'] > data['Hedging_Pressure'].quantile(0.8)])}"
                            ], className="mb-1 small"),
                            html.P([
                                html.Strong("Data Points: "),
                                f"{len(data)}"
                            ], className="mb-1 small"),
                            html.P([
                                html.Strong("Last Updated: "),
                                datetime.now().strftime("%H:%M:%S")
                            ], className="mb-0 small")
                        ], md=4)
                    ])
                ])
            ], className="mb-4", style={"backgroundColor": THEME_CONFIG["paper_color"]})
        ])
        
        # Default to delta surface view
        content = html.Div([
            summary_metrics,
            visualizations.get("dealer_delta_surface", html.Div("No delta surface available"))
        ])
        
        return content, f"✅ Loaded {len(data)} contracts"
        
    except Exception as e:
        error_msg = f"Error updating dealer data: {str(e)}"
        print(error_msg)
        return (
            dbc.Alert(error_msg, color="danger"),
            "❌ Error"
        )

@callback(
    Output("dealer-content", "children", allow_duplicate=True),
    Input("show-delta-surf-btn", "n_clicks"),
    prevent_initial_call=True
)
def show_delta_surface(n_clicks):
    """Show dealer delta surface"""
    if not n_clicks:
        return dash.no_update
    
    visualizations = dealer_surfaces_module.create_visualizations()
    return visualizations.get("dealer_delta_surface", html.Div("No delta surface available"))

@callback(
    Output("dealer-content", "children", allow_duplicate=True),
    Input("show-gamma-surf-btn", "n_clicks"),
    prevent_initial_call=True
)
def show_gamma_surface(n_clicks):
    """Show dealer gamma surface"""
    if not n_clicks:
        return dash.no_update
    
    visualizations = dealer_surfaces_module.create_visualizations()
    return visualizations.get("dealer_gamma_surface", html.Div("No gamma surface available"))

@callback(
    Output("dealer-content", "children", allow_duplicate=True),
    Input("show-hedge-btn", "n_clicks"),
    prevent_initial_call=True
)
def show_hedging_pressure(n_clicks):
    """Show hedging pressure analysis"""
    if not n_clicks:
        return dash.no_update
    
    visualizations = dealer_surfaces_module.create_visualizations()
    return visualizations.get("hedging_pressure", html.Div("No hedging pressure data available"))

@callback(
    Output("dealer-content", "children", allow_duplicate=True),
    Input("show-flow-btn", "n_clicks"),
    prevent_initial_call=True
)
def show_dealer_flow(n_clicks):
    """Show dealer flow analysis"""
    if not n_clicks:
        return dash.no_update
    
    visualizations = dealer_surfaces_module.create_visualizations()
    return visualizations.get("dealer_flow", html.Div("No dealer flow data available"))

# IV Surface Module Callbacks
@callback(
    [Output("iv-summary", "children"),
     Output("iv-status", "children")],
    Input("fetch-iv-btn", "n_clicks"),
    State("current-ticker-store", "data"),
    prevent_initial_call=True
)
def update_iv_data(n_clicks, ticker):
    """Update IV surface data"""
    if not n_clicks or not ticker:
        return dash.no_update, dash.no_update
    
    print(f"🔍 IV Update: Fetching data for {ticker}")
    
    # Update data with universal adapter (auto mode by default)
    data = iv_surface_module.update_data(ticker, mode="auto")
    
    if data is not None and not data.empty:
        # Create summary metrics
        summary_cards = []
        
        # Calculate basic metrics
        total_contracts = len(data)
        avg_iv = data['IV'].mean() if 'IV' in data.columns else 0
        volume_total = data['Volume'].sum() if 'Volume' in data.columns else 0
        
        summary_cards.extend([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Total Contracts", className="text-muted"),
                        html.H4(f"{total_contracts:,}")
                    ])
                ])
            ], md=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Average IV", className="text-muted"),
                        html.H4(f"{avg_iv:.1%}")
                    ])
                ])
            ], md=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Total Volume", className="text-muted"),
                        html.H4(f"{volume_total:,.0f}")
                    ])
                ])
            ], md=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Status", className="text-muted"),
                        html.H4("Ready", className="text-success")
                    ])
                ])
            ], md=3)
        ])
        
        summary = dbc.Row(summary_cards, className="mb-4")
        status = html.Span(f"✅ Updated {total_contracts} contracts for {ticker}", className="text-success")
        
        return summary, status
    else:
        return html.Div("No data available"), html.Span("❌ Failed to fetch data", className="text-danger")

@callback(
    Output("iv-content", "children", allow_duplicate=True),
    Input("show-terms-btn", "n_clicks"),
    prevent_initial_call=True
)
def show_term_structure(n_clicks):
    """Show IV term structure chart"""
    if not n_clicks:
        return dash.no_update
    
    visualizations = iv_surface_module.create_visualizations()
    return visualizations.get("term_structure", html.Div("No term structure data available"))

@callback(
    Output("iv-content", "children", allow_duplicate=True),
    Input("show-3d-btn", "n_clicks"),
    prevent_initial_call=True
)
def show_iv_surface(n_clicks):
    """Show 3D IV surface"""
    if not n_clicks:
        return dash.no_update
    
    visualizations = iv_surface_module.create_visualizations()
    return visualizations.get("iv_surface", html.Div("No 3D surface data available"))

@callback(
    Output("iv-content", "children", allow_duplicate=True),
    Input("show-hist-btn", "n_clicks"),
    prevent_initial_call=True
)
def show_iv_historical(n_clicks):
    """Show historical IV watermarks"""
    if not n_clicks:
        return dash.no_update
    
    visualizations = iv_surface_module.create_visualizations()
    return visualizations.get("historical_iv", html.Div("No historical IV data available"))

@callback(
    Output("iv-content", "children", allow_duplicate=True),
    Input("show-skew-btn", "n_clicks"),
    prevent_initial_call=True
)
def show_iv_skew(n_clicks):
    """Show volatility skew analysis"""
    if not n_clicks:
        return dash.no_update
    
    visualizations = iv_surface_module.create_visualizations()
    return visualizations.get("skew_analysis", html.Div("No skew analysis data available"))

# Options Heatmap Module Callbacks
@callback(
    [Output("heatmap-summary", "children"),
     Output("heatmap-status", "children")],
    Input("fetch-heatmap-btn", "n_clicks"),
    State("current-ticker-store", "data"),
    prevent_initial_call=True
)
def update_heatmap_data(n_clicks, ticker):
    """Update heatmap data"""
    if not n_clicks or not ticker:
        return dash.no_update, dash.no_update
    
    print(f"🔍 Heatmap Update: Fetching data for {ticker}")
    
    # Update data with universal adapter (auto mode by default)
    data = options_heatmap_module.update_data(ticker, mode="auto")
    
    if data is not None and not data.empty:
        # Create summary metrics
        total_contracts = len(data)
        total_volume = data['Volume'].sum() if 'Volume' in data.columns else 0
        avg_iv = data['IV'].mean() if 'IV' in data.columns else 0
        
        summary_cards = [
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Total Contracts", className="text-muted"),
                        html.H4(f"{total_contracts:,}")
                    ])
                ])
            ], md=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Total Volume", className="text-muted"),
                        html.H4(f"{total_volume:,.0f}")
                    ])
                ])
            ], md=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Average IV", className="text-muted"),
                        html.H4(f"{avg_iv:.1%}")
                    ])
                ])
            ], md=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Status", className="text-muted"),
                        html.H4("Ready", className="text-success")
                    ])
                ])
            ], md=3)
        ]
        
        summary = dbc.Row(summary_cards, className="mb-4")
        status = html.Span(f"✅ Updated heatmap with {total_contracts} contracts for {ticker}", className="text-success")
        
        return summary, status
    else:
        return html.Div("No data available"), html.Span("❌ Failed to fetch heatmap data", className="text-danger")

@callback(
    Output("heatmap-content", "children", allow_duplicate=True),
    Input("show-volume-heat-btn", "n_clicks"),
    prevent_initial_call=True
)
def show_volume_heatmap(n_clicks):
    """Show volume heatmap"""
    if not n_clicks:
        return dash.no_update
    
    visualizations = options_heatmap_module.create_visualizations()
    return visualizations.get("volume_heatmap", html.Div("No volume heatmap data available"))

@callback(
    Output("heatmap-content", "children", allow_duplicate=True),
    Input("show-iv-heat-btn", "n_clicks"),
    prevent_initial_call=True
)
def show_iv_heatmap(n_clicks):
    """Show IV heatmap"""
    if not n_clicks:
        return dash.no_update
    
    visualizations = options_heatmap_module.create_visualizations()
    return visualizations.get("iv_heatmap", html.Div("No IV heatmap data available"))

@callback(
    Output("heatmap-content", "children", allow_duplicate=True),
    Input("show-unusual-heat-btn", "n_clicks"),
    prevent_initial_call=True
)
def show_unusual_heatmap(n_clicks):
    """Show unusual activity heatmap"""
    if not n_clicks:
        return dash.no_update
    
    visualizations = options_heatmap_module.create_visualizations()
    return visualizations.get("unusual_heatmap", html.Div("No unusual activity heatmap data available"))

@callback(
    Output("heatmap-content", "children", allow_duplicate=True),
    Input("show-flow-heat-btn", "n_clicks"),
    prevent_initial_call=True
)
def show_flow_heatmap(n_clicks):
    """Show flow direction heatmap"""
    if not n_clicks:
        return dash.no_update
    
    visualizations = options_heatmap_module.create_visualizations()
    return visualizations.get("flow_heatmap", html.Div("No flow heatmap data available"))

# Flow Scanner Module Callbacks
@callback(
    [Output("flow-alerts", "children"),
     Output("flow-status", "children")],
    Input("scan-flow-btn", "n_clicks"),
    State("current-ticker-store", "data"),
    prevent_initial_call=True
)
def update_flow_data(n_clicks, ticker):
    """Update flow scanner data"""
    if not n_clicks or not ticker:
        return dash.no_update, dash.no_update
    
    print(f"🔍 Flow Scanner: Analyzing flow for {ticker}")
    
    # Update data with universal adapter (auto mode by default)
    data = flow_scanner_module.update_data(ticker, mode="auto")
    
    if data is not None and not data.empty:
        # Create alert cards for unusual activity
        visualizations = flow_scanner_module.create_visualizations()
        alerts_html = visualizations.get("unusual_alerts", html.Div("No alerts available"))

        status = html.Span(f"✅ Scanned {len(data)} contracts", className="text-success")

        return alerts_html, status
    else:
        return html.Div([dbc.Alert("No flow data available", color="warning")]), html.Span("❌ Failed to scan flow", className="text-danger")

@callback(
    Output("flow-content", "children", allow_duplicate=True),
    Input("show-flow-table-btn", "n_clicks"),
    prevent_initial_call=True
)
def show_flow_table(n_clicks):
    """Show flow analysis table"""
    if not n_clicks:
        return dash.no_update
    
    visualizations = flow_scanner_module.create_visualizations()
    return visualizations.get("flow_table", html.Div("No flow table data available"))

@callback(
    Output("flow-content", "children", allow_duplicate=True),
    Input("show-flow-chart-btn", "n_clicks"),
    prevent_initial_call=True
)
def show_flow_chart(n_clicks):
    """Show flow visualization chart"""
    if not n_clicks:
        return dash.no_update
    
    visualizations = flow_scanner_module.create_visualizations()
    return visualizations.get("flow_chart", html.Div("No flow chart data available"))

@callback(
    Output("flow-content", "children", allow_duplicate=True),
    Input("show-params-btn", "n_clicks"),
    prevent_initial_call=True
)
def show_flow_parameters(n_clicks):
    """Show flow analysis parameters"""
    if not n_clicks:
        return dash.no_update
    
    visualizations = flow_scanner_module.create_visualizations()
    return visualizations.get("parameter_analysis", html.Div("No parameters analysis available"))

@callback(
    Output("flow-content", "children", allow_duplicate=True),
    Input("show-alerts-btn", "n_clicks"),
    prevent_initial_call=True
)
def show_flow_alerts(n_clicks):
    """Show detailed flow alerts"""
    if not n_clicks:
        return dash.no_update
    
    visualizations = flow_scanner_module.create_visualizations()
    return visualizations.get("unusual_alerts", html.Div("No alert details available"))

@callback(
    Output("dealer-content", "children", allow_duplicate=True),
    Input("show-hist-btn", "n_clicks"),
    prevent_initial_call=True
)
def show_dealer_history(n_clicks):
    """Show dealer positioning history"""
    if not n_clicks:
        return dash.no_update
    
    visualizations = dealer_surfaces_module.create_visualizations()
    return visualizations.get("positioning_history", html.Div("No historical data available"))

@callback(
    Output("dealer-content", "children", allow_duplicate=True),
    Input("show-combined-surf-btn", "n_clicks"),
    prevent_initial_call=True
)
def show_combined_surface(n_clicks):
    """Show combined 3D dealer surface"""
    if not n_clicks:
        return dash.no_update

    visualizations = dealer_surfaces_module.create_visualizations()
    return visualizations.get("combined_surface", html.Div("No combined surface data available"))

@callback(
    Output("dealer-content", "children", allow_duplicate=True),
    Input("show-risk-scenarios-btn", "n_clicks"),
    prevent_initial_call=True
)
def show_risk_scenarios(n_clicks):
    """Show dealer risk scenario analysis"""
    if not n_clicks:
        return dash.no_update

    visualizations = dealer_surfaces_module.create_visualizations()
    return visualizations.get("risk_scenarios", html.Div("No risk scenario data available"))

@callback(
    Output("dealer-content", "children", allow_duplicate=True),
    Input("show-interactive-surf-btn", "n_clicks"),
    prevent_initial_call=True
)
def show_interactive_surface(n_clicks):
    """Show interactive 3D dealer surface"""
    if not n_clicks:
        return dash.no_update

    visualizations = dealer_surfaces_module.create_visualizations()
    return visualizations.get("interactive_surface", html.Div("No interactive surface data available"))

# ============================================================================
# RIDGELINE MODULE CALLBACKS
# ============================================================================

@callback(
    [Output("ridgeline-total-volume", "children"),
     Output("ridgeline-total-oi", "children"),
     Output("ridgeline-expirations", "children"),
     Output("ridgeline-spot-price", "children"),
     Output("ridgeline-status", "children")],
    Input("fetch-ridgeline-btn", "n_clicks"),
    State("current-ticker-store", "data"),
    prevent_initial_call=True
)
def update_ridgeline_data(n_clicks, ticker):
    """Update ridgeline data"""
    if not n_clicks or not ticker:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    print(f"🔍 Ridgeline Update: Fetching data for {ticker}")

    try:
        data = ridgeline_module.update_data(ticker)
        if data is not None and not data.empty:
            # Calculate summary metrics
            total_volume = f"{data['Volume'].sum():,.0f}"
            total_oi = f"{data['Open_Interest'].sum():,.0f}"
            active_exps = f"{data['Expiry'].nunique()}"
            spot_price = f"${ridgeline_module.current_spot:.2f}" if ridgeline_module.current_spot else "N/A"
            status = f"✅ Updated: {len(data)} contracts across {data['Expiry'].nunique()} expirations"

            return total_volume, total_oi, active_exps, spot_price, status
        else:
            return "0", "0", "0", "N/A", "❌ No data available"
    except Exception as e:
        print(f"Error updating ridgeline data: {e}")
        return "Error", "Error", "Error", "Error", f"❌ Error: {str(e)}"

@callback(
    Output("ridgeline-content", "children", allow_duplicate=True),
    Input("show-volume-ridge-btn", "n_clicks"),
    prevent_initial_call=True
)
def show_volume_ridge(n_clicks):
    """Show volume distribution ridgeline"""
    if not n_clicks:
        return dash.no_update

    visualizations = ridgeline_module.create_visualizations()
    if "volume_ridge" in visualizations:
        return dcc.Graph(figure=visualizations["volume_ridge"], style={"height": "600px"})
    return html.Div("No volume ridgeline data available")

@callback(
    Output("ridgeline-content", "children", allow_duplicate=True),
    Input("show-oi-ridge-btn", "n_clicks"),
    prevent_initial_call=True
)
def show_oi_ridge(n_clicks):
    """Show open interest ridgeline"""
    if not n_clicks:
        return dash.no_update

    visualizations = ridgeline_module.create_visualizations()
    if "oi_ridge" in visualizations:
        return dcc.Graph(figure=visualizations["oi_ridge"], style={"height": "600px"})
    return html.Div("No OI ridgeline data available")

@callback(
    Output("ridgeline-content", "children", allow_duplicate=True),
    Input("show-combined-ridge-btn", "n_clicks"),
    prevent_initial_call=True
)
def show_combined_ridge(n_clicks):
    """Show combined ridgeline visualization"""
    if not n_clicks:
        return dash.no_update

    visualizations = ridgeline_module.create_visualizations()
    if "combined_ridge" in visualizations:
        return dcc.Graph(figure=visualizations["combined_ridge"], style={"height": "800px"})
    return html.Div("No combined ridgeline data available")

# ============================================================================
# INTEGRATED AUTHENTICATION CALLBACKS
# ============================================================================

@callback(
    [Output("auth-status-store", "data"),
     Output("auth-status-badge", "children"),
     Output("auth-status-badge", "color"),
     Output("auth-status-icon", "style"),
     Output("auth-login-btn", "style")],
    [Input("auth-check-interval", "n_intervals")]
)
def update_auth_status(n_intervals):
    """Update authentication status display"""
    try:
        status = enhanced_schwab_client.get_auth_status()

        if status["authenticated"]:
            badge_children = [html.Span("●", className="me-1"), "Connected"]
            badge_color = "success"
            icon_style = {"color": "#5fb85f"}
            login_btn_style = {"display": "none"}

        elif status["needs_refresh"]:
            badge_children = [html.Span("●", className="me-1"), "Expires Soon"]
            badge_color = "warning"
            icon_style = {"color": "#ffc107"}
            login_btn_style = {"display": "inline-block"}

        else:
            badge_children = [html.Span("●", className="me-1"), "Not Connected"]
            badge_color = "danger"
            icon_style = {"color": "#ff6b6b"}
            login_btn_style = {"display": "inline-block"}

        return status, badge_children, badge_color, icon_style, login_btn_style

    except Exception as e:
        return {
            "authenticated": False,
            "error": str(e)
        }, [html.Span("●", className="me-1"), "Error"], "danger", {"color": "#ff6b6b"}, {"display": "inline-block"}

@callback(
    Output("auth-modal", "is_open"),
    [Input("auth-login-btn", "n_clicks"),
     Input("auth-modal-close", "n_clicks")],
    [State("auth-modal", "is_open")]
)
def toggle_auth_modal(login_clicks, close_clicks, is_open):
    """Toggle the authentication modal"""
    ctx = dash.callback_context
    if not ctx.triggered:
        return is_open

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if trigger_id == "auth-login-btn" and login_clicks:
        return True
    elif trigger_id == "auth-modal-close" and close_clicks:
        return False

    return is_open

@callback(
    Output("auth-url-container", "children"),
    [Input("generate-auth-url-btn", "n_clicks")]
)
def generate_auth_url(n_clicks):
    """Generate and display authorization URL"""
    if not n_clicks:
        return html.Div()

    try:
        auth_url = enhanced_schwab_client.get_authorization_url()
        if auth_url:
            return create_auth_url_display(auth_url)
        else:
            return dbc.Alert("Failed to generate authorization URL. Check your API credentials.",
                           color="danger")
    except Exception as e:
        return dbc.Alert(f"Error generating auth URL: {str(e)}", color="danger")

@callback(
    Output("process-callback-btn", "disabled"),
    [Input("callback-url-input", "value")]
)
def toggle_process_button(callback_url):
    """Enable process button when valid callback URL is entered"""
    if not callback_url:
        return True
    return not callback_url.startswith("https://127.0.0.1/?code=")

@callback(
    [Output("auth-alerts-container", "children"),
     Output("auth-processing", "style"),
     Output("callback-url-input", "value"),
     Output("auth-modal", "is_open", allow_duplicate=True)],
    [Input("process-callback-btn", "n_clicks")],
    [State("callback-url-input", "value")],
    prevent_initial_call=True
)
def process_callback_url(n_clicks, callback_url):
    """Process the callback URL and authenticate"""
    if not n_clicks or not callback_url:
        return dash.no_update, {"display": "none"}, dash.no_update, dash.no_update

    try:
        result = enhanced_schwab_client.process_callback_url(callback_url)

        if result["success"]:
            alert = create_auth_success_alert()
            return alert, {"display": "none"}, "", False  # Close modal on success
        else:
            alert = create_auth_error_alert(result["message"])
            return alert, {"display": "none"}, callback_url, dash.no_update

    except Exception as e:
        alert = create_auth_error_alert(f"Unexpected error: {str(e)}")
        return alert, {"display": "none"}, callback_url, dash.no_update

# Universal Data Quality and Mode Selection Callbacks
@callback(
    [Output({"type": "module-data-info", "module": ALL}, "children"),
     Output({"type": "module-content", "module": ALL}, "children")],
    [Input({"type": "live-btn", "module": ALL}, "n_clicks"),
     Input({"type": "historical-btn", "module": ALL}, "n_clicks"),
     Input({"type": "auto-btn", "module": ALL}, "n_clicks"),
     Input({"type": "refresh-btn", "module": ALL}, "n_clicks")],
    [State("current-ticker-store", "data"),
     State({"type": "module-data-info", "module": ALL}, "id")],
    prevent_initial_call=True
)
def update_universal_module_data(live_clicks, hist_clicks, auto_clicks, refresh_clicks,
                                ticker, module_ids):
    """Universal callback for data mode selection and refresh across all modules"""
    ctx = dash.callback_context
    if not ctx.triggered or not ticker:
        return [dash.no_update] * len(module_ids), [dash.no_update] * len(module_ids)

    # Determine which button was clicked and which module
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    button_data = eval(button_id) if isinstance(button_id, str) and button_id.startswith("{") else {}

    if not button_data or 'module' not in button_data:
        return [dash.no_update] * len(module_ids), [dash.no_update] * len(module_ids)

    target_module = button_data['module']
    button_type = button_data['type']

    # Determine mode from button type
    mode_map = {
        "live-btn": "live",
        "historical-btn": "historical",
        "auto-btn": "auto",
        "refresh-btn": "auto"  # Refresh uses current/auto mode
    }
    mode = mode_map.get(button_type, "auto")

    # Update only the target module
    data_infos = []
    contents = []

    for module_id in module_ids:
        module_name = module_id['module']

        if module_name == target_module:
            try:
                # Get the appropriate module instance
                module_map = {
                    'flow_scanner': flow_scanner_module,
                    'iv_surface': iv_surface_module,
                    'options_heatmap': options_heatmap_module,
                    'strike_analysis': strike_analysis_module,
                    'options_chain': options_chain_module,
                    'intraday_charts': intraday_charts_module,
                    'dealer_surfaces': dealer_surfaces_module,
                    'ridgeline': ridgeline_module
                }

                module = module_map.get(module_name)
                if module:
                    # Update module data with selected mode
                    data = module.update_data(ticker, mode=mode)

                    # Get data quality info
                    quality_info = module.get_data_quality_info()
                    if quality_info:
                        data_info = create_data_quality_alert(quality_info['info'])
                        data_infos.append(data_info)
                    else:
                        data_infos.append(dash.no_update)

                    # Create refreshed content (module-specific implementation needed)
                    contents.append(html.Div(f"Updated {module_name} with {mode} mode"))
                else:
                    data_infos.append(dash.no_update)
                    contents.append(dash.no_update)
            except Exception as e:
                error_alert = html.Div(f"Error updating {module_name}: {str(e)}",
                                     className="alert alert-danger")
                data_infos.append(error_alert)
                contents.append(dash.no_update)
        else:
            data_infos.append(dash.no_update)
            contents.append(dash.no_update)

    return data_infos, contents

# Enhanced Data Status Callback for Individual Modules
@callback(
    Output("data-status", "children", allow_duplicate=True),
    [Input("current-ticker-store", "data")],
    prevent_initial_call=True
)
def update_enhanced_data_status(ticker):
    """Update data status with quality information when ticker changes"""
    if not ticker:
        return "No ticker selected"

    # Show universal data system status
    try:
        data_adapter = ModuleDataAdapter()
        return html.Div([
            dbc.Alert([
                html.I(className="fas fa-magic me-2"),
                html.Strong("Universal Data System Active"),
                html.Br(),
                f"Ready to provide always-available analysis for {ticker}",
                html.Br(),
                html.Small("Intelligent routing: Live → Historical → Enriched", className="text-muted")
            ], color="info", className="mb-2"),

            html.Small([
                html.I(className="fas fa-info-circle me-1"),
                "All modules now support Live/Historical/Auto data modes"
            ], className="text-muted")
        ])
    except Exception as e:
        return dbc.Alert(f"Universal data system error: {str(e)}", color="warning")

# Dynamic Module Header Updates
@callback(
    Output("options-chain-header", "children"),
    Input("current-ticker-store", "data"),
    prevent_initial_call=True
)
def update_options_chain_header(ticker):
    """Update options chain header when ticker changes"""
    if ticker:
        return f"📊 Enhanced Options Chain - {ticker}"
    return "📊 Enhanced Options Chain"

@callback(
    Output("ridgeline-header", "children"),
    Input("current-ticker-store", "data"),
    prevent_initial_call=True
)
def update_ridgeline_header(ticker):
    """Update ridgeline header when ticker changes"""
    if ticker:
        return f"📊 Ridgeline Analysis - {ticker}"
    return "📊 Ridgeline Analysis"

@callback(
    Output("strike-analysis-header", "children"),
    Input("current-ticker-store", "data"),
    prevent_initial_call=True
)
def update_strike_analysis_header(ticker):
    """Update strike analysis header when ticker changes"""
    if ticker:
        return f"📊 Strike Analysis - {ticker}"
    return "📊 Strike Analysis"

if __name__ == "__main__":
    app.run_server(host=APP_HOST, port=APP_PORT, debug=DEBUG_MODE)