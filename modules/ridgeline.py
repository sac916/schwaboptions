"""
Ridgeline Module - ConvexValue 'joy' module equivalent
Live ridgeline plots showing options chain depth visualization
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

from modules.base_module import BaseModule
from data.schwab_client import schwab_client
from data.processors import OptionsProcessor
from config import THEME_CONFIG

class RidgelineModule(BaseModule):
    """Ridgeline Plots for Options Chain Depth Visualization"""

    def __init__(self):
        super().__init__(
            module_id="ridgeline",
            name="Ridgeline",
            description="Live ridgeline plots showing options chain depth visualization"
        )
        self.ridgeline_history = []  # Store historical ridgeline data
        self.current_spot = None

    def update_data(self, ticker: str, **kwargs):
        """Update ridgeline data"""
        try:
            raw_data = schwab_client.get_option_chain(
                symbol=ticker,
                contractType="ALL",           # Get both calls and puts
                strikeCount=50,               # More strikes for better ridgeline
                includeUnderlyingQuote=True,  # Include underlying stock data
                range="ALL",                  # All options for full distribution
                daysToExpiration=120          # 4 months for multiple ridges
            )
            if raw_data:
                self.data = OptionsProcessor.parse_option_chain(raw_data)
                self._last_updated = datetime.now()

                # Extract current spot price
                if hasattr(raw_data, 'underlyingQuote') and raw_data.underlyingQuote:
                    self.current_spot = raw_data.underlyingQuote.get('last', 0)
                elif not self.data.empty:
                    self.current_spot = self.data['Underlying_Price'].iloc[0]

                # Store historical ridgeline point
                if not self.data.empty:
                    current_metrics = self._calculate_ridgeline_metrics()
                    self.ridgeline_history.append({
                        'timestamp': datetime.now(),
                        'ticker': ticker,
                        'spot_price': self.current_spot,
                        **current_metrics
                    })

                    # Keep only last 50 data points
                    if len(self.ridgeline_history) > 50:
                        self.ridgeline_history = self.ridgeline_history[-50:]

                return self.data
        except Exception as e:
            print(f"Error updating ridgeline data: {e}")
        return None

    def _calculate_ridgeline_metrics(self):
        """Calculate key ridgeline metrics"""
        if self.data.empty:
            return {}

        # Group by expiration for ridgeline analysis
        exp_groups = self.data.groupby('Expiry').agg({
            'Volume': ['sum', 'mean', 'max'],
            'openInterest': ['sum', 'mean', 'max'],
            'Strike': ['min', 'max', 'count'],
            'DTE': 'first',
            'Premium': ['sum', 'mean']
        }).round(2)

        # Flatten column names
        exp_groups.columns = ['_'.join(col).strip() for col in exp_groups.columns]

        return {
            'total_volume': exp_groups['Volume_sum'].sum(),
            'total_oi': exp_groups['openInterest_sum'].sum(),
            'active_expirations': len(exp_groups),
            'volume_concentration': exp_groups['Volume_sum'].std() / exp_groups['Volume_sum'].mean() if exp_groups['Volume_sum'].mean() > 0 else 0,
            'strike_spread': exp_groups['Strike_max'].mean() - exp_groups['Strike_min'].mean()
        }

    def create_layout(self, ticker: str):
        """Create ridgeline module layout"""
        return html.Div([
            # Header
            dbc.Row([
                dbc.Col([
                    html.H3(f"📊 Ridgeline Analysis - {ticker}", className="text-white mb-3"),
                    html.P("Live ridgeline plots showing options chain depth and distribution",
                           className="text-muted mb-4")
                ])
            ]),

            # Control Panel
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Controls", className="text-white mb-3"),

                            dbc.ButtonGroup([
                                dbc.Button("Update Data", id="fetch-ridgeline-btn", color="primary", size="sm"),
                                dbc.Button("Volume Ridge", id="show-volume-ridge-btn", color="info", size="sm"),
                                dbc.Button("OI Ridge", id="show-oi-ridge-btn", color="success", size="sm"),
                                dbc.Button("Combined", id="show-combined-ridge-btn", color="warning", size="sm")
                            ], className="mb-3"),

                            # Ridge type selector
                            html.Div([
                                html.Label("Ridge Type:", className="text-white mb-2"),
                                dcc.Dropdown(
                                    id="ridge-type-selector",
                                    options=[
                                        {"label": "Volume Distribution", "value": "volume"},
                                        {"label": "Open Interest", "value": "oi"},
                                        {"label": "Premium Flow", "value": "premium"},
                                        {"label": "Activity Heatmap", "value": "activity"}
                                    ],
                                    value="volume",
                                    className="mb-3",
                                    style={"color": "#000"}
                                )
                            ])
                        ])
                    ], color="dark", outline=True)
                ], width=12)
            ], className="mb-4"),

            # Summary Cards
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Total Volume", className="text-muted"),
                            html.H4(id="ridgeline-total-volume", className="text-primary"),
                        ])
                    ], color="dark", outline=True)
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Total OI", className="text-muted"),
                            html.H4(id="ridgeline-total-oi", className="text-success"),
                        ])
                    ], color="dark", outline=True)
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Active Expirations", className="text-muted"),
                            html.H4(id="ridgeline-expirations", className="text-info"),
                        ])
                    ], color="dark", outline=True)
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Current Spot", className="text-muted"),
                            html.H4(id="ridgeline-spot-price", className="text-warning"),
                        ])
                    ], color="dark", outline=True)
                ], width=3)
            ], className="mb-4"),

            # Status Row
            dbc.Row([
                dbc.Col([
                    html.Div(id="ridgeline-status", className="text-info")
                ], width=12)
            ], className="mb-3"),

            # Main Content Area
            dbc.Row([
                dbc.Col([
                    html.Div(id="ridgeline-content", children=[
                        dbc.Card([
                            dbc.CardBody([
                                html.H5("📊 Ridgeline Visualization", className="text-white mb-3"),
                                html.P("Click 'Update Data' to load ridgeline plots showing options distribution across strikes and expirations.",
                                       className="text-muted"),
                                html.Hr(),
                                html.P("🎯 Ridge Features:", className="text-white mb-2"),
                                html.Ul([
                                    html.Li("Volume distribution by strike across expirations"),
                                    html.Li("Open interest concentration patterns"),
                                    html.Li("Real-time activity flow visualization"),
                                    html.Li("Interactive 3D ridgeline surfaces")
                                ], className="text-muted")
                            ])
                        ], color="dark", outline=True)
                    ])
                ], width=12)
            ])
        ], className="p-4")

    def create_visualizations(self):
        """Create ridgeline visualizations"""
        if self.data is None or self.data.empty:
            return {
                "volume_ridge": go.Figure().add_annotation(
                    text="No data available", x=0.5, y=0.5,
                    showarrow=False, font=dict(color="white", size=16)
                ),
                "oi_ridge": go.Figure().add_annotation(
                    text="No data available", x=0.5, y=0.5,
                    showarrow=False, font=dict(color="white", size=16)
                ),
                "combined_ridge": go.Figure().add_annotation(
                    text="No data available", x=0.5, y=0.5,
                    showarrow=False, font=dict(color="white", size=16)
                )
            }

        # Create volume ridgeline
        volume_ridge = self._create_volume_ridgeline()

        # Create OI ridgeline
        oi_ridge = self._create_oi_ridgeline()

        # Create combined ridgeline
        combined_ridge = self._create_combined_ridgeline()

        return {
            "volume_ridge": volume_ridge,
            "oi_ridge": oi_ridge,
            "combined_ridge": combined_ridge
        }

    def _create_volume_ridgeline(self):
        """Create volume distribution ridgeline plot"""
        fig = go.Figure()

        # Get unique expirations sorted by DTE
        expirations = self.data['Expiry'].unique()
        exp_data = []
        for exp in expirations:
            exp_df = self.data[self.data['Expiry'] == exp]
            if not exp_df.empty:
                exp_data.append((exp, exp_df['DTE'].iloc[0], exp_df))

        # Sort by DTE
        exp_data.sort(key=lambda x: x[1])

        # Create ridgeline for each expiration
        colors = px.colors.qualitative.Set3
        y_offset = 0

        for i, (exp, dte, exp_df) in enumerate(exp_data[:8]):  # Limit to 8 expirations
            # Group by strike for distribution
            strike_volume = exp_df.groupby('Strike')['Volume'].sum().reset_index()

            if len(strike_volume) > 0:
                # Normalize for ridgeline effect
                max_vol = strike_volume['Volume'].max()
                if max_vol > 0:
                    strike_volume['Normalized'] = strike_volume['Volume'] / max_vol

                    # Create filled area
                    fig.add_trace(go.Scatter(
                        x=strike_volume['Strike'],
                        y=strike_volume['Normalized'] + y_offset,
                        mode='lines',
                        fill='tonexty' if i > 0 else 'tozeroy',
                        fillcolor=colors[i % len(colors)],
                        line=dict(color=colors[i % len(colors)], width=2),
                        name=f"{dte}d exp ({exp})",
                        hovertemplate=f"<b>{dte}d to exp</b><br>" +
                                    "Strike: $%{x}<br>" +
                                    "Volume: %{customdata}<br>" +
                                    "<extra></extra>",
                        customdata=strike_volume['Volume']
                    ))

                    # Add baseline
                    fig.add_hline(y=y_offset, line_dash="dot",
                                line_color="rgba(255,255,255,0.3)", line_width=1)

            y_offset += 1.2

        # Add spot price line
        if self.current_spot:
            fig.add_vline(x=self.current_spot, line_dash="dash",
                         line_color="yellow", line_width=2,
                         annotation_text=f"Spot: ${self.current_spot:.2f}")

        fig.update_layout(
            title="Volume Distribution Ridgeline",
            xaxis_title="Strike Price ($)",
            yaxis_title="Expirations (Normalized Volume)",
            template="plotly_dark",
            paper_bgcolor=THEME_CONFIG["paper_color"],
            plot_bgcolor=THEME_CONFIG["background_color"],
            height=600,
            showlegend=True,
            legend=dict(x=1.02, y=1)
        )

        return fig

    def _create_oi_ridgeline(self):
        """Create open interest ridgeline plot"""
        fig = go.Figure()

        # Similar to volume but for OI
        expirations = self.data['Expiry'].unique()
        exp_data = []
        for exp in expirations:
            exp_df = self.data[self.data['Expiry'] == exp]
            if not exp_df.empty:
                exp_data.append((exp, exp_df['DTE'].iloc[0], exp_df))

        exp_data.sort(key=lambda x: x[1])

        colors = px.colors.qualitative.Pastel
        y_offset = 0

        for i, (exp, dte, exp_df) in enumerate(exp_data[:8]):
            strike_oi = exp_df.groupby('Strike')['openInterest'].sum().reset_index()

            if len(strike_oi) > 0:
                max_oi = strike_oi['openInterest'].max()
                if max_oi > 0:
                    strike_oi['Normalized'] = strike_oi['openInterest'] / max_oi

                    fig.add_trace(go.Scatter(
                        x=strike_oi['Strike'],
                        y=strike_oi['Normalized'] + y_offset,
                        mode='lines',
                        fill='tonexty' if i > 0 else 'tozeroy',
                        fillcolor=colors[i % len(colors)],
                        line=dict(color=colors[i % len(colors)], width=2),
                        name=f"{dte}d exp ({exp})",
                        hovertemplate=f"<b>{dte}d to exp</b><br>" +
                                    "Strike: $%{x}<br>" +
                                    "OI: %{customdata}<br>" +
                                    "<extra></extra>",
                        customdata=strike_oi['openInterest']
                    ))

                    fig.add_hline(y=y_offset, line_dash="dot",
                                line_color="rgba(255,255,255,0.3)", line_width=1)

            y_offset += 1.2

        if self.current_spot:
            fig.add_vline(x=self.current_spot, line_dash="dash",
                         line_color="yellow", line_width=2,
                         annotation_text=f"Spot: ${self.current_spot:.2f}")

        fig.update_layout(
            title="Open Interest Distribution Ridgeline",
            xaxis_title="Strike Price ($)",
            yaxis_title="Expirations (Normalized OI)",
            template="plotly_dark",
            paper_bgcolor=THEME_CONFIG["paper_color"],
            plot_bgcolor=THEME_CONFIG["background_color"],
            height=600,
            showlegend=True,
            legend=dict(x=1.02, y=1)
        )

        return fig

    def _create_combined_ridgeline(self):
        """Create combined volume + OI ridgeline"""
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=["Volume Distribution", "Open Interest Distribution"],
            vertical_spacing=0.1,
            shared_xaxes=True
        )

        # Add volume ridgeline to top subplot
        vol_fig = self._create_volume_ridgeline()
        for trace in vol_fig.data:
            fig.add_trace(trace, row=1, col=1)

        # Add OI ridgeline to bottom subplot
        oi_fig = self._create_oi_ridgeline()
        for trace in oi_fig.data:
            trace.showlegend = False  # Don't duplicate legend
            fig.add_trace(trace, row=2, col=1)

        # Add spot price lines
        if self.current_spot:
            fig.add_vline(x=self.current_spot, line_dash="dash",
                         line_color="yellow", line_width=2, row=1, col=1)
            fig.add_vline(x=self.current_spot, line_dash="dash",
                         line_color="yellow", line_width=2, row=2, col=1)

        fig.update_layout(
            title="Combined Ridgeline Analysis",
            template="plotly_dark",
            paper_bgcolor=THEME_CONFIG["paper_color"],
            plot_bgcolor=THEME_CONFIG["background_color"],
            height=800,
            showlegend=True
        )

        fig.update_xaxes(title_text="Strike Price ($)", row=2, col=1)
        fig.update_yaxes(title_text="Normalized Volume", row=1, col=1)
        fig.update_yaxes(title_text="Normalized OI", row=2, col=1)

        return fig

# Create module instance
ridgeline_module = RidgelineModule()