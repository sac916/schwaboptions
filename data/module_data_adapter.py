"""
Module Data Adapter - Universal Data Interface for All Modules
Provides consistent, intelligent data access for all SchwaOptions modules
"""
import pandas as pd
from typing import Dict, Any, Optional, Tuple, List
from datetime import date, datetime
import logging

from .universal_data_router import universal_data_router, DataQuality
from .processors import OptionsProcessor

logger = logging.getLogger(__name__)

class ModuleDataAdapter:
    """
    Universal data adapter for all SchwaOptions modules
    Replaces direct schwab_client calls with intelligent data routing
    """

    def __init__(self):
        self.processor = OptionsProcessor()

    def get_options_analysis(self, symbol: str,
                           analysis_type: str = "comprehensive",
                           force_mode: Optional[str] = None,
                           target_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Get comprehensive options analysis data for any module

        Args:
            symbol: Stock ticker symbol
            analysis_type: Type of analysis ("iv_surface", "flow_scanner", "heatmap", etc.)
            force_mode: "live", "historical", or None for intelligent routing
            target_date: Specific historical date for analysis

        Returns:
            Dictionary with processed data ready for module consumption
        """

        # Get intelligent data routing
        force_live = (force_mode == "live")
        force_historical = (force_mode == "historical")

        raw_data, quality = universal_data_router.get_options_data(
            symbol=symbol,
            force_live=force_live,
            force_historical=force_historical,
            target_date=target_date
        )

        # Process raw data into module-ready format
        processed_data = self._process_for_modules(symbol, raw_data, quality, analysis_type)

        # Add metadata for module UI
        processed_data['data_info'] = self._create_data_info(symbol, quality, raw_data)

        return processed_data

    def _process_for_modules(self, symbol: str, raw_data: Dict,
                           quality: DataQuality, analysis_type: str) -> Dict[str, Any]:
        """Process raw data into module-specific format"""

        # Base structure for all modules
        processed = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'data_quality': quality,
            'analysis_ready': True
        }

        # Check if we have real options data or demo/enriched data
        if self._has_options_chains(raw_data):
            # Real options data - process normally
            try:
                if analysis_type == "iv_surface":
                    processed.update(self._process_for_iv_surface(raw_data))
                elif analysis_type == "flow_scanner":
                    processed.update(self._process_for_flow_scanner(raw_data))
                elif analysis_type == "options_heatmap":
                    processed.update(self._process_for_heatmap(raw_data))
                elif analysis_type == "strike_analysis":
                    processed.update(self._process_for_strike_analysis(raw_data))
                elif analysis_type == "intraday_charts":
                    processed.update(self._process_for_intraday(raw_data))
                elif analysis_type == "dealer_surfaces":
                    processed.update(self._process_for_dealer_surfaces(raw_data))
                else:
                    # Comprehensive processing for general use
                    processed.update(self._process_comprehensive(raw_data))

            except Exception as e:
                logger.error(f"Error processing {analysis_type} data for {symbol}: {e}")
                processed.update(self._create_error_fallback(symbol, str(e)))

        else:
            # Enriched/demo data - create meaningful presentation
            processed.update(self._process_enriched_data(raw_data, analysis_type))

        return processed

    def _has_options_chains(self, raw_data: Dict) -> bool:
        """Check if raw data contains actual options chain data"""
        if not raw_data:
            return False

        return ('callExpDateMap' in raw_data and 'putExpDateMap' in raw_data) or \
               ('options_chains' in raw_data and raw_data['options_chains'])

    def _process_for_iv_surface(self, raw_data: Dict) -> Dict:
        """Process data specifically for IV Surface module"""
        try:
            if 'options_chains' in raw_data:
                # Historical data format
                options_chains = raw_data['options_chains']
                surface_data = self._build_iv_surface_from_historical(options_chains)
            else:
                # Live data format
                surface_data = self._build_iv_surface_from_live(raw_data)

            return {
                'iv_surface_data': surface_data,
                'term_structure': self._calculate_term_structure(surface_data),
                'volatility_metrics': self._calculate_volatility_metrics(surface_data),
                'surface_quality': self._assess_surface_quality(surface_data)
            }
        except Exception as e:
            logger.error(f"Error processing IV surface data: {e}")
            return self._create_iv_surface_fallback()

    def _process_for_flow_scanner(self, raw_data: Dict) -> Dict:
        """Process data specifically for Flow Scanner module"""
        try:
            if 'unusual_activity' in raw_data:
                # Use stored unusual activity
                unusual_flows = raw_data['unusual_activity']
            else:
                # Calculate from live data
                unusual_flows = self._detect_unusual_activity(raw_data)

            return {
                'unusual_flows': unusual_flows,
                'flow_summary': self._create_flow_summary(unusual_flows),
                'alert_level': self._calculate_alert_level(unusual_flows),
                'flow_parameters': self._calculate_flow_parameters(raw_data)
            }
        except Exception as e:
            logger.error(f"Error processing flow scanner data: {e}")
            return self._create_flow_scanner_fallback()

    def _process_for_heatmap(self, raw_data: Dict) -> Dict:
        """Process data specifically for Options Heatmap module"""
        try:
            heatmap_matrix = self._build_heatmap_matrix(raw_data)

            return {
                'heatmap_data': heatmap_matrix,
                'volume_heatmap': self._create_volume_heatmap(heatmap_matrix),
                'oi_heatmap': self._create_oi_heatmap(heatmap_matrix),
                'iv_heatmap': self._create_iv_heatmap(heatmap_matrix),
                'heatmap_stats': self._calculate_heatmap_stats(heatmap_matrix)
            }
        except Exception as e:
            logger.error(f"Error processing heatmap data: {e}")
            return self._create_heatmap_fallback()

    def _process_for_strike_analysis(self, raw_data: Dict) -> Dict:
        """Process data for Strike Analysis module"""
        try:
            strike_data = self._analyze_strikes(raw_data)

            return {
                'strike_analysis': strike_data,
                'support_resistance': self._find_support_resistance(strike_data),
                'volume_distribution': self._analyze_volume_distribution(strike_data),
                'max_pain': self._calculate_max_pain(strike_data)
            }
        except Exception as e:
            logger.error(f"Error processing strike analysis data: {e}")
            return self._create_strike_analysis_fallback()

    def _process_for_intraday(self, raw_data: Dict) -> Dict:
        """Process data for Intraday Charts module"""
        try:
            return {
                'intraday_data': self._prepare_intraday_data(raw_data),
                'price_levels': self._identify_key_levels(raw_data),
                'volume_profile': self._create_volume_profile(raw_data),
                'flow_overlay': self._prepare_flow_overlay(raw_data)
            }
        except Exception as e:
            logger.error(f"Error processing intraday data: {e}")
            return self._create_intraday_fallback()

    def _process_for_dealer_surfaces(self, raw_data: Dict) -> Dict:
        """Process data for Dealer Surfaces module"""
        try:
            return {
                'dealer_surfaces': self._calculate_dealer_surfaces(raw_data),
                'gamma_surface': self._build_gamma_surface(raw_data),
                'delta_surface': self._build_delta_surface(raw_data),
                'vega_surface': self._build_vega_surface(raw_data)
            }
        except Exception as e:
            logger.error(f"Error processing dealer surfaces data: {e}")
            return self._create_dealer_surfaces_fallback()

    def _process_comprehensive(self, raw_data: Dict) -> Dict:
        """Comprehensive processing for general module use"""
        try:
            return {
                'options_summary': self._create_options_summary(raw_data),
                'key_metrics': self._calculate_key_metrics(raw_data),
                'risk_metrics': self._calculate_risk_metrics(raw_data),
                'activity_summary': self._create_activity_summary(raw_data)
            }
        except Exception as e:
            logger.error(f"Error in comprehensive processing: {e}")
            return self._create_comprehensive_fallback()

    def _process_enriched_data(self, raw_data: Dict, analysis_type: str) -> Dict:
        """Process enriched/historical data for meaningful presentation"""

        enrichment = raw_data.get('enrichment', {})

        base_result = {
            'enriched_analysis': True,
            'data_source': enrichment.get('data_source', 'historical_enriched'),
            'analysis_depth': 'comprehensive_with_context'
        }

        # Create meaningful content based on enrichment data
        if 'historical_context' in enrichment:
            base_result['historical_context'] = enrichment['historical_context']

        if 'time_series_analysis' in enrichment:
            base_result['time_series_available'] = True

        if 'pattern_recognition' in enrichment:
            base_result['patterns_identified'] = True

        # Add analysis-specific enriched content
        if analysis_type == "iv_surface":
            base_result.update(self._create_enriched_iv_analysis(raw_data))
        elif analysis_type == "flow_scanner":
            base_result.update(self._create_enriched_flow_analysis(raw_data))

        return base_result

    def _create_data_info(self, symbol: str, quality: DataQuality, raw_data: Dict) -> Dict:
        """Create data information for module UI"""

        info = {
            'symbol': symbol,
            'quality': quality,
            'timestamp': datetime.now().isoformat(),
            'data_age': self._calculate_data_age(raw_data),
            'coverage': self._assess_data_coverage(raw_data),
            'source_description': self._describe_data_source(quality, raw_data)
        }

        # Add quality-specific UI messages
        if quality == DataQuality.EXCELLENT:
            info['user_message'] = "🟢 Live data with high volume and complete coverage"
        elif quality == DataQuality.GOOD:
            info['user_message'] = "🟡 Live data with moderate activity"
        elif quality == DataQuality.FAIR:
            info['user_message'] = "🟠 Low volume data - historical context provided"
        elif quality == DataQuality.ENRICHED:
            info['user_message'] = "🔵 Historical analysis with comprehensive insights"
        else:
            info['user_message'] = "🔴 Limited data available - showing demo content"

        return info

    # Placeholder methods for specific processing logic
    def _build_iv_surface_from_historical(self, chains: List) -> Dict:
        return {'surface_type': 'historical', 'data_points': len(chains)}

    def _build_iv_surface_from_live(self, data: Dict) -> Dict:
        return {'surface_type': 'live', 'contracts': self._count_contracts(data)}

    def _calculate_term_structure(self, surface_data: Dict) -> Dict:
        return {'term_structure_available': True}

    def _calculate_volatility_metrics(self, surface_data: Dict) -> Dict:
        return {'iv_rank': 45.0, 'iv_percentile': 62.0}

    def _assess_surface_quality(self, surface_data: Dict) -> str:
        return 'good'

    def _create_iv_surface_fallback(self) -> Dict:
        return {'error': 'IV surface data unavailable', 'fallback_mode': True}

    def _detect_unusual_activity(self, data: Dict) -> List:
        return []  # Placeholder

    def _create_flow_summary(self, flows: List) -> Dict:
        return {'total_flows': len(flows), 'bullish_flows': 0, 'bearish_flows': 0}

    def _calculate_alert_level(self, flows: List) -> str:
        return 'normal'

    def _calculate_flow_parameters(self, data: Dict) -> Dict:
        return {'parameters_calculated': 100}

    def _create_flow_scanner_fallback(self) -> Dict:
        return {'error': 'Flow scanner data unavailable', 'fallback_mode': True}

    def _count_contracts(self, data: Dict) -> int:
        return 0  # Placeholder

    def _calculate_data_age(self, raw_data: Dict) -> str:
        return 'current'

    def _assess_data_coverage(self, raw_data: Dict) -> str:
        return 'complete'

    def _describe_data_source(self, quality: DataQuality, raw_data: Dict) -> str:
        if quality == DataQuality.ENRICHED:
            return "Historical data with derived analytics"
        else:
            return "Live market data"

    # Additional placeholder methods for other processing functions
    def _build_heatmap_matrix(self, data: Dict) -> Dict:
        return {}

    def _create_volume_heatmap(self, matrix: Dict) -> Dict:
        return {}

    def _create_oi_heatmap(self, matrix: Dict) -> Dict:
        return {}

    def _create_iv_heatmap(self, matrix: Dict) -> Dict:
        return {}

    def _calculate_heatmap_stats(self, matrix: Dict) -> Dict:
        return {}

    def _create_heatmap_fallback(self) -> Dict:
        return {'error': 'Heatmap data unavailable'}

    def _analyze_strikes(self, data: Dict) -> Dict:
        return {}

    def _find_support_resistance(self, strike_data: Dict) -> Dict:
        return {}

    def _analyze_volume_distribution(self, strike_data: Dict) -> Dict:
        return {}

    def _calculate_max_pain(self, strike_data: Dict) -> float:
        return 0.0

    def _create_strike_analysis_fallback(self) -> Dict:
        return {'error': 'Strike analysis data unavailable'}

    def _prepare_intraday_data(self, data: Dict) -> Dict:
        return {}

    def _identify_key_levels(self, data: Dict) -> List:
        return []

    def _create_volume_profile(self, data: Dict) -> Dict:
        return {}

    def _prepare_flow_overlay(self, data: Dict) -> Dict:
        return {}

    def _create_intraday_fallback(self) -> Dict:
        return {'error': 'Intraday data unavailable'}

    def _calculate_dealer_surfaces(self, data: Dict) -> Dict:
        return {}

    def _build_gamma_surface(self, data: Dict) -> Dict:
        return {}

    def _build_delta_surface(self, data: Dict) -> Dict:
        return {}

    def _build_vega_surface(self, data: Dict) -> Dict:
        return {}

    def _create_dealer_surfaces_fallback(self) -> Dict:
        return {'error': 'Dealer surfaces data unavailable'}

    def _create_options_summary(self, data: Dict) -> Dict:
        return {}

    def _calculate_key_metrics(self, data: Dict) -> Dict:
        return {}

    def _calculate_risk_metrics(self, data: Dict) -> Dict:
        return {}

    def _create_activity_summary(self, data: Dict) -> Dict:
        return {}

    def _create_comprehensive_fallback(self) -> Dict:
        return {'error': 'Comprehensive data unavailable'}

    def _create_enriched_iv_analysis(self, data: Dict) -> Dict:
        return {'enriched_iv_analysis': True}

    def _create_enriched_flow_analysis(self, data: Dict) -> Dict:
        return {'enriched_flow_analysis': True}

    def _create_error_fallback(self, symbol: str, error_msg: str) -> Dict:
        return {
            'error': True,
            'error_message': error_msg,
            'symbol': symbol,
            'fallback_data': True
        }

# Global instance for modules to use
module_data_adapter = ModuleDataAdapter()