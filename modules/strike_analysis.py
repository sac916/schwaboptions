"""
Strike Analysis Module - ConvexValue 'stks' module equivalent
Live bar chart visualization of option levels by strike price
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
from data.module_data_adapter import ModuleDataAdapter
from data.processors import OptionsProcessor
from config import THEME_CONFIG

class StrikeAnalysisModule(BaseModule):
    """Strike-based Options Analysis and Visualization"""
    
    def __init__(self):
        super().__init__(
            module_id="strike_analysis",
            name="Strike Analysis",
            description="Option levels by strike with support/resistance"
        )
        self.data_adapter = ModuleDataAdapter()
        
    def update_data(self, ticker: str, mode: str = "auto", target_date = None, **kwargs):
        """Update strike analysis data using universal data adapter"""
        try:
            # Get data through universal adapter
            data_result = self.data_adapter.get_options_analysis(
                symbol=ticker,
                analysis_type="strike_analysis",
                force_mode=mode,
                target_date=target_date
            )

            if data_result and data_result.get('options_data') is not None:
                self.data = data_result['options_data']
                self.data_quality = data_result.get('data_quality')
                self.data_info = data_result.get('data_info', {})

                if not self.data.empty:
                    # Calculate strike-level metrics
                    raw_data = data_result.get('raw_data', {})
                    self.data = self._calculate_strike_metrics(self.data, raw_data)
                    self._last_updated = datetime.now()
                return self.data
        except Exception as e:
            print(f"Error updating strike data: {e}")
        return None

    def get_data_quality_info(self):
        """Get current data quality information for UI display"""
        if hasattr(self, 'data_quality') and hasattr(self, 'data_info'):
            return {
                'quality': self.data_quality,
                'info': self.data_info
            }
        return None
    
    def _calculate_strike_metrics(self, df, raw_data):
        """Calculate strike-level analysis metrics"""
        # Get underlying price
        underlying_price = raw_data.get('underlying', {}).get('last', 0)
        df['UnderlyingPrice'] = underlying_price
        
        # Strike-level aggregations
        strike_summary = df.groupby('Strike').agg({
            'Volume': 'sum',
            'Open Int': 'sum', 
            'Premium': 'sum',
            'IV': 'mean',
            'UnusualScore': 'max'
        }).reset_index()
        
        # Call/Put split by strike
        call_data = df[df.get('Type', '') == 'CALL'].groupby('Strike').agg({
            'Volume': 'sum',
            'Open Int': 'sum',
            'Premium': 'sum'
        }).add_suffix('_Call').reset_index()
        
        put_data = df[df.get('Type', '') == 'PUT'].groupby('Strike').agg({
            'Volume': 'sum', 
            'Open Int': 'sum',
            'Premium': 'sum'
        }).add_suffix('_Put').reset_index()
        
        # Merge call/put data
        strike_summary = strike_summary.merge(call_data, on='Strike', how='left')
        strike_summary = strike_summary.merge(put_data, on='Strike', how='left')
        strike_summary = strike_summary.fillna(0)
        
        # Calculate derived metrics
        strike_summary['CallPutVolumeRatio'] = (
            strike_summary['Volume_Call'] / (strike_summary['Volume_Put'] + 1)
        )
        strike_summary['CallPutOIRatio'] = (
            strike_summary['Open Int_Call'] / (strike_summary['Open Int_Put'] + 1)  
        )
        strike_summary['NetVolume'] = (
            strike_summary['Volume_Call'] - strike_summary['Volume_Put']
        )
        strike_summary['NetOI'] = (
            strike_summary['Open Int_Call'] - strike_summary['Open Int_Put']
        )
        
        # Distance from underlying
        strike_summary['DistanceFromUnderlying'] = (
            strike_summary['Strike'] - underlying_price
        )
        strike_summary['DistancePct'] = (
            strike_summary['DistanceFromUnderlying'] / underlying_price * 100
        )
        
        # Support/Resistance scoring
        strike_summary['SupportResistanceScore'] = self._calculate_sr_score(
            strike_summary, underlying_price
        )
        
        # Merge back to main dataframe
        df = df.merge(
            strike_summary[['Strike', 'SupportResistanceScore', 'CallPutVolumeRatio']], 
            on='Strike', 
            how='left'
        )
        
        return df
    
    def _calculate_sr_score(self, strike_data, underlying_price):
        """Calculate support/resistance score for each strike"""
        scores = []
        
        for _, row in strike_data.iterrows():
            score = 0
            strike = row['Strike']
            
            # High open interest adds to S/R strength
            oi_percentile = (
                strike_data['Open Int'].rank(pct=True).loc[row.name]
                if 'Open Int' in strike_data.columns else 0
            )
            score += oi_percentile * 30
            
            # High volume adds to current relevance
            volume_percentile = (
                strike_data['Volume'].rank(pct=True).loc[row.name]
                if 'Volume' in strike_data.columns else 0
            )
            score += volume_percentile * 20
            
            # Distance from current price (closer = more relevant)
            distance_pct = abs(strike - underlying_price) / underlying_price * 100
            if distance_pct < 2:  # Within 2%
                score += 25
            elif distance_pct < 5:  # Within 5%
                score += 15
            elif distance_pct < 10:  # Within 10%
                score += 5
            
            # Round number strikes (psychological levels)
            if strike % 10 == 0:
                score += 10
            elif strike % 5 == 0:
                score += 5
                
            scores.append(min(score, 100))  # Cap at 100
            
        return scores
    
    def create_visualizations(self):
        """Create strike analysis visualizations"""
        if self.data is None or self.data.empty:
            return {}
            
        return {
            "strike_volume_chart": self._create_strike_volume_chart(),
            "strike_oi_chart": self._create_strike_oi_chart(), 
            "call_put_analysis": self._create_call_put_analysis(),
            "support_resistance": self._create_support_resistance_chart()
        }
    
    def _create_strike_volume_chart(self):
        """Create volume by strike bar chart"""
        # Aggregate by strike
        strike_data = self.data.groupby(['Strike', 'Type']).agg({
            'Volume': 'sum',
            'Premium': 'sum'
        }).reset_index()
        
        fig = go.Figure()
        
        # Call volume bars
        calls = strike_data[strike_data['Type'] == 'CALL']
        if not calls.empty:
            fig.add_trace(go.Bar(
                x=calls['Strike'],
                y=calls['Volume'],
                name='Call Volume',
                marker_color=THEME_CONFIG["primary_color"],
                opacity=0.8
            ))
        
        # Put volume bars (negative to show below axis)
        puts = strike_data[strike_data['Type'] == 'PUT']  
        if not puts.empty:
            fig.add_trace(go.Bar(
                x=puts['Strike'],
                y=-puts['Volume'],  # Negative for visual separation
                name='Put Volume',
                marker_color=THEME_CONFIG["secondary_color"],
                opacity=0.8
            ))
        
        # Add underlying price line
        if 'UnderlyingPrice' in self.data.columns:
            underlying = self.data['UnderlyingPrice'].iloc[0]
            fig.add_vline(
                x=underlying, 
                line_dash="dash",
                line_color="white",
                annotation_text=f"Current: ${underlying:.2f}",
                annotation_position="top"
            )
        
        fig.add_hline(y=0, line_color="rgba(255,255,255,0.3)", line_width=1)
        
        fig.update_layout(
            title="Volume by Strike (Calls Above, Puts Below)",
            xaxis_title="Strike Price",
            yaxis_title="Volume",
            plot_bgcolor=THEME_CONFIG["paper_color"],
            paper_bgcolor=THEME_CONFIG["background_color"],
            font=dict(color=THEME_CONFIG["text_color"]),
            height=500,
            bargap=0.1
        )
        
        return dcc.Graph(figure=fig)
    
    def _create_strike_oi_chart(self):
        """Create open interest by strike chart"""
        strike_data = self.data.groupby(['Strike', 'Type']).agg({
            'Open Int': 'sum'
        }).reset_index()
        
        fig = go.Figure()
        
        # Call OI
        calls = strike_data[strike_data['Type'] == 'CALL']
        if not calls.empty:
            fig.add_trace(go.Bar(
                x=calls['Strike'],
                y=calls['Open Int'], 
                name='Call OI',
                marker_color=THEME_CONFIG["primary_color"],
                opacity=0.6
            ))
        
        # Put OI
        puts = strike_data[strike_data['Type'] == 'PUT']
        if not puts.empty:
            fig.add_trace(go.Bar(
                x=puts['Strike'],
                y=-puts['Open Int'],
                name='Put OI',
                marker_color=THEME_CONFIG["secondary_color"],
                opacity=0.6
            ))
        
        # Underlying price
        if 'UnderlyingPrice' in self.data.columns:
            underlying = self.data['UnderlyingPrice'].iloc[0]
            fig.add_vline(
                x=underlying,
                line_dash="dash", 
                line_color="white",
                annotation_text=f"${underlying:.2f}",
                annotation_position="bottom"
            )
        
        fig.add_hline(y=0, line_color="rgba(255,255,255,0.3)", line_width=1)
        
        fig.update_layout(
            title="Open Interest by Strike",
            xaxis_title="Strike Price", 
            yaxis_title="Open Interest",
            plot_bgcolor=THEME_CONFIG["paper_color"],
            paper_bgcolor=THEME_CONFIG["background_color"],
            font=dict(color=THEME_CONFIG["text_color"]),
            height=500
        )
        
        return dcc.Graph(figure=fig)
    
    def _create_call_put_analysis(self):
        """Create call/put ratio analysis"""
        if 'CallPutVolumeRatio' not in self.data.columns:
            return html.Div("No call/put ratio data available")
        
        # Group by strike for ratios
        ratio_data = self.data.groupby('Strike').agg({
            'CallPutVolumeRatio': 'first',
            'Volume': 'sum'
        }).reset_index()
        
        fig = go.Figure()
        
        # Call/Put ratio line
        fig.add_trace(go.Scatter(
            x=ratio_data['Strike'],
            y=ratio_data['CallPutVolumeRatio'],
            mode='lines+markers',
            name='Call/Put Volume Ratio',
            line=dict(color=THEME_CONFIG["accent_color"], width=3),
            marker=dict(size=8)
        ))
        
        # Add horizontal lines for key levels
        fig.add_hline(y=1, line_dash="dash", line_color="white", 
                     annotation_text="Equal C/P")
        fig.add_hline(y=2, line_dash="dot", line_color=THEME_CONFIG["primary_color"],
                     annotation_text="2:1 Bullish")
        fig.add_hline(y=0.5, line_dash="dot", line_color=THEME_CONFIG["secondary_color"],
                     annotation_text="1:2 Bearish")
        
        # Underlying price
        if 'UnderlyingPrice' in self.data.columns:
            underlying = self.data['UnderlyingPrice'].iloc[0]
            fig.add_vline(x=underlying, line_dash="dash", line_color="yellow")
        
        fig.update_layout(
            title="Call/Put Volume Ratio by Strike",
            xaxis_title="Strike Price",
            yaxis_title="Call/Put Ratio",
            plot_bgcolor=THEME_CONFIG["paper_color"],
            paper_bgcolor=THEME_CONFIG["background_color"],
            font=dict(color=THEME_CONFIG["text_color"]),
            height=450
        )
        
        return dcc.Graph(figure=fig)
    
    def _create_support_resistance_chart(self):
        """Create support/resistance level chart"""
        if 'SupportResistanceScore' not in self.data.columns:
            return html.Div("No support/resistance data available")
        
        # Get unique strikes with S/R scores
        sr_data = self.data.groupby('Strike').agg({
            'SupportResistanceScore': 'first',
            'Volume': 'sum',
            'Open Int': 'sum'
        }).reset_index()
        
        # Only show significant levels (score > 20)
        significant_levels = sr_data[sr_data['SupportResistanceScore'] > 20]
        
        fig = go.Figure()
        
        # S/R strength bars
        fig.add_trace(go.Bar(
            x=significant_levels['Strike'],
            y=significant_levels['SupportResistanceScore'],
            name='S/R Strength',
            marker=dict(
                color=significant_levels['SupportResistanceScore'],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="S/R Score")
            )
        ))
        
        # Underlying price
        if 'UnderlyingPrice' in self.data.columns:
            underlying = self.data['UnderlyingPrice'].iloc[0]
            fig.add_vline(
                x=underlying,
                line_dash="dash",
                line_color="red",
                line_width=3,
                annotation_text=f"Current: ${underlying:.2f}",
                annotation_position="top"
            )
            
            # Add price projection zones
            fig.add_vrect(
                x0=underlying * 0.98, x1=underlying * 1.02,
                fillcolor="rgba(255,255,0,0.1)",
                annotation_text="2% Zone", annotation_position="top left"
            )
        
        fig.update_layout(
            title="Support/Resistance Levels Analysis",
            xaxis_title="Strike Price",
            yaxis_title="S/R Strength Score",
            plot_bgcolor=THEME_CONFIG["paper_color"],
            paper_bgcolor=THEME_CONFIG["background_color"],
            font=dict(color=THEME_CONFIG["text_color"]),
            height=500
        )
        
        return dcc.Graph(figure=fig)
    
    def _create_strike_summary(self):
        """Create strike analysis summary stats"""
        if self.data.empty:
            return html.Div("No data available")
        
        # Key metrics
        total_volume = self.data.get('Volume', pd.Series([0])).sum()
        total_oi = self.data.get('Open Int', pd.Series([0])).sum()
        call_volume = self.data[self.data.get('Type', '') == 'CALL'].get('Volume', pd.Series([0])).sum()
        put_volume = self.data[self.data.get('Type', '') == 'PUT'].get('Volume', pd.Series([0])).sum()
        
        call_put_ratio = call_volume / max(put_volume, 1)
        
        # Find max activity strikes
        strike_activity = self.data.groupby('Strike')['Volume'].sum().sort_values(ascending=False)
        top_strike = strike_activity.index[0] if len(strike_activity) > 0 else 0
        
        return dbc.Row([
            dbc.Col([
                html.H6("Total Volume"),
                html.H4(f"{int(total_volume):,}", className="text-primary")
            ], md=3),
            dbc.Col([
                html.H6("Call/Put Ratio"),
                html.H4(f"{call_put_ratio:.2f}", className="text-info")
            ], md=3),
            dbc.Col([
                html.H6("Total OI"),
                html.H4(f"{int(total_oi):,}", className="text-success")
            ], md=3),
            dbc.Col([
                html.H6("Most Active Strike"),
                html.H4(f"${top_strike:.0f}", className="text-warning")
            ], md=3)
        ])
    
    def create_layout(self, ticker: str) -> html.Div:
        """Create strike analysis layout"""
        return html.Div([
            # Header
            dbc.Row([
                dbc.Col([
                    dbc.Button("← Dashboard", id={"type": "back-button", "module": "strike_analysis"}, color="outline-primary", size="sm")
                ], width="auto"),
                dbc.Col([
                    html.H3(f"📊 Strike Analysis - {ticker}",
                           id="strike-analysis-header",
                           style={"color": THEME_CONFIG["primary_color"]})
                ])
            ], align="center", className="mb-4"),
            
            # Controls
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Button("🔄 Update Analysis", 
                                      id="update-strikes-btn",
                                      color="primary",
                                      size="lg")
                        ], width="auto"),
                        dbc.Col([
                            dbc.ButtonGroup([
                                dbc.Button("Volume", id="show-strike-vol-btn", color="info", size="sm"),
                                dbc.Button("Open Interest", id="show-strike-oi-btn", color="info", size="sm"),
                                dbc.Button("C/P Ratio", id="show-cp-ratio-btn", color="info", size="sm"),
                                dbc.Button("S/R Levels", id="show-sr-btn", color="info", size="sm")
                            ])
                        ], width="auto"),
                        dbc.Col([
                            html.Div(id="strike-status", className="text-muted small")
                        ], className="ms-auto text-end")
                    ], align="center")
                ])
            ], className="mb-4"),
            
            # Summary stats
            dbc.Card([
                dbc.CardBody([
                    html.H5("Strike Activity Summary", className="mb-3"),
                    html.Div(id="strike-summary")
                ])
            ], className="mb-4"),
            
            # Main content
            html.Div(id="strike-content", children=[
                self._create_welcome_message(ticker)
            ])
        ])
    
    def _create_welcome_message(self, ticker: str) -> html.Div:
        """Create welcome message"""
        return dbc.Card([
            dbc.CardBody([
                html.H4(f"Strike Analysis Ready for {ticker}", className="text-center"),
                html.P("Comprehensive strike-level options analysis with S/R levels", 
                       className="text-center text-muted"),
                html.Hr(),
                dbc.Row([
                    dbc.Col([
                        html.H6("📊 Analysis Types:"),
                        html.Ul([
                            html.Li("Volume by Strike"),
                            html.Li("Open Interest Distribution"),
                            html.Li("Call/Put Ratio Analysis"),
                            html.Li("Support/Resistance Levels")
                        ])
                    ], md=6),
                    dbc.Col([
                        html.H6("🎯 Key Features:"),
                        html.Ul([
                            html.Li("Interactive bar charts"),
                            html.Li("Current price overlay"),
                            html.Li("Psychological level detection"),
                            html.Li("Activity hotspot identification")
                        ])
                    ], md=6)
                ])
            ])
        ], style={"backgroundColor": THEME_CONFIG["paper_color"]})

# Global instance
strike_analysis_module = StrikeAnalysisModule()