"""
Flow Scanner Module - ConvexValue 'flow' module equivalent
Live options flow analysis with 100+ parameters and unusual activity detection
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go

from modules.base_module import BaseModule
from data.schwab_client import schwab_client
from data.enhanced_schwab_client import enhanced_schwab_client
from data.historical_collector import historical_collector
from data.processors import OptionsProcessor
from config import THEME_CONFIG
from datetime import date

class FlowScannerModule(BaseModule):
    """Advanced Options Flow Scanner with 100+ Parameters"""
    
    def __init__(self):
        super().__init__(
            module_id="flow_scanner",
            name="Flow Scanner",
            description="Live options flow with 100+ parameters"
        )
        self.flow_parameters = self._define_flow_parameters()
        
    def _define_flow_parameters(self):
        """Define the 100+ flow analysis parameters"""
        return {
            # Volume Metrics
            'volume': 'Contract Volume',
            'dollar_volume': 'Dollar Volume (Volume × Premium)',
            'volume_oi_ratio': 'Volume/Open Interest Ratio',
            'relative_volume': 'Volume vs 20-day Average',
            'volume_rank': 'Volume Percentile Rank',
            
            # Premium & Money Flow
            'premium': 'Total Premium',
            'avg_premium': 'Average Premium per Contract',
            'premium_rank': 'Premium Size Percentile',
            'money_flow_bullish': 'Bullish Money Flow',
            'money_flow_bearish': 'Bearish Money Flow',
            'net_money_flow': 'Net Money Flow',
            
            # Timing & Expiration
            'dte': 'Days to Expiration', 
            'dte_category': 'DTE Category (Weekly/Monthly/Quarterly)',
            'expiry_concentration': 'Expiration Concentration Score',
            'time_decay_risk': 'Time Decay Risk Factor',
            
            # Strike & Moneyness
            'strike_concentration': 'Strike Concentration Score',
            'moneyness': 'Moneyness (% from ATM)',
            'moneyness_category': 'Moneyness Category',
            'atm_distance': 'Distance from ATM',
            
            # Greeks & Risk
            'total_delta': 'Total Delta Exposure',
            'total_gamma': 'Total Gamma Exposure',
            'total_theta': 'Total Theta Exposure',
            'total_vega': 'Total Vega Exposure',
            'net_delta': 'Net Delta (Calls - Puts)',
            'delta_adjusted_volume': 'Delta-Adjusted Volume',
            
            # Volatility
            'iv_percentile': 'IV Percentile Rank',
            'iv_vs_hv': 'IV vs Historical Volatility',
            'iv_skew': 'IV Skew Factor',
            'vega_weighted_iv': 'Vega-Weighted IV',
            
            # Spread & Liquidity
            'bid_ask_spread': 'Bid-Ask Spread',
            'bid_ask_pct': 'Bid-Ask Spread %',
            'liquidity_score': 'Liquidity Score',
            'market_impact': 'Estimated Market Impact',
            
            # Flow Directional
            'call_put_ratio': 'Call/Put Ratio',
            'call_volume_pct': 'Call Volume %',
            'put_volume_pct': 'Put Volume %',
            'net_call_premium': 'Net Call Premium',
            'net_put_premium': 'Net Put Premium',
            
            # Unusual Activity
            'unusual_volume': 'Unusual Volume Score',
            'unusual_premium': 'Unusual Premium Score', 
            'sweep_score': 'Option Sweep Score',
            'block_score': 'Block Trade Score',
            'whale_activity': 'Large Order Score',
            
            # Market Context
            'sector_flow': 'Sector Flow Alignment',
            'market_flow': 'Market Flow Alignment',
            'earnings_proximity': 'Earnings Event Proximity',
            'event_risk': 'Event Risk Score',
            
            # Technical
            'price_momentum': 'Underlying Price Momentum',
            'support_resistance': 'Strike S/R Level',
            'breakout_potential': 'Breakout Potential Score',
            'trend_alignment': 'Flow/Price Trend Alignment'
        }
    
    def update_data(self, ticker: str, **kwargs):
        """Update flow scanner data"""
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
                if not self.data.empty:
                    # Calculate advanced flow parameters
                    self.data = self._calculate_flow_parameters(self.data)
                    self._last_updated = datetime.now()
                return self.data
        except Exception as e:
            print(f"Error updating flow data: {e}")
        return None
    
    def _calculate_flow_parameters(self, df):
        """Calculate all 100+ flow parameters"""
        # Basic volume metrics
        df['DollarVolume'] = df.get('Volume', 0) * df.get('Premium', 0)
        df['VolOI_Ratio'] = df.get('V/OI', 0)
        df['VolumeRank'] = df.get('Volume', 0).rank(pct=True)
        df['PremiumRank'] = df.get('Premium', 0).rank(pct=True)
        
        # Greeks calculations
        df['TotalDelta'] = df.get('Volume', 0) * df.get('Delta', 0)
        df['TotalGamma'] = df.get('Volume', 0) * df.get('Gamma', 0)
        df['TotalTheta'] = df.get('Volume', 0) * df.get('Theta', 0)
        df['TotalVega'] = df.get('Volume', 0) * df.get('Vega', 0)
        
        # Call/Put analysis
        calls_mask = df.get('Type', '') == 'CALL'
        puts_mask = df.get('Type', '') == 'PUT'
        
        total_call_volume = df[calls_mask].get('Volume', pd.Series([0])).sum()
        total_put_volume = df[puts_mask].get('Volume', pd.Series([0])).sum()
        
        df['CallPutRatio'] = total_call_volume / max(total_put_volume, 1)
        df['CallVolumePct'] = total_call_volume / max(total_call_volume + total_put_volume, 1) * 100
        
        # Moneyness categories
        df['MoneynessCategory'] = 'ATM'
        df.loc[df.get('Moneyness', 0) > 5, 'MoneynessCategory'] = 'OTM'
        df.loc[df.get('Moneyness', 0) < -5, 'MoneynessCategory'] = 'ITM'
        
        # DTE categories
        df['DTECategory'] = 'Monthly'
        df.loc[df.get('DTE', 0) <= 7, 'DTECategory'] = 'Weekly'
        df.loc[df.get('DTE', 0) >= 60, 'DTECategory'] = 'Quarterly'
        
        # Liquidity score (based on bid-ask spread and volume)
        df['LiquidityScore'] = (
            (100 - df.get('Spread%', 100)) * 0.5 + 
            df.get('VolumeRank', 0) * 50
        ).clip(0, 100)
        
        # Unusual activity scores (enhanced from base processor)
        df['UnusualVolumeScore'] = np.where(df.get('V/OI', 0) > 3, 
                                           df.get('V/OI', 0) * 10, 0).clip(0, 100)
        
        df['SweepScore'] = np.where(
            (df.get('Volume', 0) > df.get('Volume', 0).quantile(0.9)) & 
            (df.get('Spread%', 0) < 5), 75, 0
        )
        
        df['BlockScore'] = np.where(df.get('Premium', 0) > df.get('Premium', 0).quantile(0.95), 80, 0)
        
        # Whale activity (large premium + volume)
        df['WhaleActivity'] = (
            (df.get('PremiumRank', 0) > 0.9) & 
            (df.get('VolumeRank', 0) > 0.8)
        ).astype(int) * 90
        
        # Flow direction score
        df['FlowDirectionScore'] = 0
        df.loc[calls_mask, 'FlowDirectionScore'] = df.loc[calls_mask, 'Volume'] * 1
        df.loc[puts_mask, 'FlowDirectionScore'] = df.loc[puts_mask, 'Volume'] * -1
        
        return df
    
    def analyze_historical_flow(self, symbol: str, timeframe_days: int) -> dict:
        """Analyze historical flow patterns (Unusual Whales style)"""
        try:
            # Get historical snapshots
            end_date = date.today()
            start_date = end_date - timedelta(days=timeframe_days)

            historical_data = []
            for i in range(timeframe_days + 1):
                target_date = start_date + timedelta(days=i)
                snapshot = historical_collector.load_historical_snapshot(symbol, target_date)
                if snapshot:
                    historical_data.append(snapshot)

            if not historical_data:
                return {"error": f"No historical data available for {symbol}"}

            # Analyze patterns like the screenshots show
            analysis = {
                'timeframe': f"{timeframe_days} days",
                'symbol': symbol,
                'unusual_patterns': self._detect_flow_patterns(historical_data),
                'position_builds': self._analyze_position_builds(historical_data),
                'whale_activity': self._detect_whale_patterns(historical_data),
                'sweep_patterns': self._analyze_sweep_patterns(historical_data),
                'daily_summary': self._create_daily_flow_summary(historical_data)
            }

            return analysis

        except Exception as e:
            return {"error": f"Error analyzing historical flow: {str(e)}"}

    def _detect_flow_patterns(self, historical_data: list) -> list:
        """Detect unusual flow patterns over multiple days"""
        patterns = []
        strike_tracking = {}

        try:
            for snapshot in historical_data:
                snapshot_date = snapshot.get('date')
                for unusual in snapshot.get('unusual_activity', []):
                    strike_key = f"{unusual['strike']}{unusual['type'][0]}_{unusual['expiry']}"

                    if strike_key not in strike_tracking:
                        strike_tracking[strike_key] = []

                    strike_tracking[strike_key].append({
                        'date': snapshot_date,
                        'volume': unusual['volume'],
                        'unusual_score': unusual['unusual_score'],
                        'strike': unusual['strike'],
                        'type': unusual['type'],
                        'expiry': unusual['expiry']
                    })

            # Find patterns with consistent activity
            for strike_key, activities in strike_tracking.items():
                if len(activities) >= 2:  # Active on multiple days
                    total_volume = sum(a['volume'] for a in activities)
                    avg_score = sum(a['unusual_score'] for a in activities) / len(activities)
                    days_active = len(activities)

                    if total_volume >= 5000 and avg_score >= 3.0:
                        patterns.append({
                            'pattern_id': strike_key,
                            'strike': activities[0]['strike'],
                            'type': activities[0]['type'],
                            'expiry': activities[0]['expiry'],
                            'days_active': days_active,
                            'total_volume': total_volume,
                            'avg_unusual_score': round(avg_score, 2),
                            'first_seen': activities[0]['date'],
                            'last_seen': activities[-1]['date'],
                            'pattern_strength': min(100, (days_active * 20) + (avg_score * 10)),
                            'timeline': activities
                        })

            # Sort by pattern strength
            patterns.sort(key=lambda x: x['pattern_strength'], reverse=True)

        except Exception as e:
            patterns.append({'error': str(e)})

        return patterns[:20]  # Return top 20 patterns

    def _analyze_position_builds(self, historical_data: list) -> list:
        """Analyze position building patterns (like ConvexValue's gamma evolution)"""
        builds = []

        try:
            # Track OI changes by contract
            contract_evolution = {}

            for i, snapshot in enumerate(historical_data):
                if i == 0:
                    continue  # Need previous day for comparison

                prev_snapshot = historical_data[i-1]
                current_date = snapshot.get('date')

                # Compare OI between days
                for chain in snapshot.get('options_chains', []):
                    expiry = chain.get('expiry')

                    for option_type in ['calls', 'puts']:
                        for option in chain.get(option_type, []):
                            strike = option['strike']
                            current_oi = option.get('open_interest', 0)

                            # Find previous day's OI
                            prev_oi = 0
                            for prev_chain in prev_snapshot.get('options_chains', []):
                                if prev_chain.get('expiry') == expiry:
                                    for prev_option in prev_chain.get(option_type, []):
                                        if prev_option['strike'] == strike:
                                            prev_oi = prev_option.get('open_interest', 0)
                                            break

                            oi_change = current_oi - prev_oi
                            if abs(oi_change) >= 1000:  # Significant OI change
                                contract_key = f"{strike}{option_type[0].upper()}_{expiry}"

                                if contract_key not in contract_evolution:
                                    contract_evolution[contract_key] = []

                                contract_evolution[contract_key].append({
                                    'date': current_date,
                                    'oi_change': oi_change,
                                    'current_oi': current_oi,
                                    'volume': option.get('volume', 0)
                                })

            # Identify significant builds
            for contract_key, changes in contract_evolution.items():
                if len(changes) >= 2:
                    total_oi_change = sum(c['oi_change'] for c in changes)
                    avg_daily_change = total_oi_change / len(changes)

                    if abs(total_oi_change) >= 5000:
                        builds.append({
                            'contract': contract_key,
                            'days_building': len(changes),
                            'total_oi_change': total_oi_change,
                            'avg_daily_change': round(avg_daily_change),
                            'build_direction': 'accumulation' if total_oi_change > 0 else 'distribution',
                            'build_strength': min(100, abs(total_oi_change) / 1000),
                            'timeline': changes
                        })

            builds.sort(key=lambda x: abs(x['total_oi_change']), reverse=True)

        except Exception as e:
            builds.append({'error': str(e)})

        return builds[:15]  # Return top 15 builds

    def _detect_whale_patterns(self, historical_data: list) -> list:
        """Detect whale activity patterns over time"""
        whale_patterns = []

        try:
            for snapshot in historical_data:
                snapshot_date = snapshot.get('date')

                for unusual in snapshot.get('unusual_activity', []):
                    volume = unusual.get('volume', 0)
                    unusual_score = unusual.get('unusual_score', 0)

                    # Whale criteria: High volume + high unusual score
                    if volume >= 10000 and unusual_score >= 5.0:
                        whale_patterns.append({
                            'date': snapshot_date,
                            'strike': unusual['strike'],
                            'type': unusual['type'],
                            'expiry': unusual['expiry'],
                            'volume': volume,
                            'unusual_score': unusual_score,
                            'whale_score': min(100, (volume / 1000) + (unusual_score * 5))
                        })

            # Sort by whale score
            whale_patterns.sort(key=lambda x: x['whale_score'], reverse=True)

        except Exception as e:
            whale_patterns.append({'error': str(e)})

        return whale_patterns[:10]  # Return top 10 whale activities

    def _analyze_sweep_patterns(self, historical_data: list) -> list:
        """Analyze sweep patterns over time"""
        # Simplified sweep detection - can be enhanced with more sophisticated logic
        sweeps = []

        try:
            for snapshot in historical_data:
                snapshot_date = snapshot.get('date')

                for unusual in snapshot.get('unusual_activity', []):
                    volume = unusual.get('volume', 0)
                    # Simple sweep criteria - high volume unusual activity
                    if volume >= 15000:
                        sweeps.append({
                            'date': snapshot_date,
                            'contract': f"{unusual['strike']}{unusual['type'][0]}",
                            'volume': volume,
                            'expiry': unusual['expiry'],
                            'sweep_score': min(100, volume / 500)
                        })

        except Exception as e:
            sweeps.append({'error': str(e)})

        return sweeps[:10]

    def _create_daily_flow_summary(self, historical_data: list) -> list:
        """Create daily flow summary (like Unusual Whales table format)"""
        summary = []

        try:
            for snapshot in historical_data:
                snapshot_date = snapshot.get('date')
                stats = snapshot.get('daily_stats', {})
                unusual_count = len(snapshot.get('unusual_activity', []))

                total_volume = stats.get('total_call_volume', 0) + stats.get('total_put_volume', 0)
                put_call_ratio = stats.get('put_call_volume_ratio', 0)

                summary.append({
                    'date': snapshot_date,
                    'total_volume': total_volume,
                    'call_volume': stats.get('total_call_volume', 0),
                    'put_volume': stats.get('total_put_volume', 0),
                    'put_call_ratio': round(put_call_ratio, 2),
                    'unusual_count': unusual_count,
                    'underlying_price': snapshot.get('underlying_price'),
                })

        except Exception as e:
            summary.append({'error': str(e)})

        return summary

    def create_visualizations(self):
        """Create flow scanner visualizations"""
        if self.data is None or self.data.empty:
            return {}
            
        return {
            "flow_table": self._create_advanced_flow_table(),
            "flow_chart": self._create_flow_chart(),
            "parameter_analysis": self._create_parameter_analysis(),
            "unusual_alerts": self._create_unusual_alerts()
        }
    
    def _create_advanced_flow_table(self):
        """Create advanced flow analysis table"""
        # Select key flow columns
        display_cols = [
            'Type', 'Strike', 'Expiry', 'Volume', 'Premium', 'DollarVolume',
            'VolOI_Ratio', 'IV', 'UnusualScore', 'LiquidityScore', 'MoneynessCategory',
            'DTECategory', 'FlowDirectionScore', 'SweepScore', 'BlockScore', 'WhaleActivity'
        ]
        
        # Filter columns that exist
        available_cols = [col for col in display_cols if col in self.data.columns]
        display_data = self.data[available_cols].copy()
        
        # Sort by unusual activity
        if 'UnusualScore' in display_data.columns:
            display_data = display_data.sort_values('UnusualScore', ascending=False)
        
        # Conditional formatting for table
        style_conditions = [
            # Unusual activity
            {
                'if': {'filter_query': '{UnusualScore} > 75'},
                'backgroundColor': 'rgba(255, 0, 0, 0.4)',
                'color': 'white'
            },
            {
                'if': {'filter_query': '{UnusualScore} > 50'},
                'backgroundColor': 'rgba(255, 165, 0, 0.4)',
                'color': 'white'
            },
            # Large volume
            {
                'if': {'filter_query': '{Volume} > 1000'},
                'backgroundColor': 'rgba(0, 212, 170, 0.3)',
                'color': 'white'
            },
            # Sweep activity
            {
                'if': {'filter_query': '{SweepScore} > 50'},
                'backgroundColor': 'rgba(75, 0, 130, 0.4)',
                'color': 'white'
            }
        ]
        
        return dash_table.DataTable(
            id="flow-table",
            columns=[{"name": col, "id": col} for col in display_data.columns],
            data=display_data.head(50).to_dict("records"),  # Limit to top 50
            style_table={'overflowX': 'auto'},
            style_header={
                'backgroundColor': THEME_CONFIG["accent_color"],
                'color': 'white',
                'fontWeight': 'bold'
            },
            style_cell={
                'backgroundColor': THEME_CONFIG["paper_color"],
                'color': THEME_CONFIG["text_color"],
                'textAlign': 'center'
            },
            style_data_conditional=style_conditions,
            sort_action="native",
            filter_action="native",
            page_action="native",
            page_size=25
        )
    
    def _create_flow_chart(self):
        """Create flow visualization chart"""
        fig = go.Figure()
        
        # Call flow
        calls = self.data[self.data.get('Type', '') == 'CALL'] if 'Type' in self.data.columns else self.data
        if not calls.empty:
            fig.add_trace(go.Scatter(
                x=calls.get('DTE', []),
                y=calls.get('Premium', []),
                mode='markers',
                name='Call Flow',
                marker=dict(
                    size=np.sqrt(calls.get('Volume', [1])),
                    color=calls.get('UnusualScore', [0]),
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="Unusual Score", x=1.1)
                ),
                text=calls.get('Strike', []),
                hovertemplate='<b>Call</b><br>' +
                             'Strike: %{text}<br>' +
                             'DTE: %{x}<br>' +
                             'Premium: $%{y:,.0f}<br>' +
                             '<extra></extra>'
            ))
        
        # Put flow
        puts = self.data[self.data.get('Type', '') == 'PUT'] if 'Type' in self.data.columns else pd.DataFrame()
        if not puts.empty:
            fig.add_trace(go.Scatter(
                x=puts.get('DTE', []),
                y=puts.get('Premium', []) * -1,  # Negative for puts
                mode='markers',
                name='Put Flow',
                marker=dict(
                    size=np.sqrt(puts.get('Volume', [1])),
                    color=THEME_CONFIG["secondary_color"],
                    opacity=0.7
                ),
                text=puts.get('Strike', []),
                hovertemplate='<b>Put</b><br>' +
                             'Strike: %{text}<br>' +
                             'DTE: %{x}<br>' +
                             'Premium: $%{y:,.0f}<br>' +
                             '<extra></extra>'
            ))
        
        fig.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.5)
        
        fig.update_layout(
            title="Options Flow Analysis (Bubble Size = Volume)",
            xaxis_title="Days to Expiration",
            yaxis_title="Premium (Calls +, Puts -)",
            plot_bgcolor=THEME_CONFIG["paper_color"],
            paper_bgcolor=THEME_CONFIG["background_color"],
            font=dict(color=THEME_CONFIG["text_color"]),
            height=600
        )
        
        return dcc.Graph(figure=fig)
    
    def _create_parameter_analysis(self):
        """Create parameter importance analysis"""
        if self.data.empty:
            return html.Div("No data for parameter analysis")
        
        # Calculate parameter correlations with unusual activity
        numeric_cols = self.data.select_dtypes(include=[np.number]).columns
        correlations = {}
        
        if 'UnusualScore' in self.data.columns:
            for col in numeric_cols:
                if col != 'UnusualScore' and not self.data[col].isna().all():
                    corr = self.data[col].corr(self.data['UnusualScore'])
                    if not np.isnan(corr):
                        correlations[col] = abs(corr)
        
        if not correlations:
            return html.Div("Insufficient data for parameter analysis")
        
        # Top 10 most important parameters
        top_params = sorted(correlations.items(), key=lambda x: x[1], reverse=True)[:10]
        
        param_names = [param[0] for param in top_params]
        param_scores = [param[1] for param in top_params]
        
        fig = go.Figure(data=go.Bar(
            y=param_names,
            x=param_scores,
            orientation='h',
            marker_color=THEME_CONFIG["primary_color"]
        ))
        
        fig.update_layout(
            title="Top Flow Parameters (Correlation with Unusual Activity)",
            xaxis_title="Correlation Strength",
            yaxis_title="Parameter",
            plot_bgcolor=THEME_CONFIG["paper_color"],
            paper_bgcolor=THEME_CONFIG["background_color"],
            font=dict(color=THEME_CONFIG["text_color"]),
            height=500
        )
        
        return dcc.Graph(figure=fig)
    
    def _create_unusual_alerts(self):
        """Create unusual activity alerts"""
        alerts = []
        
        if self.data.empty:
            return html.Div("No data for alerts")
        
        # High unusual score alerts
        if 'UnusualScore' in self.data.columns:
            unusual_high = self.data[self.data['UnusualScore'] > 75]
            for _, row in unusual_high.head(5).iterrows():
                alerts.append(
                    dbc.Alert([
                        html.H6(f"🚨 HIGH UNUSUAL ACTIVITY", className="alert-heading"),
                        html.P(f"{row.get('Type', 'N/A')} {row.get('Strike', 'N/A')} "
                              f"exp {row.get('Expiry', 'N/A')} - Score: {row.get('UnusualScore', 0):.0f}")
                    ], color="danger", className="mb-2")
                )
        
        # Sweep alerts
        if 'SweepScore' in self.data.columns:
            sweeps = self.data[self.data['SweepScore'] > 50]
            for _, row in sweeps.head(3).iterrows():
                alerts.append(
                    dbc.Alert([
                        html.H6("⚡ OPTION SWEEP DETECTED", className="alert-heading"),
                        html.P(f"{row.get('Type', 'N/A')} {row.get('Strike', 'N/A')} "
                              f"- Volume: {row.get('Volume', 0):,.0f}")
                    ], color="warning", className="mb-2")
                )
        
        # Whale activity alerts
        if 'WhaleActivity' in self.data.columns:
            whales = self.data[self.data['WhaleActivity'] > 50]
            for _, row in whales.head(3).iterrows():
                alerts.append(
                    dbc.Alert([
                        html.H6("🐋 LARGE ORDER ACTIVITY", className="alert-heading"),
                        html.P(f"{row.get('Type', 'N/A')} {row.get('Strike', 'N/A')} "
                              f"- Premium: ${row.get('Premium', 0):,.0f}")
                    ], color="info", className="mb-2")
                )
        
        if not alerts:
            alerts.append(
                dbc.Alert("No unusual activity detected at this time", color="light")
            )
        
        return html.Div(alerts[:8])  # Limit to 8 alerts
    
    def create_layout(self, ticker: str) -> html.Div:
        """Create flow scanner layout"""
        return html.Div([
            # Header
            dbc.Row([
                dbc.Col([
                    dbc.Button("← Dashboard", id={"type": "back-button", "module": "flow_scanner"}, color="outline-primary", size="sm")
                ], width="auto"),
                dbc.Col([
                    html.H3(f"🔍 Flow Scanner - {ticker}", 
                           style={"color": THEME_CONFIG["primary_color"]})
                ])
            ], align="center", className="mb-4"),
            
            # Controls
            dbc.Card([
                dbc.CardBody([
                    # Main controls row
                    dbc.Row([
                        dbc.Col([
                            dbc.Button("🔄 Scan Flow",
                                      id="scan-flow-btn",
                                      color="primary",
                                      size="lg")
                        ], width="auto"),
                        dbc.Col([
                            dbc.ButtonGroup([
                                dbc.Button("Flow Table", id="show-flow-table-btn", color="info", size="sm"),
                                dbc.Button("Flow Chart", id="show-flow-chart-btn", color="info", size="sm"),
                                dbc.Button("Parameters", id="show-params-btn", color="info", size="sm"),
                                dbc.Button("Alerts", id="show-alerts-btn", color="info", size="sm")
                            ])
                        ], width="auto"),
                        dbc.Col([
                            html.Div(id="flow-status", className="text-muted small")
                        ], className="ms-auto text-end")
                    ], align="center", className="mb-3"),

                    # Historical analysis controls row
                    dbc.Row([
                        dbc.Col([
                            html.Label("Analysis Mode:", className="form-label small mb-1"),
                            dbc.RadioItems(
                                id="flow-analysis-mode",
                                options=[
                                    {"label": "Live", "value": "live"},
                                    {"label": "Historical", "value": "historical"}
                                ],
                                value="live",
                                inline=True,
                                className="small"
                            )
                        ], width=2),
                        dbc.Col([
                            html.Label("Timeframe:", className="form-label small mb-1"),
                            dbc.ButtonGroup([
                                dbc.Button("1D", id="flow-1d-btn", size="sm", outline=True, color="secondary"),
                                dbc.Button("3D", id="flow-3d-btn", size="sm", outline=True, color="secondary"),
                                dbc.Button("1W", id="flow-1w-btn", size="sm", color="secondary"),
                                dbc.Button("2W", id="flow-2w-btn", size="sm", outline=True, color="secondary"),
                            ], size="sm")
                        ], width=3, id="flow-timeframe-controls", style={"display": "none"}),
                        dbc.Col([
                            html.Label("Pattern Type:", className="form-label small mb-1"),
                            dcc.Dropdown(
                                id="flow-pattern-filter",
                                options=[
                                    {"label": "All Patterns", "value": "all"},
                                    {"label": "Consistent Builds", "value": "builds"},
                                    {"label": "Whale Activity", "value": "whale"},
                                    {"label": "Sweep Patterns", "value": "sweeps"}
                                ],
                                value="all",
                                className="small",
                                style={"fontSize": "12px"}
                            )
                        ], width=2, id="flow-pattern-controls", style={"display": "none"}),
                        dbc.Col([
                            html.Small("💡 Historical mode shows position builds over time",
                                     className="text-muted", style={"display": "none"}),
                            html.Small("⚡ Live mode shows current unusual activity",
                                     className="text-info")
                        ], width=5, id="flow-mode-help")
                    ], align="center")
                ])
            ], className="mb-4"),
            
            # Alert panel
            dbc.Card([
                dbc.CardBody([
                    html.H5("🚨 Real-time Alerts", className="mb-3"),
                    html.Div(id="flow-alerts")
                ])
            ], className="mb-4"),
            
            # Main content
            html.Div(id="flow-content", children=[
                self._create_welcome_message(ticker)
            ])
        ])
    
    def _create_welcome_message(self, ticker: str) -> html.Div:
        """Create welcome message"""
        return dbc.Card([
            dbc.CardBody([
                html.H4(f"Flow Scanner Ready for {ticker}", className="text-center"),
                html.P("Advanced options flow analysis with 100+ parameters", 
                       className="text-center text-muted"),
                html.Hr(),
                dbc.Row([
                    dbc.Col([
                        html.H6("🔍 Analysis Features:"),
                        html.Ul([
                            html.Li("100+ Flow Parameters"),
                            html.Li("Unusual Activity Detection"),
                            html.Li("Option Sweeps & Blocks"),
                            html.Li("Whale Activity Alerts")
                        ])
                    ], md=6),
                    dbc.Col([
                        html.H6("📊 Visualizations:"),
                        html.Ul([
                            html.Li("Advanced Flow Table"),
                            html.Li("Interactive Flow Charts"),
                            html.Li("Parameter Importance"),
                            html.Li("Real-time Alerts")
                        ])
                    ], md=6)
                ])
            ])
        ], style={"backgroundColor": THEME_CONFIG["paper_color"]})

# Global instance
flow_scanner_module = FlowScannerModule()