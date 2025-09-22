"""
Enhanced Options Chain Module - First working ConvexValue-style module
"""
import pandas as pd
from datetime import datetime
from dash import html, dcc, dash_table, callback, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from modules.base_module import BaseModule
from data.module_data_adapter import ModuleDataAdapter
from data.processors import OptionsProcessor
from config import THEME_CONFIG

class OptionsChainModule(BaseModule):
    """Enhanced Options Chain with ConvexValue-style features"""
    
    def __init__(self):
        super().__init__(
            module_id="options_chain",
            name="Options Chain",
            description="Enhanced options chain with unusual activity detection"
        )
        self.data_adapter = ModuleDataAdapter()
    
    def update_data(self, ticker: str, mode: str = "auto", target_date = None, **kwargs):
        """Update options data for ticker using universal data adapter"""
        try:
            # Get data through universal adapter
            data_result = self.data_adapter.get_options_analysis(
                symbol=ticker,
                analysis_type="options_chain",
                force_mode=mode,
                target_date=target_date
            )

            if data_result and data_result.get('options_data') is not None:
                self.data = data_result['options_data']
                self.data_quality = data_result.get('data_quality')
                self.data_info = data_result.get('data_info', {})
                self._last_updated = datetime.now()
                return self.data
        except Exception as e:
            print(f"Error updating data: {e}")
        return None

    def get_data_quality_info(self):
        """Get current data quality information for UI display"""
        if hasattr(self, 'data_quality') and hasattr(self, 'data_info'):
            return {
                'quality': self.data_quality,
                'info': self.data_info
            }
        return None
    
    def create_visualizations(self):
        """Create module visualizations"""
        if self.data is None or self.data.empty:
            return {}
        
        return {
            "data_table": create_enhanced_data_table(self.data),
            "charts": create_options_charts(self.data, "ticker")
        }
        
    def create_layout(self, ticker: str) -> html.Div:
        """Create enhanced options chain layout"""
        return html.Div([
            # Header
            dbc.Row([
                dbc.Col([
                    dbc.Button("← Dashboard", id={"type": "back-button", "module": "options_chain"}, color="outline-primary", size="sm")
                ], width="auto"),
                dbc.Col([
                    html.H3(f"📊 Enhanced Options Chain - {ticker}",
                           id="options-chain-header",
                           style={"color": THEME_CONFIG["primary_color"]})
                ])
            ], align="center", className="mb-4"),
            
            # Controls
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Button("🔄 Fetch Data", 
                                      id="fetch-options-btn", 
                                      color="primary", 
                                      size="lg")
                        ], width="auto"),
                        dbc.Col([
                            dbc.Button("🔍 Show Unusual Only", 
                                      id="show-unusual-btn", 
                                      color="warning",
                                      outline=True,
                                      size="sm")
                        ], width="auto"),
                        dbc.Col([
                            dbc.Button("📊 View Charts", 
                                      id="show-charts-btn", 
                                      color="info",
                                      outline=True,
                                      size="sm")
                        ], width="auto"),
                        dbc.Col([
                            dbc.InputGroup([
                                dbc.InputGroupText("Min Volume"),
                                dbc.Input(id="min-volume-input", 
                                         type="number", 
                                         value=0, 
                                         min=0,
                                         size="sm")
                            ], size="sm")
                        ], width="auto"),
                        dbc.Col([
                            html.Div(id="data-status", className="text-muted small")
                        ], className="ms-auto text-end")
                    ], align="center")
                ])
            ], className="mb-4"),
            
            # Main content with loading spinner
            dcc.Loading(
                id="loading-options-data",
                type="default",
                children=html.Div(id="options-content", children=[
                    self._create_welcome_message(ticker)
                ])
            )
        ])
    
    def _create_welcome_message(self, ticker: str) -> html.Div:
        """Create welcome message before data is loaded"""
        return dbc.Card([
            dbc.CardBody([
                html.H4(f"Ready to analyze {ticker} options", className="text-center"),
                html.P("Click 'Fetch Data' to load the options chain with enhanced analytics", 
                       className="text-center text-muted"),
                html.Hr(),
                dbc.Row([
                    dbc.Col([
                        html.H6("✨ Enhanced Features:"),
                        html.Ul([
                            html.Li("Unusual Activity Detection"),
                            html.Li("Volume/OI Analysis"),
                            html.Li("Flow Direction Indicators"),
                            html.Li("Real-time Calculations")
                        ])
                    ], md=6),
                    dbc.Col([
                        html.H6("📈 Available Views:"),
                        html.Ul([
                            html.Li("Sortable Data Table"),
                            html.Li("Volume Heatmap"),
                            html.Li("IV Surface Plot"),
                            html.Li("Strike Distribution")
                        ])
                    ], md=6)
                ])
            ])
        ], style={"backgroundColor": THEME_CONFIG["paper_color"]})

def create_enhanced_data_table(df: pd.DataFrame) -> dash_table.DataTable:
    """Create enhanced data table with ConvexValue styling"""
    
    # Define conditional formatting
    style_data_conditional = [
        # Unusual activity highlighting
        {
            'if': {'filter_query': '{UnusualScore} > 75'},
            'backgroundColor': 'rgba(255, 107, 107, 0.3)',
            'color': 'white',
        },
        {
            'if': {'filter_query': '{UnusualScore} > 50'},
            'backgroundColor': 'rgba(255, 193, 7, 0.3)',
            'color': 'white',
        },
        # High volume highlighting
        {
            'if': {'filter_query': '{Volume} > 1000'},
            'backgroundColor': 'rgba(0, 212, 170, 0.2)',
            'color': 'white',
        },
        # ITM options
        {
            'if': {'filter_query': '{OptionType} = ITM'},
            'backgroundColor': 'rgba(77, 171, 247, 0.2)',
            'color': 'white',
        }
    ]
    
    # Format columns
    columns = []
    for col in df.columns:
        col_config = {"name": col, "id": col}
        
        # Format numeric columns
        if col in ["Mark", "Strike", "IV", "Delta", "Gamma", "Theta", "Vega", "Bid-Ask"]:
            col_config["type"] = "numeric"
            col_config["format"] = {"specifier": ".3f"}
        elif col in ["Volume", "Open Int", "Premium"]:
            col_config["type"] = "numeric"
            col_config["format"] = {"specifier": ",.0f"}
        elif col in ["UnusualScore", "DTE"]:
            col_config["type"] = "numeric"
            col_config["format"] = {"specifier": ".0f"}
            
        columns.append(col_config)
    
    return dash_table.DataTable(
        id="options-table",
        columns=columns,
        data=df.to_dict("records"),
        style_table={
            'overflowX': 'auto',
            'backgroundColor': THEME_CONFIG["paper_color"]
        },
        style_header={
            'backgroundColor': THEME_CONFIG["accent_color"],
            'color': 'white',
            'fontWeight': 'bold',
            'textAlign': 'center'
        },
        style_cell={
            'backgroundColor': THEME_CONFIG["paper_color"],
            'color': THEME_CONFIG["text_color"],
            'textAlign': 'center',
            'padding': '8px',
            'border': f'1px solid {THEME_CONFIG["accent_color"]}'
        },
        style_data_conditional=style_data_conditional,
        sort_action="native",
        filter_action="native",
        page_action="native",
        page_current=0,
        page_size=25,
        export_format="csv"
    )

def create_options_charts(df: pd.DataFrame, ticker: str):
    """Create enhanced visualizations for options data"""
    
    if df.empty:
        return html.Div("No data available for charts")
    
    # Create subplots - larger layout with proper 3D scene
    fig = make_subplots(
        rows=1, cols=2,  # Changed to 1x2 for larger charts
        subplot_titles=['Volume by Strike & Price', 'IV Surface (Strike × Time × Volatility)'],
        specs=[[{"secondary_y": True}, {"type": "scene"}]],
        column_widths=[0.5, 0.5]
    )
    
    # Chart 1: Volume by Strike
    calls_df = df[df['Type'] == 'CALL'] if 'Type' in df.columns else df
    puts_df = df[df['Type'] == 'PUT'] if 'Type' in df.columns else pd.DataFrame()
    
    if not calls_df.empty:
        fig.add_trace(
            go.Bar(
                x=calls_df['Strike'], 
                y=calls_df['Volume'], 
                name='Call Volume', 
                marker_color=THEME_CONFIG["primary_color"],
                hovertemplate='<b>Call Options</b><br>' +
                              'Strike: $%{x}<br>' +
                              'Volume: %{y:,}<br>' +
                              '<extra></extra>'
            ),
            row=1, col=1
        )
    
    if not puts_df.empty:
        fig.add_trace(
            go.Bar(
                x=puts_df['Strike'], 
                y=puts_df['Volume'], 
                name='Put Volume', 
                marker_color=THEME_CONFIG["secondary_color"],
                hovertemplate='<b>Put Options</b><br>' +
                              'Strike: $%{x}<br>' +
                              'Volume: %{y:,}<br>' +
                              '<extra></extra>'
            ),
            row=1, col=1
        )
    
    # Add underlying price line on secondary y-axis
    underlying_price = df.get('underlying_price', [df['Strike'].mean()])[0] if 'underlying_price' in df.columns else df['Strike'].mean()
    fig.add_trace(
        go.Scatter(
            x=[df['Strike'].min(), df['Strike'].max()],
            y=[underlying_price, underlying_price],
            mode='lines',
            name=f'{ticker} Stock Price',
            line=dict(color='white', width=3, dash='dash'),
            hovertemplate=f'<b>{ticker} Current Price</b><br>' +
                          'Price: $%{y}<br>' +
                          '<extra></extra>'
        ),
        secondary_y=True, row=1, col=1
    )
    
    # Chart 2: 3D IV Surface (Strike x Time x IV)
    if 'IV' in df.columns and 'Strike' in df.columns and 'DTE' in df.columns:
        # Create IV surface data - use calls only for cleaner surface
        calls_df = df[df['Type'] == 'CALL'] if 'Type' in df.columns else df
        
        if not calls_df.empty:
            # Create pivot table with interpolation for smoother surface
            surface_data = calls_df.pivot_table(
                values='IV', 
                index='DTE',     # Y-axis: Time to expiration
                columns='Strike', # X-axis: Strike prices
                aggfunc='mean'
            )
            
            # Fill NaN values with interpolation for smoother surface
            surface_data = surface_data.interpolate(method='linear', axis=1)
            surface_data = surface_data.interpolate(method='linear', axis=0)
            
            if not surface_data.empty and surface_data.shape[0] > 1 and surface_data.shape[1] > 1:
                fig.add_trace(
                    go.Surface(
                        z=surface_data.values,
                        x=surface_data.columns,  # Strikes
                        y=surface_data.index,    # DTE
                        colorscale='RdYlBu_r',   # Red-Yellow-Blue reversed (high IV = red)
                        name='Call IV Surface',
                        showscale=True,
                        colorbar=dict(
                            title="Implied<br>Volatility (%)",
                            titleside="right",
                            x=1.02
                        ),
                        hovertemplate='<b>Options Volatility</b><br>' +
                                      'Strike: $%{x}<br>' +
                                      'Days to Exp: %{y}<br>' +
                                      'Implied Vol: %{z:.1%}<br>' +
                                      '<extra></extra>'
                    ),
                    row=1, col=2
                )
            else:
                # Fallback to scatter plot if not enough data for surface
                fig.add_trace(
                    go.Scatter3d(
                        x=calls_df['Strike'],
                        y=calls_df['DTE'], 
                        z=calls_df['IV'],
                        mode='markers',
                        marker=dict(
                            size=calls_df['Volume']/50,
                            color=calls_df['IV'],
                            colorscale='RdYlBu_r',
                            showscale=True,
                            colorbar=dict(
                                title="Implied<br>Volatility (%)",
                                titleside="right"
                            )
                        ),
                        name='Call IV Points',
                        hovertemplate='<b>Call Option</b><br>' +
                                      'Strike: $%{x}<br>' +
                                      'Days to Exp: %{y}<br>' +
                                      'Implied Vol: %{z:.1%}<br>' +
                                      'Volume: %{marker.size*50:,.0f}<br>' +
                                      '<extra></extra>'
                    ),
                    row=1, col=2
                )
    
    # Update axis labels and layout
    fig.update_xaxes(
        title_text="Strike Price ($)", 
        showgrid=True,
        row=1, col=1
    )
    fig.update_yaxes(
        title_text="Volume (Contracts)", 
        showgrid=True,
        row=1, col=1
    )
    fig.update_yaxes(
        title_text=f"{ticker} Stock Price ($)", 
        secondary_y=True,
        row=1, col=1
    )
    
    # Update 3D scene layout for the IV surface
    fig.update_scenes(
        xaxis_title="Strike Price ($)",
        yaxis_title="Days to Expiration",
        zaxis_title="Implied Volatility (%)",
        row=1, col=2
    )
    
    # Update layout for larger, more professional charts
    fig.update_layout(
        height=900,  # Increased height
        title_text=f"{ticker} Professional Options Analysis",
        plot_bgcolor=THEME_CONFIG["paper_color"],
        paper_bgcolor=THEME_CONFIG["background_color"],
        font=dict(color=THEME_CONFIG["text_color"], size=12),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return dcc.Graph(
        figure=fig, 
        style={"height": "900px"},
        config={
            "displayModeBar": True,
            "displaylogo": False,
            "modeBarButtonsToRemove": ["pan2d", "lasso2d"],
            "toImageButtonOptions": {
                "format": "png",
                "filename": f"{ticker}_options_analysis",
                "height": 900,
                "width": 1200,
                "scale": 1
            }
        }
    )

# Global options chain module instance
options_chain_module = OptionsChainModule()