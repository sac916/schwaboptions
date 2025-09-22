"""
Intraday Charts Module - ConvexValue 'flowchart' module equivalent  
Live intraday chart with price and options-based parameters overlay
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from modules.base_module import BaseModule
from data.module_data_adapter import ModuleDataAdapter
from data.processors import OptionsProcessor
from config import THEME_CONFIG

class IntradayChartsModule(BaseModule):
    """Intraday Price Charts with Options Flow Overlay"""
    
    def __init__(self):
        super().__init__(
            module_id="intraday_charts",
            name="Intraday Charts",
            description="Live intraday chart with options flow overlay"
        )
        self.price_history = []
        self.data_adapter = ModuleDataAdapter()
        self.flow_history = []
        
    def update_data(self, ticker: str, mode: str = "auto", target_date = None, **kwargs):
        """Update intraday data with options flow using universal data adapter"""
        try:
            # Get data through universal adapter
            data_result = self.data_adapter.get_options_analysis(
                symbol=ticker,
                analysis_type="intraday_charts",
                force_mode=mode,
                target_date=target_date
            )

            if data_result and data_result.get('options_data') is not None:
                self.data = data_result['options_data']
                self.data_quality = data_result.get('data_quality')
                self.data_info = data_result.get('data_info', {})

                # Get underlying price from data
                raw_data = data_result.get('raw_data', {})
                underlying_price = raw_data.get('underlying', {}).get('last', 0)
                current_time = datetime.now()

                # Store price point
                self.price_history.append({
                    'timestamp': current_time,
                    'price': underlying_price,
                    'ticker': ticker
                })
                
                # Calculate current flow metrics
                if not self.data.empty:
                    flow_metrics = self._calculate_flow_metrics()
                    flow_metrics['timestamp'] = current_time
                    flow_metrics['ticker'] = ticker
                    self.flow_history.append(flow_metrics)
                
                # Keep last 100 data points for intraday view
                if len(self.price_history) > 100:
                    self.price_history = self.price_history[-100:]
                if len(self.flow_history) > 100:
                    self.flow_history = self.flow_history[-100:]
                
                self._last_updated = current_time
                return self.data
        except Exception as e:
            print(f"Error updating intraday data: {e}")
        return None

    def get_data_quality_info(self):
        """Get current data quality information for UI display"""
        if hasattr(self, 'data_quality') and hasattr(self, 'data_info'):
            return {
                'quality': self.data_quality,
                'info': self.data_info
            }
        return None

    def _calculate_flow_metrics(self):
        """Calculate current flow metrics"""
        metrics = {}
        
        if self.data.empty:
            return metrics
        
        # Volume metrics
        total_volume = self.data.get('Volume', pd.Series([0])).sum()
        call_volume = self.data[self.data.get('Type', '') == 'CALL'].get('Volume', pd.Series([0])).sum()
        put_volume = self.data[self.data.get('Type', '') == 'PUT'].get('Volume', pd.Series([0])).sum()
        
        metrics['total_volume'] = total_volume
        metrics['call_volume'] = call_volume
        metrics['put_volume'] = put_volume
        metrics['call_put_ratio'] = call_volume / max(put_volume, 1)
        
        # Premium flow
        total_premium = self.data.get('Premium', pd.Series([0])).sum()
        call_premium = self.data[self.data.get('Type', '') == 'CALL'].get('Premium', pd.Series([0])).sum()
        put_premium = self.data[self.data.get('Type', '') == 'PUT'].get('Premium', pd.Series([0])).sum()
        
        metrics['total_premium'] = total_premium
        metrics['net_premium_flow'] = call_premium - put_premium
        
        # Unusual activity
        if 'UnusualScore' in self.data.columns:
            metrics['max_unusual'] = self.data['UnusualScore'].max()
            metrics['unusual_count'] = len(self.data[self.data['UnusualScore'] > 50])
        else:
            metrics['max_unusual'] = 0
            metrics['unusual_count'] = 0
        
        # IV metrics
        if 'IV' in self.data.columns:
            metrics['avg_iv'] = self.data['IV'].mean()
        else:
            metrics['avg_iv'] = 0
        
        return metrics
    
    def create_visualizations(self):
        """Create intraday chart visualizations"""
        return {
            "price_flow_chart": self._create_price_flow_chart(),
            "volume_timeline": self._create_volume_timeline(),
            "flow_indicators": self._create_flow_indicators(),
            "options_overlay": self._create_options_overlay()
        }
    
    def _create_price_flow_chart(self):
        """Create main price chart with options flow overlay"""
        if len(self.price_history) < 2:
            return html.Div("Insufficient data - keep updating to see intraday chart")
        
        price_df = pd.DataFrame(self.price_history)
        flow_df = pd.DataFrame(self.flow_history) if self.flow_history else pd.DataFrame()
        
        # Create subplots
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.6, 0.25, 0.15],
            subplot_titles=('Price with Flow', 'Volume Flow', 'Call/Put Ratio')
        )
        
        # Main price line
        fig.add_trace(
            go.Scatter(
                x=price_df['timestamp'],
                y=price_df['price'],
                mode='lines',
                name='Price',
                line=dict(color=THEME_CONFIG["text_color"], width=2)
            ),
            row=1, col=1
        )
        
        if not flow_df.empty:
            # Unusual activity markers
            unusual_events = flow_df[flow_df['unusual_count'] > 0]
            if not unusual_events.empty:
                fig.add_trace(
                    go.Scatter(
                        x=unusual_events['timestamp'],
                        y=unusual_events.index.map(price_df.set_index('timestamp')['price']),
                        mode='markers',
                        name='Unusual Activity',
                        marker=dict(
                            symbol='triangle-up',
                            color=THEME_CONFIG["secondary_color"],
                            size=10
                        )
                    ),
                    row=1, col=1
                )
            
            # Volume flow bars
            fig.add_trace(
                go.Bar(
                    x=flow_df['timestamp'],
                    y=flow_df['call_volume'],
                    name='Call Volume',
                    marker_color=THEME_CONFIG["primary_color"],
                    opacity=0.7
                ),
                row=2, col=1
            )
            
            fig.add_trace(
                go.Bar(
                    x=flow_df['timestamp'],
                    y=-flow_df['put_volume'],  # Negative for visual separation
                    name='Put Volume',
                    marker_color=THEME_CONFIG["secondary_color"],
                    opacity=0.7
                ),
                row=2, col=1
            )
            
            # Call/Put ratio line
            fig.add_trace(
                go.Scatter(
                    x=flow_df['timestamp'],
                    y=flow_df['call_put_ratio'],
                    mode='lines+markers',
                    name='C/P Ratio',
                    line=dict(color=THEME_CONFIG["accent_color"])
                ),
                row=3, col=1
            )
            
            # Add horizontal line at C/P ratio = 1
            fig.add_hline(
                y=1, line_dash="dash", line_color="white", 
                row=3, col=1
            )
        
        fig.update_layout(
            title="Intraday Price Action with Options Flow",
            plot_bgcolor=THEME_CONFIG["paper_color"],
            paper_bgcolor=THEME_CONFIG["background_color"],
            font=dict(color=THEME_CONFIG["text_color"]),
            height=700,
            showlegend=True
        )
        
        # Update axes
        fig.update_xaxes(title_text="Time", row=3, col=1)
        fig.update_yaxes(title_text="Price", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)
        fig.update_yaxes(title_text="Ratio", row=3, col=1)
        
        return dcc.Graph(figure=fig)
    
    def _create_volume_timeline(self):
        """Create volume timeline chart"""
        if not self.flow_history:
            return html.Div("No flow data available")
        
        flow_df = pd.DataFrame(self.flow_history)
        
        fig = go.Figure()
        
        # Stacked area chart for call/put volume
        fig.add_trace(go.Scatter(
            x=flow_df['timestamp'],
            y=flow_df['call_volume'],
            mode='lines',
            stackgroup='volume',
            name='Call Volume',
            fill='tonexty',
            line=dict(color=THEME_CONFIG["primary_color"])
        ))
        
        fig.add_trace(go.Scatter(
            x=flow_df['timestamp'],
            y=flow_df['put_volume'],
            mode='lines',
            stackgroup='volume',
            name='Put Volume', 
            fill='tonexty',
            line=dict(color=THEME_CONFIG["secondary_color"])
        ))
        
        fig.update_layout(
            title="Volume Flow Timeline",
            xaxis_title="Time",
            yaxis_title="Cumulative Volume",
            plot_bgcolor=THEME_CONFIG["paper_color"],
            paper_bgcolor=THEME_CONFIG["background_color"],
            font=dict(color=THEME_CONFIG["text_color"]),
            height=400
        )
        
        return dcc.Graph(figure=fig)
    
    def _create_flow_indicators(self):
        """Create flow indicator gauges"""
        if not self.flow_history:
            return html.Div("No flow indicators available")
        
        latest_flow = self.flow_history[-1]
        
        # Create gauge charts
        fig = make_subplots(
            rows=1, cols=3,
            specs=[[{"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}]],
            subplot_titles=('Call/Put Ratio', 'Unusual Activity', 'Average IV')
        )
        
        # Call/Put ratio gauge
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=latest_flow.get('call_put_ratio', 1),
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "C/P Ratio"},
                gauge={
                    'axis': {'range': [None, 3]},
                    'bar': {'color': THEME_CONFIG["primary_color"]},
                    'steps': [
                        {'range': [0, 0.5], 'color': THEME_CONFIG["secondary_color"]},
                        {'range': [0.5, 1.5], 'color': 'gray'},
                        {'range': [1.5, 3], 'color': THEME_CONFIG["primary_color"]}
                    ],
                    'threshold': {
                        'line': {'color': "white", 'width': 4},
                        'thickness': 0.75,
                        'value': 1
                    }
                }
            ),
            row=1, col=1
        )
        
        # Unusual activity gauge
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=latest_flow.get('unusual_count', 0),
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Unusual Count"},
                gauge={
                    'axis': {'range': [None, 20]},
                    'bar': {'color': THEME_CONFIG["secondary_color"]},
                    'steps': [
                        {'range': [0, 5], 'color': 'green'},
                        {'range': [5, 10], 'color': 'yellow'},
                        {'range': [10, 20], 'color': 'red'}
                    ]
                }
            ),
            row=1, col=2
        )
        
        # Average IV gauge
        fig.add_trace(
            go.Indicator(
                mode="gauge+number+delta",
                value=latest_flow.get('avg_iv', 0) * 100,  # Convert to percentage
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Avg IV %"},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': THEME_CONFIG["accent_color"]},
                    'steps': [
                        {'range': [0, 20], 'color': 'lightgray'},
                        {'range': [20, 40], 'color': 'yellow'},
                        {'range': [40, 100], 'color': 'red'}
                    ]
                }
            ),
            row=1, col=3
        )
        
        fig.update_layout(
            font=dict(color=THEME_CONFIG["text_color"]),
            paper_bgcolor=THEME_CONFIG["background_color"],
            height=300
        )
        
        return dcc.Graph(figure=fig)
    
    def _create_options_overlay(self):
        """Create options-specific overlay indicators"""
        if not self.flow_history:
            return html.Div("No overlay data available")
        
        flow_df = pd.DataFrame(self.flow_history)
        
        fig = go.Figure()
        
        # Net premium flow
        fig.add_trace(go.Scatter(
            x=flow_df['timestamp'],
            y=flow_df['net_premium_flow'],
            mode='lines+markers',
            name='Net Premium Flow',
            line=dict(color=THEME_CONFIG["accent_color"], width=2),
            fill='tozeroy',
            fillcolor=f"rgba({tuple(int(THEME_CONFIG['accent_color'][i:i+2], 16) for i in (1, 3, 5))}, 0.3)"
        ))
        
        # Zero line
        fig.add_hline(
            y=0, 
            line_dash="solid", 
            line_color="white",
            annotation_text="Neutral Flow"
        )
        
        # Unusual activity events
        unusual_points = flow_df[flow_df['max_unusual'] > 50]
        if not unusual_points.empty:
            fig.add_trace(go.Scatter(
                x=unusual_points['timestamp'],
                y=unusual_points['net_premium_flow'],
                mode='markers',
                name='High Unusual Activity',
                marker=dict(
                    symbol='star',
                    color=THEME_CONFIG["secondary_color"],
                    size=15,
                    line=dict(color='white', width=1)
                )
            ))
        
        fig.update_layout(
            title="Options Premium Flow Analysis",
            xaxis_title="Time",
            yaxis_title="Net Premium Flow ($)",
            plot_bgcolor=THEME_CONFIG["paper_color"],
            paper_bgcolor=THEME_CONFIG["background_color"],
            font=dict(color=THEME_CONFIG["text_color"]),
            height=400
        )
        
        return dcc.Graph(figure=fig)
    
    def create_layout(self, ticker: str) -> html.Div:
        """Create intraday charts layout"""
        return html.Div([
            # Header
            dbc.Row([
                dbc.Col([
                    dbc.Button("← Dashboard", id={"type": "back-button", "module": "intraday_charts"}, color="outline-primary", size="sm")
                ], width="auto"),
                dbc.Col([
                    html.H3(f"📈 Intraday Charts - {ticker}",
                           style={"color": THEME_CONFIG["primary_color"]})
                ])
            ], align="center", className="mb-4"),
            
            # Controls
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Button("🔄 Update Chart", 
                                      id="update-intraday-btn",
                                      color="primary",
                                      size="lg")
                        ], width="auto"),
                        dbc.Col([
                            dbc.ButtonGroup([
                                dbc.Button("Price+Flow", id="show-price-flow-btn", color="info", size="sm"),
                                dbc.Button("Volume", id="show-vol-timeline-btn", color="info", size="sm"),
                                dbc.Button("Indicators", id="show-indicators-btn", color="info", size="sm"),
                                dbc.Button("Overlay", id="show-overlay-btn", color="info", size="sm")
                            ])
                        ], width="auto"),
                        dbc.Col([
                            html.Div([
                                html.Span("Auto-refresh: ", className="me-2"),
                                dbc.Switch(id="auto-refresh-switch", value=False, className="d-inline")
                            ], className="d-flex align-items-center")
                        ], width="auto"),
                        dbc.Col([
                            html.Div(id="intraday-status", className="text-muted small")
                        ], className="ms-auto text-end")
                    ], align="center")
                ])
            ], className="mb-4"),
            
            # Live metrics
            dbc.Card([
                dbc.CardBody([
                    html.H5("📊 Live Flow Metrics", className="mb-3"),
                    html.Div(id="live-metrics", children=[
                        self._create_live_metrics_placeholder()
                    ])
                ])
            ], className="mb-4"),
            
            # Main content
            html.Div(id="intraday-content", children=[
                self._create_welcome_message(ticker)
            ]),
            
            # Auto-refresh interval (disabled by default)
            dcc.Interval(
                id='intraday-refresh-interval',
                interval=30000,  # 30 seconds
                n_intervals=0,
                disabled=True
            )
        ])
    
    def _create_live_metrics_placeholder(self):
        """Create placeholder for live metrics"""
        return dbc.Row([
            dbc.Col([
                html.H6("Data Points"),
                html.H4("0", className="text-primary", id="data-points-count")
            ], md=3),
            dbc.Col([
                html.H6("Current C/P"),
                html.H4("--", className="text-info", id="current-cp-ratio")
            ], md=3),
            dbc.Col([
                html.H6("Unusual Events"),
                html.H4("0", className="text-warning", id="unusual-events-count")
            ], md=3),
            dbc.Col([
                html.H6("Time Span"),
                html.H4("--", className="text-success", id="time-span")
            ], md=3)
        ])
    
    def _create_welcome_message(self, ticker: str) -> html.Div:
        """Create welcome message"""
        return dbc.Card([
            dbc.CardBody([
                html.H4(f"Intraday Analysis Ready for {ticker}", className="text-center"),
                html.P("Real-time price charts with live options flow overlay", 
                       className="text-center text-muted"),
                html.Hr(),
                dbc.Row([
                    dbc.Col([
                        html.H6("📈 Chart Features:"),
                        html.Ul([
                            html.Li("Live price action"),
                            html.Li("Options flow overlay"),
                            html.Li("Volume timeline"),
                            html.Li("Real-time indicators")
                        ])
                    ], md=6),
                    dbc.Col([
                        html.H6("⚡ Live Updates:"),
                        html.Ul([
                            html.Li("Auto-refresh capability"),
                            html.Li("Unusual activity alerts"),
                            html.Li("Flow direction changes"),
                            html.Li("Premium flow analysis")
                        ])
                    ], md=6)
                ]),
                html.Hr(),
                dbc.Alert([
                    html.Strong("Tip: "),
                    "Enable auto-refresh for live updates, or click 'Update Chart' manually to add data points."
                ], color="info", className="mb-0")
            ])
        ], style={"backgroundColor": THEME_CONFIG["paper_color"]})

# Global instance
intraday_charts_module = IntradayChartsModule()