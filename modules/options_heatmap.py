"""
Options Heatmap Module - ConvexValue 'grid' module equivalent
Visual options chain heatmap with color-coded activity levels
"""
import pandas as pd
import numpy as np
from datetime import datetime
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from modules.base_module import BaseModule
from data.schwab_client import schwab_client
from data.processors import OptionsProcessor
from config import THEME_CONFIG

class OptionsHeatmapModule(BaseModule):
    """Options Chain Heatmap Visualization"""
    
    def __init__(self):
        super().__init__(
            module_id="options_heatmap",
            name="Options Heatmap",
            description="Visual options chain heatmap with activity levels"
        )
        
    def update_data(self, ticker: str, **kwargs):
        """Update options data for heatmap"""
        try:
            raw_data = schwab_client.get_option_chain(
                symbol=ticker,
                contractType="ALL",
                strikeCount=40,
                includeUnderlyingQuote=True,
                range="ALL",
                daysToExpiration=120
            )
            if raw_data:
                self.data = OptionsProcessor.parse_option_chain(raw_data)
                self._last_updated = datetime.now()
                return self.data
        except Exception as e:
            print(f"Error updating heatmap data: {e}")
        return None
    
    def create_visualizations(self):
        """Create heatmap visualizations"""
        if self.data is None or self.data.empty:
            return {}
            
        return {
            "volume_heatmap": self._create_volume_heatmap(),
            "iv_heatmap": self._create_iv_heatmap(),
            "unusual_heatmap": self._create_unusual_activity_heatmap(),
            "flow_heatmap": self._create_flow_direction_heatmap()
        }
    
    def _create_volume_heatmap(self):
        """Create volume-based heatmap"""
        # Prepare heatmap data
        heatmap_data = self._prepare_heatmap_data('Volume')
        
        if heatmap_data.empty:
            return html.Div("No data for volume heatmap")
        
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data.values,
            x=heatmap_data.columns,  # Expiration dates
            y=heatmap_data.index,    # Strike prices
            colorscale='Viridis',
            hoverongaps=False,
            colorbar=dict(title="Volume", titleside="right")
        ))
        
        # Add annotations for high-volume cells
        annotations = []
        for i, strike in enumerate(heatmap_data.index):
            for j, exp in enumerate(heatmap_data.columns):
                value = heatmap_data.iloc[i, j]
                if value > np.percentile(heatmap_data.values.flatten(), 80):  # Top 20%
                    annotations.append(
                        dict(x=j, y=i, text=f"{int(value):,}", 
                            showarrow=False, font=dict(color="white", size=10))
                    )
        
        fig.update_layout(
            title="Options Volume Heatmap",
            xaxis_title="Expiration Date",
            yaxis_title="Strike Price", 
            annotations=annotations,
            plot_bgcolor=THEME_CONFIG["paper_color"],
            paper_bgcolor=THEME_CONFIG["background_color"],
            font=dict(color=THEME_CONFIG["text_color"]),
            height=600
        )
        
        return dcc.Graph(figure=fig)
    
    def _create_iv_heatmap(self):
        """Create implied volatility heatmap"""
        heatmap_data = self._prepare_heatmap_data('IV')
        
        if heatmap_data.empty:
            return html.Div("No data for IV heatmap")
        
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data.values,
            x=heatmap_data.columns,
            y=heatmap_data.index,
            colorscale='RdYlBu_r',  # Red-Yellow-Blue reversed
            hoverongaps=False,
            colorbar=dict(title="Implied Vol", titleside="right")
        ))
        
        fig.update_layout(
            title="Implied Volatility Heatmap",
            xaxis_title="Expiration Date",
            yaxis_title="Strike Price",
            plot_bgcolor=THEME_CONFIG["paper_color"],
            paper_bgcolor=THEME_CONFIG["background_color"],
            font=dict(color=THEME_CONFIG["text_color"]),
            height=600
        )
        
        return dcc.Graph(figure=fig)
    
    def _create_unusual_activity_heatmap(self):
        """Create unusual activity heatmap"""
        heatmap_data = self._prepare_heatmap_data('UnusualScore')
        
        if heatmap_data.empty:
            return html.Div("No unusual activity data")
        
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data.values,
            x=heatmap_data.columns,
            y=heatmap_data.index,
            colorscale=[[0, '#1f1f1f'], [0.5, '#ff6b6b'], [1, '#ff0000']],  # Dark to red
            hoverongaps=False,
            colorbar=dict(title="Unusual Score", titleside="right")
        ))
        
        # Highlight unusual activity > 50
        annotations = []
        for i, strike in enumerate(heatmap_data.index):
            for j, exp in enumerate(heatmap_data.columns):
                value = heatmap_data.iloc[i, j]
                if value > 50:
                    annotations.append(
                        dict(x=j, y=i, text="🚨", 
                            showarrow=False, font=dict(size=16))
                    )
        
        fig.update_layout(
            title="Unusual Activity Heatmap",
            xaxis_title="Expiration Date",
            yaxis_title="Strike Price",
            annotations=annotations,
            plot_bgcolor=THEME_CONFIG["paper_color"],
            paper_bgcolor=THEME_CONFIG["background_color"],
            font=dict(color=THEME_CONFIG["text_color"]),
            height=600
        )
        
        return dcc.Graph(figure=fig)
    
    def _create_flow_direction_heatmap(self):
        """Create flow direction heatmap"""
        # Create numeric flow values
        flow_data = self.data.copy()
        flow_mapping = {'Bullish': 1, 'Neutral': 0, 'Bearish': -1}
        
        if 'FlowDirection' in flow_data.columns:
            flow_data['FlowValue'] = flow_data['FlowDirection'].map(flow_mapping).fillna(0)
        else:
            flow_data['FlowValue'] = 0
        
        heatmap_data = self._prepare_heatmap_data('FlowValue', flow_data)
        
        if heatmap_data.empty:
            return html.Div("No flow direction data")
        
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data.values,
            x=heatmap_data.columns,
            y=heatmap_data.index,
            colorscale=[[0, '#ff6b6b'], [0.5, '#1f1f1f'], [1, '#00d4aa']],  # Red-Black-Green
            zmid=0,  # Center the colorscale at 0
            hoverongaps=False,
            colorbar=dict(title="Flow Direction", titleside="right",
                         tickvals=[-1, 0, 1], ticktext=["Bearish", "Neutral", "Bullish"])
        ))
        
        fig.update_layout(
            title="Options Flow Direction Heatmap",
            xaxis_title="Expiration Date",
            yaxis_title="Strike Price",
            plot_bgcolor=THEME_CONFIG["paper_color"],
            paper_bgcolor=THEME_CONFIG["background_color"],
            font=dict(color=THEME_CONFIG["text_color"]),
            height=600
        )
        
        return dcc.Graph(figure=fig)
    
    def _prepare_heatmap_data(self, value_column, data=None):
        """Prepare data for heatmap visualization"""
        if data is None:
            data = self.data
            
        if data.empty or value_column not in data.columns:
            return pd.DataFrame()
        
        # Create pivot table for heatmap
        heatmap_data = data.pivot_table(
            values=value_column,
            index='Strike',
            columns='Expiry',
            aggfunc='mean',  # Average if multiple entries
            fill_value=0
        )
        
        # Limit to reasonable number of strikes for visualization
        if len(heatmap_data) > 20:
            # Keep strikes around the money
            middle_idx = len(heatmap_data) // 2
            start_idx = max(0, middle_idx - 10)
            end_idx = min(len(heatmap_data), middle_idx + 10)
            heatmap_data = heatmap_data.iloc[start_idx:end_idx]
        
        # Limit expiration dates
        if len(heatmap_data.columns) > 8:
            heatmap_data = heatmap_data.iloc[:, :8]
        
        return heatmap_data
    
    def _create_summary_stats(self):
        """Create summary statistics for heatmap"""
        if self.data.empty:
            return html.Div("No data available")
        
        # Calculate key metrics
        total_volume = self.data.get('Volume', pd.Series([0])).sum()
        avg_iv = self.data.get('IV', pd.Series([0])).mean()
        max_unusual = self.data.get('UnusualScore', pd.Series([0])).max()
        hot_strikes = len(self.data[self.data.get('Volume', 0) > self.data.get('Volume', pd.Series([0])).quantile(0.8)])
        
        return dbc.Row([
            dbc.Col([
                html.H6("Total Volume"),
                html.H4(f"{int(total_volume):,}", className="text-primary")
            ], md=3),
            dbc.Col([
                html.H6("Avg IV"),
                html.H4(f"{avg_iv:.1%}", className="text-info")
            ], md=3),
            dbc.Col([
                html.H6("Max Unusual"),
                html.H4(f"{max_unusual:.0f}", className="text-warning")
            ], md=3),
            dbc.Col([
                html.H6("Hot Strikes"),
                html.H4(f"{hot_strikes}", className="text-success")
            ], md=3)
        ])
    
    def create_layout(self, ticker: str) -> html.Div:
        """Create heatmap module layout"""
        return html.Div([
            # Header
            dbc.Row([
                dbc.Col([
                    dbc.Button("← Dashboard", id="dashboard-btn-simple", color="outline-primary", size="sm")
                ], width="auto"),
                dbc.Col([
                    html.H3(f"🔥 Options Heatmap - {ticker}", 
                           style={"color": THEME_CONFIG["primary_color"]})
                ])
            ], align="center", className="mb-4"),
            
            # Controls
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Button("🔄 Update Data", 
                                      id="fetch-heatmap-btn", 
                                      color="primary", 
                                      size="lg")
                        ], width="auto"),
                        dbc.Col([
                            dbc.ButtonGroup([
                                dbc.Button("Volume", id="show-volume-heat-btn", color="info", size="sm"),
                                dbc.Button("IV", id="show-iv-heat-btn", color="info", size="sm"),
                                dbc.Button("Unusual", id="show-unusual-heat-btn", color="info", size="sm"),
                                dbc.Button("Flow", id="show-flow-heat-btn", color="info", size="sm")
                            ])
                        ], width="auto"),
                        dbc.Col([
                            html.Div(id="heatmap-status", className="text-muted small")
                        ], className="ms-auto text-end")
                    ], align="center")
                ])
            ], className="mb-4"),
            
            # Summary stats
            dbc.Card([
                dbc.CardBody([
                    html.H5("Market Activity Summary", className="mb-3"),
                    html.Div(id="heatmap-summary")
                ])
            ], className="mb-4"),
            
            # Main content
            html.Div(id="heatmap-content", children=[
                self._create_welcome_message(ticker)
            ])
        ])
    
    def _create_welcome_message(self, ticker: str) -> html.Div:
        """Create welcome message"""
        return dbc.Card([
            dbc.CardBody([
                html.H4(f"Heatmap Analysis Ready for {ticker}", className="text-center"),
                html.P("Click 'Update Data' to load visual options heatmaps", 
                       className="text-center text-muted"),
                html.Hr(),
                dbc.Row([
                    dbc.Col([
                        html.H6("🔥 Heatmap Types:"),
                        html.Ul([
                            html.Li("Volume Heatmap - Trading activity"),
                            html.Li("IV Heatmap - Implied volatility levels"),
                            html.Li("Unusual Heatmap - Abnormal activity"),
                            html.Li("Flow Heatmap - Bullish/bearish direction")
                        ])
                    ], md=6),
                    dbc.Col([
                        html.H6("💡 Visual Features:"),
                        html.Ul([
                            html.Li("Color-coded intensity levels"),
                            html.Li("Interactive hover data"),
                            html.Li("Automatic hotspot detection"),
                            html.Li("Strike/expiration matrix view")
                        ])
                    ], md=6)
                ])
            ])
        ], style={"backgroundColor": THEME_CONFIG["paper_color"]})

# Global instance
options_heatmap_module = OptionsHeatmapModule()