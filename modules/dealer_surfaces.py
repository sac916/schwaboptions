"""
3D Dealer Surfaces Module - ConvexValue 'dx' module equivalent
Advanced 3D dealer delta and gamma positioning analysis
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
from data.schwab_client import schwab_client
from data.processors import OptionsProcessor
from config import THEME_CONFIG

class DealerSurfacesModule(BaseModule):
    """3D Dealer Delta and Gamma Surface Analysis"""
    
    def __init__(self):
        super().__init__(
            module_id="dealer_surfaces",
            name="3D Dealer Surfaces", 
            description="Advanced 3D dealer delta and gamma positioning analysis"
        )
        self.dealer_history = []  # Store historical dealer positioning
        self.current_spot = None
        
    def update_data(self, ticker: str, **kwargs):
        """Update dealer surface data with advanced calculations"""
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
                
                # Calculate dealer positioning metrics
                if not self.data.empty:
                    self.data = self._calculate_dealer_metrics()
                    
                    # Store historical dealer positioning
                    dealer_snapshot = self._calculate_dealer_snapshot()
                    self.dealer_history.append({
                        'timestamp': datetime.now(),
                        'ticker': ticker,
                        **dealer_snapshot
                    })
                    
                    # Keep only last 100 data points
                    if len(self.dealer_history) > 100:
                        self.dealer_history = self.dealer_history[-100:]
                
                return self.data
        except Exception as e:
            print(f"Error updating dealer surface data: {e}")
        return None
    
    def _calculate_dealer_metrics(self):
        """Calculate advanced dealer positioning metrics"""
        if self.data.empty:
            return self.data
            
        data = self.data.copy()
        
        # Estimate current spot price from option strikes
        self.current_spot = self._estimate_spot_price(data)
        
        # Calculate moneyness
        data['Moneyness'] = data['Strike'] / self.current_spot
        data['Log_Moneyness'] = np.log(data['Moneyness'])
        
        # Black-Scholes Greeks approximations
        data = self._calculate_greeks(data)
        
        # Dealer positioning estimates
        data = self._estimate_dealer_positioning(data)
        
        # Market maker inventory estimates  
        data = self._estimate_mm_inventory(data)
        
        return data
    
    def _estimate_spot_price(self, data):
        """Estimate current spot price from options data"""
        if 'Last Price' in data.columns and not data['Last Price'].isna().all():
            # Use put-call parity to estimate spot
            calls = data[data['Type'] == 'CALL'].copy() if 'Type' in data.columns else data
            puts = data[data['Type'] == 'PUT'].copy() if 'Type' in data.columns else pd.DataFrame()
            
            if not calls.empty and not puts.empty:
                # Find matching strikes
                common_strikes = set(calls['Strike']).intersection(set(puts['Strike']))
                if common_strikes:
                    strike = list(common_strikes)[0]
                    call_price = calls[calls['Strike'] == strike]['Last Price'].iloc[0]
                    put_price = puts[puts['Strike'] == strike]['Last Price'].iloc[0]
                    # S = C - P + K (simplified, ignoring risk-free rate)
                    return call_price - put_price + strike
        
        # Fallback: use median strike as approximation
        return data['Strike'].median()
    
    def _calculate_greeks(self, data):
        """Calculate Black-Scholes Greeks approximations"""
        # Simplified Greeks calculation for dealer analysis
        # In practice, would use full Black-Scholes model
        
        S = self.current_spot  # Current spot price
        r = 0.05  # Risk-free rate (5% assumption)
        
        data['Delta'] = 0.0
        data['Gamma'] = 0.0
        data['Theta'] = 0.0
        data['Vega'] = 0.0
        
        for idx, row in data.iterrows():
            K = row['Strike']
            T = max(row['DTE'] / 365, 0.001)  # Time to expiration in years
            sigma = max(row['IV'], 0.01)  # Implied volatility
            
            # Moneyness
            m = S / K
            
            if row['Type'] == 'CALL':
                # Simplified call delta approximation
                if m > 1.05:  # Deep ITM
                    delta = 0.95
                elif m < 0.95:  # Deep OTM  
                    delta = 0.05
                else:  # Near ATM
                    delta = 0.5 + (m - 1) * 2
                    
                data.at[idx, 'Delta'] = max(0, min(1, delta))
                
            else:  # PUT
                # Simplified put delta approximation
                if m > 1.05:  # Deep OTM
                    delta = -0.05
                elif m < 0.95:  # Deep ITM
                    delta = -0.95
                else:  # Near ATM
                    delta = -0.5 + (1 - m) * 2
                    
                data.at[idx, 'Delta'] = max(-1, min(0, delta))
            
            # Simplified gamma (highest near ATM)
            gamma = np.exp(-((np.log(m))**2) / (2 * (sigma * np.sqrt(T))**2))
            data.at[idx, 'Gamma'] = gamma * 0.1  # Scale factor
            
            # Simplified vega (positive for both calls and puts)
            vega = S * np.sqrt(T) * gamma * 0.01
            data.at[idx, 'Vega'] = vega
            
            # Simplified theta (negative time decay)
            theta = -S * gamma * sigma / (2 * np.sqrt(T)) * 0.01
            data.at[idx, 'Theta'] = theta
        
        return data
    
    def _estimate_dealer_positioning(self, data):
        """Estimate dealer delta and gamma positioning"""
        # Dealers typically short options (negative gamma)
        # High volume/OI suggests dealer activity
        
        data['Dealer_Delta_Exposure'] = 0.0
        data['Dealer_Gamma_Exposure'] = 0.0
        data['Hedging_Pressure'] = 0.0
        
        for idx, row in data.iterrows():
            volume = row.get('Volume', 0)
            open_int = row.get('Open Int', 0)
            delta = row['Delta']
            gamma = row['Gamma']
            
            # Estimate dealer short positioning (they sell options)
            # Higher volume/OI suggests more dealer short interest
            activity_factor = np.log1p(volume + open_int)
            
            # Dealers are typically short options (negative positioning)
            dealer_delta = -delta * activity_factor * 0.1
            dealer_gamma = -gamma * activity_factor * 0.1
            
            # Hedging pressure increases with dealer gamma exposure
            hedging_pressure = abs(dealer_gamma) * activity_factor
            
            data.at[idx, 'Dealer_Delta_Exposure'] = dealer_delta
            data.at[idx, 'Dealer_Gamma_Exposure'] = dealer_gamma
            data.at[idx, 'Hedging_Pressure'] = hedging_pressure
        
        return data
    
    def _estimate_mm_inventory(self, data):
        """Estimate market maker inventory levels"""
        # Market makers adjust quotes based on inventory
        # High inventory = wider spreads, lower quotes
        
        data['MM_Inventory_Level'] = 0.0
        data['MM_Skew_Adjustment'] = 0.0
        
        # Group by expiration to analyze term structure
        for expiry in data['Expiry'].unique():
            exp_data = data[data['Expiry'] == expiry].copy()
            
            # Calculate put/call volume ratio as inventory indicator
            calls = exp_data[exp_data['Type'] == 'CALL'] if 'Type' in exp_data.columns else exp_data
            puts = exp_data[exp_data['Type'] == 'PUT'] if 'Type' in exp_data.columns else pd.DataFrame()
            
            if not calls.empty and not puts.empty:
                call_vol = calls['Volume'].sum()
                put_vol = puts['Volume'].sum()
                
                if call_vol + put_vol > 0:
                    pc_ratio = put_vol / (call_vol + put_vol)
                    
                    # High put/call ratio suggests put inventory buildup
                    for idx in exp_data.index:
                        if data.at[idx, 'Type'] == 'PUT':
                            inventory = pc_ratio - 0.5  # Neutral is 50/50
                        else:
                            inventory = 0.5 - pc_ratio
                            
                        data.at[idx, 'MM_Inventory_Level'] = inventory
                        data.at[idx, 'MM_Skew_Adjustment'] = inventory * 0.02  # 2% max adjustment
        
        return data
    
    def _calculate_dealer_snapshot(self):
        """Calculate current dealer positioning snapshot"""
        if self.data.empty:
            return {}
            
        return {
            'total_dealer_delta': self.data['Dealer_Delta_Exposure'].sum(),
            'total_dealer_gamma': self.data['Dealer_Gamma_Exposure'].sum(),
            'avg_hedging_pressure': self.data['Hedging_Pressure'].mean(),
            'max_gamma_strike': self.data.loc[self.data['Dealer_Gamma_Exposure'].abs().idxmax(), 'Strike'] if len(self.data) > 0 else 0,
            'total_volume': self.data['Volume'].sum(),
            'spot_price': self.current_spot
        }
    
    def _validate_and_clean_dealer_data(self):
        """Validate and clean data for 3D surface plotting"""
        if self.data is None or self.data.empty:
            return pd.DataFrame()
        
        clean_data = self.data.copy()
        
        # Filter realistic ranges
        clean_data = clean_data[
            (clean_data['DTE'] >= 1) & 
            (clean_data['DTE'] <= 365) &
            (clean_data['Strike'] > 0) &
            (clean_data['Dealer_Gamma_Exposure'].notna()) &
            (clean_data['Dealer_Delta_Exposure'].notna())
        ]
        
        # Remove extreme outliers
        for col in ['Dealer_Delta_Exposure', 'Dealer_Gamma_Exposure', 'Hedging_Pressure']:
            if col in clean_data.columns and len(clean_data) > 10:
                q99 = clean_data[col].quantile(0.99)
                q01 = clean_data[col].quantile(0.01)
                clean_data = clean_data[
                    (clean_data[col] >= q01) & (clean_data[col] <= q99)
                ]
        
        # Ensure sufficient data for surface
        if len(clean_data) < 10:
            print(f"Warning: Only {len(clean_data)} data points for dealer surface")
            
        return clean_data
    
    def create_visualizations(self):
        """Create dealer surface visualizations"""
        if self.data is None or self.data.empty:
            return {}
            
        return {
            "dealer_delta_surface": self._create_delta_surface_3d(),
            "dealer_gamma_surface": self._create_gamma_surface_3d(),
            "combined_surface": self._create_combined_3d_surface(),
            "hedging_pressure": self._create_hedging_pressure_chart(),
            "dealer_flow": self._create_dealer_flow_chart(),
            "positioning_history": self._create_positioning_history(),
            "risk_scenarios": self._create_risk_scenarios(),
            "interactive_surface": self._create_interactive_3d_surface()
        }
    
    def _create_delta_surface_3d(self):
        """Create 3D dealer delta exposure surface"""
        clean_data = self._validate_and_clean_dealer_data()
        
        if clean_data.empty or len(clean_data) < 10:
            return html.Div([
                dbc.Alert("Insufficient data for dealer delta surface. Need at least 10 option contracts.", 
                         color="warning")
            ])
        
        try:
            # Prepare data for 3D surface
            strikes = clean_data['Strike'].values
            dtes = clean_data['DTE'].values
            dealer_deltas = clean_data['Dealer_Delta_Exposure'].values
            
            # Create uniform grid
            strike_min, strike_max = strikes.min(), strikes.max()
            dte_min, dte_max = dtes.min(), dtes.max()
            
            grid_strikes = np.linspace(strike_min, strike_max, 40)
            grid_dtes = np.linspace(dte_min, dte_max, 40)
            strike_grid, dte_grid = np.meshgrid(grid_strikes, grid_dtes)
            
            # Interpolate dealer delta surface
            delta_grid = griddata(
                points=(strikes, dtes),
                values=dealer_deltas,
                xi=(strike_grid, dte_grid),
                method='cubic',
                fill_value=0
            )
            
            if np.isnan(delta_grid).all():
                delta_grid = griddata(
                    points=(strikes, dtes),
                    values=dealer_deltas,
                    xi=(strike_grid, dte_grid),
                    method='linear',
                    fill_value=0
                )
            
            delta_grid = np.nan_to_num(delta_grid, nan=0)
            
            # Create 3D dealer delta surface
            fig = go.Figure(data=[
                go.Surface(
                    z=delta_grid,
                    x=grid_dtes,
                    y=grid_strikes,
                    colorscale='RdBu',  # Red for short, Blue for long delta
                    name='Dealer Delta Surface',
                    hovertemplate='<b>Strike:</b> %{y:.0f}<br>' +
                                '<b>DTE:</b> %{x:.0f}<br>' + 
                                '<b>Dealer Delta:</b> %{z:.3f}<br>' +
                                '<extra></extra>',
                    colorbar=dict(
                        title="Dealer Delta Exposure",
                        titlefont=dict(color=THEME_CONFIG["text_color"]),
                        tickfont=dict(color=THEME_CONFIG["text_color"])
                    )
                )
            ])
            
            # Add current spot price indicator
            if self.current_spot:
                fig.add_trace(go.Scatter3d(
                    x=[dte_min, dte_max],
                    y=[self.current_spot, self.current_spot],
                    z=[0, 0],
                    mode='lines',
                    line=dict(color='yellow', width=8),
                    name=f'Spot Price: ${self.current_spot:.0f}',
                    showlegend=True
                ))
            
            # Professional layout
            fig.update_layout(
                title='3D Dealer Delta Exposure Surface',
                scene=dict(
                    xaxis_title='Days to Expiration',
                    yaxis_title='Strike Price',
                    zaxis_title='Dealer Delta Exposure',
                    bgcolor=THEME_CONFIG["background_color"],
                    xaxis=dict(color=THEME_CONFIG["text_color"]),
                    yaxis=dict(color=THEME_CONFIG["text_color"]),
                    zaxis=dict(color=THEME_CONFIG["text_color"]),
                    camera=dict(
                        eye=dict(x=1.5, y=1.5, z=1.2)
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
                dbc.Alert(f"Error creating dealer delta surface: {str(e)}", color="danger")
            ])
    
    def _create_gamma_surface_3d(self):
        """Create 3D dealer gamma exposure surface"""
        clean_data = self._validate_and_clean_dealer_data()
        
        if clean_data.empty or len(clean_data) < 10:
            return html.Div([
                dbc.Alert("Insufficient data for dealer gamma surface.", color="warning")
            ])
        
        try:
            strikes = clean_data['Strike'].values
            dtes = clean_data['DTE'].values
            dealer_gammas = clean_data['Dealer_Gamma_Exposure'].values
            
            # Create uniform grid
            strike_min, strike_max = strikes.min(), strikes.max()
            dte_min, dte_max = dtes.min(), dtes.max()
            
            grid_strikes = np.linspace(strike_min, strike_max, 40)
            grid_dtes = np.linspace(dte_min, dte_max, 40)
            strike_grid, dte_grid = np.meshgrid(grid_strikes, grid_dtes)
            
            # Interpolate gamma surface
            gamma_grid = griddata(
                points=(strikes, dtes),
                values=dealer_gammas,
                xi=(strike_grid, dte_grid),
                method='cubic',
                fill_value=0
            )
            
            if np.isnan(gamma_grid).all():
                gamma_grid = griddata(
                    points=(strikes, dtes),
                    values=dealer_gammas,
                    xi=(strike_grid, dte_grid),
                    method='linear',
                    fill_value=0
                )
            
            gamma_grid = np.nan_to_num(gamma_grid, nan=0)
            
            # Create 3D gamma surface
            fig = go.Figure(data=[
                go.Surface(
                    z=gamma_grid,
                    x=grid_dtes,
                    y=grid_strikes,
                    colorscale='Viridis',  # Professional gamma color scale
                    name='Dealer Gamma Surface',
                    hovertemplate='<b>Strike:</b> %{y:.0f}<br>' +
                                '<b>DTE:</b> %{x:.0f}<br>' +
                                '<b>Dealer Gamma:</b> %{z:.4f}<br>' +
                                '<extra></extra>',
                    colorbar=dict(
                        title="Dealer Gamma Exposure",
                        titlefont=dict(color=THEME_CONFIG["text_color"]),
                        tickfont=dict(color=THEME_CONFIG["text_color"])
                    )
                )
            ])
            
            # Add spot price reference
            if self.current_spot:
                fig.add_trace(go.Scatter3d(
                    x=[dte_min, dte_max],
                    y=[self.current_spot, self.current_spot],
                    z=[0, 0],
                    mode='lines',
                    line=dict(color='yellow', width=8),
                    name=f'Spot: ${self.current_spot:.0f}',
                    showlegend=True
                ))
            
            fig.update_layout(
                title='3D Dealer Gamma Exposure Surface',
                scene=dict(
                    xaxis_title='Days to Expiration',
                    yaxis_title='Strike Price',
                    zaxis_title='Dealer Gamma Exposure',
                    bgcolor=THEME_CONFIG["background_color"],
                    xaxis=dict(color=THEME_CONFIG["text_color"]),
                    yaxis=dict(color=THEME_CONFIG["text_color"]),
                    zaxis=dict(color=THEME_CONFIG["text_color"]),
                    camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))
                ),
                plot_bgcolor=THEME_CONFIG["paper_color"],
                paper_bgcolor=THEME_CONFIG["background_color"],
                font=dict(color=THEME_CONFIG["text_color"], size=12),
                height=700
            )
            
            return dcc.Graph(figure=fig, style={'height': '700px'})
            
        except Exception as e:
            return html.Div([
                dbc.Alert(f"Error creating gamma surface: {str(e)}", color="danger")
            ])
    
    def _create_hedging_pressure_chart(self):
        """Create hedging pressure analysis chart"""
        if self.data.empty:
            return html.Div("No data available")
        
        # Group by strike to show hedging pressure levels
        pressure_data = self.data.groupby('Strike').agg({
            'Hedging_Pressure': 'mean',
            'Volume': 'sum',
            'Open Int': 'sum'
        }).reset_index().sort_values('Strike')
        
        fig = go.Figure()
        
        # Hedging pressure bars
        fig.add_trace(go.Bar(
            x=pressure_data['Strike'],
            y=pressure_data['Hedging_Pressure'],
            name='Hedging Pressure',
            marker_color=THEME_CONFIG["secondary_color"],
            opacity=0.7
        ))
        
        # Add spot price line
        if self.current_spot:
            fig.add_vline(
                x=self.current_spot,
                line_dash="dash",
                line_color="yellow",
                annotation_text=f"Spot: ${self.current_spot:.0f}",
                annotation_position="top"
            )
        
        fig.update_layout(
            title="Dealer Hedging Pressure by Strike",
            xaxis_title="Strike Price",
            yaxis_title="Hedging Pressure",
            plot_bgcolor=THEME_CONFIG["paper_color"],
            paper_bgcolor=THEME_CONFIG["background_color"],
            font=dict(color=THEME_CONFIG["text_color"]),
            height=400
        )
        
        return dcc.Graph(figure=fig)
    
    def _create_dealer_flow_chart(self):
        """Create dealer flow analysis chart"""
        if self.data.empty:
            return html.Div("No data available")
        
        # Analyze dealer flow by call/put and moneyness
        flow_data = self.data.copy()
        flow_data['Moneyness_Bucket'] = pd.cut(
            flow_data['Moneyness'], 
            bins=[0, 0.95, 1.05, 2.0], 
            labels=['OTM', 'ATM', 'ITM']
        )
        
        flow_summary = flow_data.groupby(['Type', 'Moneyness_Bucket']).agg({
            'Dealer_Delta_Exposure': 'sum',
            'Volume': 'sum'
        }).reset_index()
        
        fig = go.Figure()
        
        # Dealer delta exposure by type and moneyness
        for option_type in ['CALL', 'PUT']:
            type_data = flow_summary[flow_summary['Type'] == option_type]
            if not type_data.empty:
                fig.add_trace(go.Bar(
                    x=type_data['Moneyness_Bucket'],
                    y=type_data['Dealer_Delta_Exposure'],
                    name=f'{option_type} Dealer Exposure',
                    marker_color=THEME_CONFIG["primary_color"] if option_type == 'CALL' else THEME_CONFIG["secondary_color"]
                ))
        
        fig.update_layout(
            title="Dealer Flow Analysis by Option Type & Moneyness",
            xaxis_title="Moneyness",
            yaxis_title="Dealer Delta Exposure",
            barmode='group',
            plot_bgcolor=THEME_CONFIG["paper_color"],
            paper_bgcolor=THEME_CONFIG["background_color"],
            font=dict(color=THEME_CONFIG["text_color"]),
            height=400
        )
        
        return dcc.Graph(figure=fig)
    
    def _create_positioning_history(self):
        """Create dealer positioning history chart"""
        if len(self.dealer_history) < 2:
            return html.Div("Insufficient historical data - keep app running to accumulate dealer positioning history")
        
        hist_df = pd.DataFrame(self.dealer_history)
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=['Dealer Delta History', 'Dealer Gamma History'],
            vertical_spacing=0.1
        )
        
        # Delta history
        fig.add_trace(
            go.Scatter(
                x=hist_df['timestamp'],
                y=hist_df['total_dealer_delta'],
                mode='lines+markers',
                name='Total Dealer Delta',
                line=dict(color=THEME_CONFIG["primary_color"])
            ),
            row=1, col=1
        )
        
        # Gamma history
        fig.add_trace(
            go.Scatter(
                x=hist_df['timestamp'],
                y=hist_df['total_dealer_gamma'],
                mode='lines+markers',
                name='Total Dealer Gamma',
                line=dict(color=THEME_CONFIG["secondary_color"])
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            title="Historical Dealer Positioning",
            plot_bgcolor=THEME_CONFIG["paper_color"],
            paper_bgcolor=THEME_CONFIG["background_color"],
            font=dict(color=THEME_CONFIG["text_color"]),
            height=600
        )
        
        return dcc.Graph(figure=fig)

    def _create_combined_3d_surface(self):
        """Create combined 3D surface showing both delta and gamma"""
        clean_data = self._validate_and_clean_dealer_data()

        if clean_data.empty or len(clean_data) < 10:
            return html.Div([
                dbc.Alert("Insufficient data for combined 3D surface", color="warning")
            ])

        try:
            # Prepare data for 3D surface
            strikes = clean_data['Strike'].values
            dtes = clean_data['DTE'].values
            dealer_delta = clean_data['Dealer_Delta'].values
            dealer_gamma = clean_data['Dealer_Gamma'].values

            # Create grid for interpolation
            strike_grid = np.linspace(strikes.min(), strikes.max(), 30)
            dte_grid = np.linspace(dtes.min(), dtes.max(), 20)

            X, Y = np.meshgrid(strike_grid, dte_grid)

            # Interpolate delta and gamma surfaces
            points = np.column_stack((strikes, dtes))
            Z_delta = griddata(points, dealer_delta, (X, Y), method='cubic', fill_value=0)
            Z_gamma = griddata(points, dealer_gamma, (X, Y), method='cubic', fill_value=0)

            # Create subplots for side-by-side 3D surfaces
            fig = make_subplots(
                rows=1, cols=2,
                specs=[[{"type": "surface"}, {"type": "surface"}]],
                subplot_titles=["Dealer Delta Exposure", "Dealer Gamma Exposure"],
                horizontal_spacing=0.1
            )

            # Add delta surface
            fig.add_trace(
                go.Surface(
                    x=X, y=Y, z=Z_delta,
                    colorscale='RdYlBu_r',
                    name='Delta',
                    showscale=True,
                    colorbar=dict(x=0.45, thickness=10)
                ),
                row=1, col=1
            )

            # Add gamma surface
            fig.add_trace(
                go.Surface(
                    x=X, y=Y, z=Z_gamma,
                    colorscale='Plasma',
                    name='Gamma',
                    showscale=True,
                    colorbar=dict(x=1.0, thickness=10)
                ),
                row=1, col=2
            )

            # Add spot price indicator planes
            if self.current_spot:
                # Delta surface spot line
                fig.add_trace(
                    go.Scatter3d(
                        x=[self.current_spot] * len(dte_grid),
                        y=dte_grid,
                        z=np.interp(dte_grid, dte_grid, Z_delta[:, np.argmin(np.abs(strike_grid - self.current_spot))]),
                        mode='lines',
                        line=dict(color='yellow', width=8),
                        name=f'Spot: ${self.current_spot:.0f}',
                        showlegend=True
                    ),
                    row=1, col=1
                )

            fig.update_layout(
                title="Combined 3D Dealer Exposure Surfaces",
                template="plotly_dark",
                paper_bgcolor=THEME_CONFIG["paper_color"],
                plot_bgcolor=THEME_CONFIG["background_color"],
                height=700,
                scene=dict(
                    xaxis_title="Strike Price ($)",
                    yaxis_title="Days to Expiration",
                    zaxis_title="Delta Exposure",
                    camera=dict(eye=dict(x=1.5, y=1.5, z=1.5))
                ),
                scene2=dict(
                    xaxis_title="Strike Price ($)",
                    yaxis_title="Days to Expiration",
                    zaxis_title="Gamma Exposure",
                    camera=dict(eye=dict(x=1.5, y=1.5, z=1.5))
                )
            )

            return dcc.Graph(figure=fig, style={"height": "700px"})

        except Exception as e:
            return html.Div([
                dbc.Alert(f"Error creating combined 3D surface: {str(e)}", color="danger")
            ])

    def _create_risk_scenarios(self):
        """Create risk scenario analysis visualization"""
        clean_data = self._validate_and_clean_dealer_data()

        if clean_data.empty:
            return html.Div([
                dbc.Alert("No data available for risk scenarios", color="warning")
            ])

        try:
            # Calculate risk scenarios
            current_spot = self.current_spot or clean_data['Strike'].median()

            # Define scenario moves
            moves = [-0.05, -0.03, -0.01, 0, 0.01, 0.03, 0.05]  # ±5% to ±1%
            scenario_prices = [current_spot * (1 + move) for move in moves]

            scenarios = []
            for price in scenario_prices:
                # Calculate dealer PnL impact for each scenario
                delta_pnl = clean_data['Dealer_Delta'].sum() * (price - current_spot)
                gamma_pnl = 0.5 * clean_data['Dealer_Gamma'].sum() * (price - current_spot) ** 2
                total_pnl = delta_pnl + gamma_pnl

                scenarios.append({
                    'Spot_Price': price,
                    'Move': f"{((price/current_spot - 1) * 100):+.1f}%",
                    'Delta_PnL': delta_pnl,
                    'Gamma_PnL': gamma_pnl,
                    'Total_PnL': total_pnl
                })

            df_scenarios = pd.DataFrame(scenarios)

            # Create risk scenario visualization
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=[
                    "Total P&L by Scenario",
                    "Delta vs Gamma Contribution",
                    "Risk Heatmap",
                    "Dealer Exposure Profile"
                ],
                specs=[
                    [{"type": "xy"}, {"type": "xy"}],
                    [{"type": "xy"}, {"type": "xy"}]
                ]
            )

            # Total P&L scenario
            fig.add_trace(
                go.Scatter(
                    x=df_scenarios['Move'],
                    y=df_scenarios['Total_PnL'],
                    mode='lines+markers',
                    line=dict(color=THEME_CONFIG["primary_color"], width=3),
                    marker=dict(size=8),
                    name='Total P&L'
                ),
                row=1, col=1
            )

            # Delta vs Gamma breakdown
            fig.add_trace(
                go.Bar(
                    x=df_scenarios['Move'],
                    y=df_scenarios['Delta_PnL'],
                    name='Delta P&L',
                    marker_color=THEME_CONFIG["accent_color"]
                ),
                row=1, col=2
            )
            fig.add_trace(
                go.Bar(
                    x=df_scenarios['Move'],
                    y=df_scenarios['Gamma_PnL'],
                    name='Gamma P&L',
                    marker_color=THEME_CONFIG["secondary_color"]
                ),
                row=1, col=2
            )

            # Risk heatmap
            risk_matrix = np.array([df_scenarios['Total_PnL'].values]).reshape(1, -1)
            fig.add_trace(
                go.Heatmap(
                    z=risk_matrix,
                    x=df_scenarios['Move'],
                    y=['P&L Impact'],
                    colorscale='RdYlGn',
                    showscale=True
                ),
                row=2, col=1
            )

            # Dealer exposure profile
            strikes_sorted = clean_data.sort_values('Strike')
            fig.add_trace(
                go.Scatter(
                    x=strikes_sorted['Strike'],
                    y=strikes_sorted['Dealer_Delta'].cumsum(),
                    mode='lines',
                    name='Cumulative Delta',
                    line=dict(color=THEME_CONFIG["primary_color"])
                ),
                row=2, col=2
            )

            # Add spot price line
            fig.add_vline(
                x=current_spot,
                line_dash="dash",
                line_color="yellow",
                annotation_text=f"Spot: ${current_spot:.0f}",
                row=2, col=2
            )

            fig.update_layout(
                title="Dealer Risk Scenario Analysis",
                template="plotly_dark",
                paper_bgcolor=THEME_CONFIG["paper_color"],
                plot_bgcolor=THEME_CONFIG["background_color"],
                height=800,
                showlegend=True
            )

            return dcc.Graph(figure=fig, style={"height": "800px"})

        except Exception as e:
            return html.Div([
                dbc.Alert(f"Error creating risk scenarios: {str(e)}", color="danger")
            ])

    def _create_interactive_3d_surface(self):
        """Create interactive 3D surface with animation capabilities"""
        clean_data = self._validate_and_clean_dealer_data()

        if clean_data.empty or len(clean_data) < 10:
            return html.Div([
                dbc.Alert("Insufficient data for interactive 3D surface", color="warning")
            ])

        try:
            # Create animated surface showing evolution over time
            fig = go.Figure()

            # Prepare data for 3D surface
            strikes = clean_data['Strike'].values
            dtes = clean_data['DTE'].values
            dealer_delta = clean_data['Dealer_Delta'].values

            # Create grid
            strike_grid = np.linspace(strikes.min(), strikes.max(), 25)
            dte_grid = np.linspace(dtes.min(), dtes.max(), 15)
            X, Y = np.meshgrid(strike_grid, dte_grid)

            # Interpolate surface
            points = np.column_stack((strikes, dtes))
            Z = griddata(points, dealer_delta, (X, Y), method='cubic', fill_value=0)

            # Main surface
            surface = go.Surface(
                x=X, y=Y, z=Z,
                colorscale='Viridis',
                opacity=0.8,
                name='Dealer Delta Surface',
                contours=dict(
                    x=dict(show=True, color="white", width=2),
                    y=dict(show=True, color="white", width=2),
                    z=dict(show=True, color="white", width=2)
                ),
                lighting=dict(
                    ambient=0.4,
                    diffuse=0.8,
                    specular=0.2
                )
            )

            fig.add_trace(surface)

            # Add contour projections
            fig.add_trace(
                go.Contour(
                    x=strike_grid,
                    y=dte_grid,
                    z=Z,
                    showscale=False,
                    opacity=0.5,
                    contours=dict(coloring='lines'),
                    line=dict(width=1),
                    name='Contour Projection'
                )
            )

            # Add spot price indicator
            if self.current_spot:
                spot_line_z = np.full(len(dte_grid), Z.max() * 1.1)
                fig.add_trace(
                    go.Scatter3d(
                        x=[self.current_spot] * len(dte_grid),
                        y=dte_grid,
                        z=spot_line_z,
                        mode='lines',
                        line=dict(color='yellow', width=10),
                        name=f'Current Spot: ${self.current_spot:.0f}'
                    )
                )

            # Interactive controls
            fig.update_layout(
                title="Interactive 3D Dealer Delta Surface",
                template="plotly_dark",
                paper_bgcolor=THEME_CONFIG["paper_color"],
                plot_bgcolor=THEME_CONFIG["background_color"],
                height=800,
                scene=dict(
                    xaxis_title="Strike Price ($)",
                    yaxis_title="Days to Expiration",
                    zaxis_title="Dealer Delta Exposure",
                    camera=dict(
                        eye=dict(x=1.5, y=1.5, z=1.5),
                        center=dict(x=0, y=0, z=0),
                        up=dict(x=0, y=0, z=1)
                    ),
                    bgcolor=THEME_CONFIG["background_color"],
                    xaxis=dict(
                        backgroundcolor=THEME_CONFIG["paper_color"],
                        gridcolor="gray",
                        showbackground=True
                    ),
                    yaxis=dict(
                        backgroundcolor=THEME_CONFIG["paper_color"],
                        gridcolor="gray",
                        showbackground=True
                    ),
                    zaxis=dict(
                        backgroundcolor=THEME_CONFIG["paper_color"],
                        gridcolor="gray",
                        showbackground=True
                    )
                ),
                updatemenus=[
                    dict(
                        type="buttons",
                        direction="left",
                        buttons=list([
                            dict(label="Rotate",
                                 method="animate",
                                 args=[None, {"frame": {"duration": 500, "redraw": True},
                                            "fromcurrent": True, "transition": {"duration": 300}}]),
                            dict(label="Stop",
                                 method="animate",
                                 args=[[None], {"frame": {"duration": 0, "redraw": True},
                                              "mode": "immediate", "transition": {"duration": 0}}])
                        ]),
                        pad={"r": 10, "t": 87},
                        showactive=False,
                        x=0.011,
                        xanchor="right",
                        y=0,
                        yanchor="top"
                    )
                ]
            )

            return dcc.Graph(figure=fig, style={"height": "800px"})

        except Exception as e:
            return html.Div([
                dbc.Alert(f"Error creating interactive 3D surface: {str(e)}", color="danger")
            ])

    def create_layout(self, ticker: str) -> html.Div:
        """Create dealer surfaces module layout"""
        return html.Div([
            # Header
            dbc.Row([
                dbc.Col([
                    dbc.Button("← Dashboard", id={"type": "back-button", "module": "dealer_surfaces"}, color="outline-primary", size="sm", type="button")
                ], width="auto"),
                dbc.Col([
                    html.H3(f"🎯 3D Dealer Surfaces - {ticker}", 
                           style={"color": THEME_CONFIG["primary_color"]})
                ])
            ], align="center", className="mb-4"),
            
            # Controls
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Button("🔄 Update Dealer Data", 
                                      id="fetch-dealer-btn", 
                                      color="primary", 
                                      size="lg")
                        ], width="auto"),
                        dbc.Col([
                            dbc.ButtonGroup([
                                dbc.Button("Delta Surface", id="show-delta-surf-btn", color="info", size="sm"),
                                dbc.Button("Gamma Surface", id="show-gamma-surf-btn", color="info", size="sm"),
                                dbc.Button("Combined 3D", id="show-combined-surf-btn", color="warning", size="sm"),
                                dbc.Button("Risk Scenarios", id="show-risk-scenarios-btn", color="danger", size="sm"),
                                dbc.Button("Interactive 3D", id="show-interactive-surf-btn", color="success", size="sm"),
                                dbc.Button("History", id="show-hist-btn", color="info", size="sm")
                            ])
                        ], width="auto"),
                        dbc.Col([
                            html.Div(id="dealer-status", className="text-muted small")
                        ], className="ms-auto text-end")
                    ], align="center")
                ])
            ], className="mb-4"),
            
            # Summary metrics
            html.Div(id="dealer-summary"),
            
            # Main content
            html.Div(id="dealer-content", children=[
                self._create_welcome_message(ticker)
            ])
        ])
    
    def _create_welcome_message(self, ticker: str) -> html.Div:
        """Create welcome message"""
        return dbc.Card([
            dbc.CardBody([
                html.H4(f"3D Dealer Analysis Ready for {ticker}", className="text-center"),
                html.P("Click 'Update Dealer Data' to load advanced dealer positioning analysis", 
                       className="text-center text-muted"),
                html.Hr(),
                dbc.Row([
                    dbc.Col([
                        html.H6("📊 Available Analysis:"),
                        html.Ul([
                            html.Li("3D Dealer Delta Surface"),
                            html.Li("3D Dealer Gamma Surface"),
                            html.Li("Hedging Pressure Analysis"),
                            html.Li("Dealer Flow by Moneyness"),
                            html.Li("Historical Positioning")
                        ])
                    ], md=6),
                    dbc.Col([
                        html.H6("🎯 Key Metrics:"),
                        html.Ul([
                            html.Li("Dealer Delta/Gamma Exposure"),
                            html.Li("Market Maker Inventory"),
                            html.Li("Hedging Pressure Levels"),
                            html.Li("Path-of-Least-Resistance"),
                            html.Li("Institutional Flow Analysis")
                        ])
                    ], md=6)
                ])
            ])
        ], style={"backgroundColor": THEME_CONFIG["paper_color"]})

# Global instance
dealer_surfaces_module = DealerSurfacesModule()