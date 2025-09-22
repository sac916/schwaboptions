"""
IV Term Structure Module - ConvexValue 'terms' module equivalent
Professional implied volatility analysis with historical watermarks
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.interpolate import griddata
import warnings
warnings.filterwarnings('ignore')

from modules.base_module import BaseModule
from data.module_data_adapter import ModuleDataAdapter
from data.processors import OptionsProcessor
from config import THEME_CONFIG

class IVSurfaceModule(BaseModule):
    """IV Term Structure and Surface Analysis"""
    
    def __init__(self):
        super().__init__(
            module_id="iv_surface",
            name="IV Surface",
            description="Implied volatility term structure with historical watermarks"
        )
        self.iv_history = []  # Store historical IV data
        self.data_adapter = ModuleDataAdapter()
        
    def update_data(self, ticker: str, mode: str = "auto", target_date = None, **kwargs):
        """Update IV surface data using universal data adapter"""
        try:
            # Get data through universal adapter
            data_result = self.data_adapter.get_options_analysis(
                symbol=ticker,
                analysis_type="iv_surface",
                force_mode=mode,
                target_date=target_date
            )

            if data_result and data_result.get('options_data') is not None:
                self.data = data_result['options_data']
                self.data_quality = data_result.get('data_quality')
                self.data_info = data_result.get('data_info', {})
                self._last_updated = datetime.now()

                # Store historical IV point
                if not self.data.empty:
                    current_iv = self._calculate_iv_metrics()
                    self.iv_history.append({
                        'timestamp': datetime.now(),
                        'ticker': ticker,
                        **current_iv
                    })
                    
                    # Keep only last 100 data points
                    if len(self.iv_history) > 100:
                        self.iv_history = self.iv_history[-100:]
                
                return self.data
        except Exception as e:
            print(f"Error updating IV data: {e}")
        return None

    def get_data_quality_info(self):
        """Get current data quality information for UI display"""
        if hasattr(self, 'data_quality') and hasattr(self, 'data_info'):
            return {
                'quality': self.data_quality,
                'info': self.data_info
            }
        return None

    def _calculate_iv_metrics(self):
        """Calculate key IV metrics"""
        if self.data.empty:
            return {}
            
        # Group by expiration to get term structure
        iv_by_exp = self.data.groupby('Expiry').agg({
            'IV': ['mean', 'std', 'min', 'max'],
            'Volume': 'sum',
            'DTE': 'first'
        }).round(4)
        
        # Flatten column names
        iv_by_exp.columns = ['_'.join(col).strip() for col in iv_by_exp.columns]
        
        return {
            'atm_iv_30d': iv_by_exp[iv_by_exp['DTE_first'] <= 35]['IV_mean'].mean() if len(iv_by_exp) > 0 else 0,
            'atm_iv_60d': iv_by_exp[iv_by_exp['DTE_first'] <= 65]['IV_mean'].mean() if len(iv_by_exp) > 0 else 0,
            'iv_skew': iv_by_exp['IV_std'].mean() if len(iv_by_exp) > 0 else 0,
            'term_structure_slope': self._calculate_term_slope(iv_by_exp)
        }
    
    def _calculate_term_slope(self, iv_by_exp):
        """Calculate term structure slope"""
        if len(iv_by_exp) < 2:
            return 0
            
        # Simple linear regression on DTE vs IV
        x = iv_by_exp['DTE_first'].values
        y = iv_by_exp['IV_mean'].values
        
        if len(x) > 1:
            slope = np.polyfit(x, y, 1)[0]
            return slope
        return 0
    
    def _validate_and_clean_iv_data(self):
        """Validate and clean IV data for surface plotting"""
        if self.data is None or self.data.empty:
            return pd.DataFrame()
        
        # Create a copy for cleaning
        clean_data = self.data.copy()
        
        # 1. Filter realistic IV ranges (5% to 200%)
        clean_data = clean_data[
            (clean_data['IV'] >= 0.05) & 
            (clean_data['IV'] <= 2.0) &
            (clean_data['IV'].notna())
        ]
        
        # 2. Filter realistic DTE ranges (1 to 365 days)
        clean_data = clean_data[
            (clean_data['DTE'] >= 1) & 
            (clean_data['DTE'] <= 365)
        ]
        
        # 3. Remove options with very low volume/OI (likely stale quotes)
        min_volume = max(1, clean_data['Volume'].quantile(0.1)) if 'Volume' in clean_data.columns else 1
        min_oi = max(1, clean_data['Open Int'].quantile(0.1)) if 'Open Int' in clean_data.columns else 1
        
        if 'Volume' in clean_data.columns:
            clean_data = clean_data[clean_data['Volume'] >= min_volume]
        if 'Open Int' in clean_data.columns:
            clean_data = clean_data[clean_data['Open Int'] >= min_oi]
        
        # 4. Remove statistical outliers (IV values > 3 standard deviations)
        if len(clean_data) > 10:
            iv_mean = clean_data['IV'].mean()
            iv_std = clean_data['IV'].std()
            clean_data = clean_data[
                abs(clean_data['IV'] - iv_mean) <= 3 * iv_std
            ]
        
        # 5. Ensure we have sufficient data points for surface
        if len(clean_data) < 10:
            print(f"Warning: Only {len(clean_data)} data points after cleaning")
            
        return clean_data
    
    def create_visualizations(self):
        """Create IV surface visualizations"""
        if self.data is None or self.data.empty:
            return {}
            
        return {
            "term_structure": self._create_term_structure_chart(),
            "iv_surface": self._create_iv_surface_3d(),
            "historical_iv": self._create_historical_chart(),
            "skew_analysis": self._create_skew_chart()
        }
    
    def _create_term_structure_chart(self):
        """Create term structure line chart"""
        # Group by expiration
        term_data = self.data.groupby(['Expiry', 'DTE']).agg({
            'IV': 'mean',
            'Volume': 'sum'
        }).reset_index().sort_values('DTE')
        
        fig = go.Figure()
        
        # Main term structure line
        fig.add_trace(go.Scatter(
            x=term_data['DTE'],
            y=term_data['IV'],
            mode='lines+markers',
            name='IV Term Structure',
            line=dict(color=THEME_CONFIG["primary_color"], width=3),
            marker=dict(size=8, color=THEME_CONFIG["primary_color"])
        ))
        
        # Add volume overlay
        fig.add_trace(go.Scatter(
            x=term_data['DTE'],
            y=term_data['Volume'] / term_data['Volume'].max() * term_data['IV'].max(),
            mode='lines',
            name='Volume (Scaled)',
            line=dict(color=THEME_CONFIG["accent_color"], dash='dash'),
            yaxis='y2',
            opacity=0.6
        ))
        
        fig.update_layout(
            title="Implied Volatility Term Structure",
            xaxis_title="Days to Expiration",
            yaxis_title="Implied Volatility",
            yaxis2=dict(overlaying='y', side='right', title='Volume'),
            plot_bgcolor=THEME_CONFIG["paper_color"],
            paper_bgcolor=THEME_CONFIG["background_color"],
            font=dict(color=THEME_CONFIG["text_color"]),
            height=500
        )
        
        return dcc.Graph(figure=fig)
    
    def _create_iv_surface_3d(self):
        """Create professional 3D IV surface plot with proper interpolation"""
        # Get clean data
        clean_data = self._validate_and_clean_iv_data()
        
        if clean_data.empty or len(clean_data) < 10:
            return html.Div([
                dbc.Alert("Insufficient clean data for surface plot. Need at least 10 valid options contracts.", 
                         color="warning")
            ])
        
        try:
            # Prepare data points for interpolation
            strikes = clean_data['Strike'].values
            dtes = clean_data['DTE'].values  
            ivs = clean_data['IV'].values
            
            # Create uniform grid for smooth surface
            strike_min, strike_max = strikes.min(), strikes.max()
            dte_min, dte_max = dtes.min(), dtes.max()
            
            # Professional mesh density (50x50 grid)
            grid_strikes = np.linspace(strike_min, strike_max, 50)
            grid_dtes = np.linspace(dte_min, dte_max, 50)
            
            # Create mesh grid
            strike_grid, dte_grid = np.meshgrid(grid_strikes, grid_dtes)
            
            # Interpolate IV values using cubic interpolation
            iv_grid = griddata(
                points=(strikes, dtes),
                values=ivs,
                xi=(strike_grid, dte_grid),
                method='cubic',
                fill_value=np.nan
            )
            
            # Fallback to linear if cubic fails
            if np.isnan(iv_grid).all():
                iv_grid = griddata(
                    points=(strikes, dtes),
                    values=ivs,
                    xi=(strike_grid, dte_grid),
                    method='linear',
                    fill_value=np.nan
                )
            
            # Remove any remaining NaN values at edges
            iv_grid = np.nan_to_num(iv_grid, nan=np.nanmean(iv_grid))
            
            # Create professional volatility surface
            fig = go.Figure(data=[
                go.Surface(
                    z=iv_grid,
                    x=grid_dtes,        # DTE on X-axis
                    y=grid_strikes,     # Strike on Y-axis
                    colorscale='RdYlBu_r',  # Professional vol color scheme
                    name='IV Surface',
                    hovertemplate='<b>Strike:</b> %{y:.0f}<br>' +
                                '<b>DTE:</b> %{x:.0f}<br>' + 
                                '<b>IV:</b> %{z:.1%}<br>' +
                                '<extra></extra>',
                    lighting=dict(ambient=0.4, diffuse=0.8, fresnel=0.2),
                    colorbar=dict(
                        title="Implied Volatility (%)",
                        titlefont=dict(color=THEME_CONFIG["text_color"]),
                        tickfont=dict(color=THEME_CONFIG["text_color"])
                    )
                )
            ])
            
            # Add scatter points for actual data
            fig.add_trace(go.Scatter3d(
                x=dtes,
                y=strikes, 
                z=ivs,
                mode='markers',
                marker=dict(
                    size=4,
                    color='white',
                    line=dict(color='black', width=1)
                ),
                name='Market Data',
                hovertemplate='<b>Strike:</b> %{y:.0f}<br>' +
                            '<b>DTE:</b> %{x:.0f}<br>' +
                            '<b>IV:</b> %{z:.1%}<br>' +
                            '<extra></extra>'
            ))
            
            # Professional layout with optimal camera angle
            fig.update_layout(
                title='Professional Implied Volatility Surface',
                scene=dict(
                    xaxis_title='Days to Expiration',
                    yaxis_title='Strike Price', 
                    zaxis_title='Implied Volatility',
                    bgcolor=THEME_CONFIG["background_color"],
                    xaxis=dict(color=THEME_CONFIG["text_color"]),
                    yaxis=dict(color=THEME_CONFIG["text_color"]),
                    zaxis=dict(color=THEME_CONFIG["text_color"]),
                    camera=dict(
                        eye=dict(x=1.5, y=1.5, z=1.2),  # Optimal viewing angle
                        center=dict(x=0, y=0, z=0)
                    )
                ),
                plot_bgcolor=THEME_CONFIG["paper_color"],
                paper_bgcolor=THEME_CONFIG["background_color"],
                font=dict(color=THEME_CONFIG["text_color"], size=12),
                height=700,
                showlegend=True
            )
            
            return dcc.Graph(figure=fig, style={'height': '700px'})
            
        except Exception as e:
            return html.Div([
                dbc.Alert(f"Error creating 3D surface: {str(e)}", color="danger"),
                html.P("Try using the 2D heatmap view instead.", className="text-muted")
            ])
    
    def _create_historical_chart(self):
        """Create historical IV watermarks chart"""
        if len(self.iv_history) < 2:
            return html.Div("Insufficient historical data - keep app running to accumulate data")
        
        hist_df = pd.DataFrame(self.iv_history)
        
        fig = go.Figure()
        
        # Historical 30-day IV
        fig.add_trace(go.Scatter(
            x=hist_df['timestamp'],
            y=hist_df['atm_iv_30d'],
            mode='lines',
            name='30d ATM IV',
            line=dict(color=THEME_CONFIG["primary_color"])
        ))
        
        # Historical 60-day IV  
        fig.add_trace(go.Scatter(
            x=hist_df['timestamp'],
            y=hist_df['atm_iv_60d'],
            mode='lines',
            name='60d ATM IV',
            line=dict(color=THEME_CONFIG["secondary_color"])
        ))
        
        # Add percentile bands
        if len(hist_df) > 10:
            p90 = hist_df['atm_iv_30d'].quantile(0.9)
            p10 = hist_df['atm_iv_30d'].quantile(0.1)
            
            fig.add_hline(y=p90, line_dash="dash", 
                         annotation_text="90th Percentile",
                         line_color=THEME_CONFIG["accent_color"])
            fig.add_hline(y=p10, line_dash="dash",
                         annotation_text="10th Percentile", 
                         line_color=THEME_CONFIG["accent_color"])
        
        fig.update_layout(
            title="Historical IV Watermarks",
            xaxis_title="Time",
            yaxis_title="Implied Volatility",
            plot_bgcolor=THEME_CONFIG["paper_color"],
            paper_bgcolor=THEME_CONFIG["background_color"],
            font=dict(color=THEME_CONFIG["text_color"]),
            height=400
        )
        
        return dcc.Graph(figure=fig)
    
    def _create_skew_chart(self):
        """Create volatility skew analysis"""
        # Calculate skew by strike relative to ATM
        if 'Strike' not in self.data.columns:
            return html.Div("No strike data available")
            
        # Find ATM strike (closest to current price)
        underlying_price = self.data['Strike'].median()  # Approximation
        self.data['Moneyness_Pct'] = (self.data['Strike'] - underlying_price) / underlying_price * 100
        
        # Group by moneyness for skew analysis
        skew_data = self.data.groupby(pd.cut(self.data['Moneyness_Pct'], bins=20)).agg({
            'IV': 'mean',
            'Volume': 'sum',
            'Type': 'first'
        }).reset_index()
        
        skew_data['Moneyness_Mid'] = skew_data['Moneyness_Pct'].apply(lambda x: x.mid)
        skew_data = skew_data.dropna()
        
        fig = go.Figure()
        
        # Calls and Puts separately
        calls_data = self.data[self.data['Type'] == 'CALL'] if 'Type' in self.data.columns else self.data
        puts_data = self.data[self.data['Type'] == 'PUT'] if 'Type' in self.data.columns else pd.DataFrame()
        
        if not calls_data.empty:
            fig.add_trace(go.Scatter(
                x=calls_data['Moneyness_Pct'],
                y=calls_data['IV'],
                mode='markers',
                name='Calls',
                marker=dict(color=THEME_CONFIG["primary_color"], size=6)
            ))
            
        if not puts_data.empty:
            fig.add_trace(go.Scatter(
                x=puts_data['Moneyness_Pct'], 
                y=puts_data['IV'],
                mode='markers',
                name='Puts',
                marker=dict(color=THEME_CONFIG["secondary_color"], size=6)
            ))
        
        fig.update_layout(
            title="Volatility Skew Analysis",
            xaxis_title="Moneyness (%)",
            yaxis_title="Implied Volatility",
            plot_bgcolor=THEME_CONFIG["paper_color"],
            paper_bgcolor=THEME_CONFIG["background_color"],
            font=dict(color=THEME_CONFIG["text_color"]),
            height=450
        )
        
        return dcc.Graph(figure=fig)
    
    def create_layout(self, ticker: str) -> html.Div:
        """Create IV Surface module layout"""
        return html.Div([
            # Header
            dbc.Row([
                dbc.Col([
                    dbc.Button("← Dashboard", id={"type": "back-button", "module": "iv_surface"}, color="outline-primary", size="sm")
                ], width="auto"),
                dbc.Col([
                    html.H3(f"📈 IV Term Structure - {ticker}", 
                           style={"color": THEME_CONFIG["primary_color"]})
                ])
            ], align="center", className="mb-4"),
            
            # Controls
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Button("🔄 Update IV Data", 
                                      id="fetch-iv-btn", 
                                      color="primary", 
                                      size="lg")
                        ], width="auto"),
                        dbc.Col([
                            dbc.ButtonGroup([
                                dbc.Button("Term Structure", id="show-terms-btn", color="info", size="sm"),
                                dbc.Button("3D Surface", id="show-3d-btn", color="info", size="sm"), 
                                dbc.Button("Historical", id="show-hist-btn", color="info", size="sm"),
                                dbc.Button("Skew", id="show-skew-btn", color="info", size="sm")
                            ])
                        ], width="auto"),
                        dbc.Col([
                            html.Div(id="iv-status", className="text-muted small")
                        ], className="ms-auto text-end")
                    ], align="center")
                ])
            ], className="mb-4"),
            
            # Summary metrics
            html.Div(id="iv-summary"),
            
            # Main content
            html.Div(id="iv-content", children=[
                self._create_welcome_message(ticker)
            ])
        ])
    
    def _create_welcome_message(self, ticker: str) -> html.Div:
        """Create welcome message"""
        return dbc.Card([
            dbc.CardBody([
                html.H4(f"IV Analysis Ready for {ticker}", className="text-center"),
                html.P("Click 'Update IV Data' to load implied volatility term structure", 
                       className="text-center text-muted"),
                html.Hr(),
                dbc.Row([
                    dbc.Col([
                        html.H6("📊 Available Analysis:"),
                        html.Ul([
                            html.Li("Term Structure Chart"),
                            html.Li("3D Volatility Surface"),
                            html.Li("Historical Watermarks"),
                            html.Li("Volatility Skew Analysis")
                        ])
                    ], md=6),
                    dbc.Col([
                        html.H6("🔍 Key Metrics:"),
                        html.Ul([
                            html.Li("30d/60d ATM IV Levels"),
                            html.Li("Term Structure Slope"),
                            html.Li("Historical Percentiles"),
                            html.Li("Skew Measurements")
                        ])
                    ], md=6)
                ])
            ])
        ], style={"backgroundColor": THEME_CONFIG["paper_color"]})

# Global instance
iv_surface_module = IVSurfaceModule()