"""
Data Quality UI Components for Universal Data System
Provides consistent data quality indicators and mode selection across modules
"""
import dash_bootstrap_components as dbc
from dash import html
from typing import Dict, Any, Optional

def create_data_quality_alert(data_info: Dict[str, Any]) -> dbc.Alert:
    """
    Create data quality indicator alert based on data info

    Args:
        data_info: Dictionary containing data quality information

    Returns:
        dbc.Alert component with appropriate styling and message
    """
    if not data_info:
        return dbc.Alert(
            "No data quality information available",
            color="secondary",
            className="mb-3"
        )

    quality = data_info.get('quality', 'unknown')
    source = data_info.get('source', 'unknown')
    timestamp = data_info.get('timestamp', 'unknown')

    # Quality level styling and messages
    quality_config = {
        'excellent': {
            'color': 'success',
            'icon': 'fa-check-circle',
            'message': 'Excellent - Live high-volume data'
        },
        'good': {
            'color': 'success',
            'icon': 'fa-check',
            'message': 'Good - Live moderate-volume data'
        },
        'fair': {
            'color': 'warning',
            'icon': 'fa-exclamation-triangle',
            'message': 'Fair - Low volume but recent data'
        },
        'enriched': {
            'color': 'info',
            'icon': 'fa-database',
            'message': 'Enriched - Historical data with analytics'
        },
        'poor': {
            'color': 'danger',
            'icon': 'fa-exclamation-circle',
            'message': 'Poor - Limited data with fallback'
        },
        'unknown': {
            'color': 'secondary',
            'icon': 'fa-question-circle',
            'message': 'Unknown data quality'
        }
    }

    config = quality_config.get(quality, quality_config['unknown'])

    return dbc.Alert([
        html.I(className=f"fas {config['icon']} me-2"),
        html.Strong(f"Data Quality: {quality.title()}"),
        html.Br(),
        config['message'],
        html.Br(),
        html.Small(f"Source: {source} | Updated: {timestamp}", className="text-muted")
    ], color=config['color'], className="mb-3")


def create_data_mode_buttons(active_mode: str = "auto") -> dbc.ButtonGroup:
    """
    Create data mode selection buttons

    Args:
        active_mode: Currently active mode ('live', 'historical', 'auto')

    Returns:
        dbc.ButtonGroup with mode selection buttons
    """
    return dbc.ButtonGroup([
        dbc.Button(
            [html.I(className="fas fa-broadcast-tower me-1"), "Live"],
            id="live-btn",
            size="sm",
            color="success",
            outline=True,
            active=(active_mode == "live")
        ),
        dbc.Button(
            [html.I(className="fas fa-history me-1"), "Historical"],
            id="historical-btn",
            size="sm",
            color="info",
            outline=True,
            active=(active_mode == "historical")
        ),
        dbc.Button(
            [html.I(className="fas fa-magic me-1"), "Auto"],
            id="auto-btn",
            size="sm",
            color="primary",
            outline=True,
            active=(active_mode == "auto")
        ),
    ], size="sm", className="mb-3")


def create_module_data_controls(module_id: str, active_mode: str = "auto") -> html.Div:
    """
    Create complete data controls for a module including quality indicator and mode buttons

    Args:
        module_id: Unique identifier for the module
        active_mode: Currently active mode

    Returns:
        html.Div containing data quality alert and mode selection buttons
    """
    return html.Div([
        # Data quality indicator
        dbc.Alert(
            "Loading data quality information...",
            id=f"{module_id}-data-info",
            color="info",
            className="mb-3"
        ),

        # Mode selection buttons
        html.Div([
            html.Label("Data Mode:", className="form-label small mb-1"),
            create_data_mode_buttons(active_mode)
        ], className="mb-3"),

        # Additional controls row
        dbc.Row([
            dbc.Col([
                dbc.Button(
                    [html.I(className="fas fa-sync me-1"), "Refresh"],
                    id=f"{module_id}-refresh-btn",
                    size="sm",
                    color="secondary",
                    outline=True
                )
            ], width="auto"),
            dbc.Col([
                dbc.Button(
                    [html.I(className="fas fa-calendar me-1"), "Date"],
                    id=f"{module_id}-date-btn",
                    size="sm",
                    color="secondary",
                    outline=True
                )
            ], width="auto")
        ], className="g-2")
    ], className="border-bottom pb-3 mb-4")


def get_quality_level_from_info(data_info: Dict[str, Any]) -> str:
    """
    Extract quality level from data info dictionary

    Args:
        data_info: Dictionary containing data information

    Returns:
        Quality level string ('excellent', 'good', 'fair', 'enriched', 'poor', 'unknown')
    """
    if not data_info:
        return 'unknown'

    return data_info.get('quality', 'unknown')


def format_data_timestamp(timestamp: str) -> str:
    """
    Format timestamp for display in data quality alerts

    Args:
        timestamp: Raw timestamp string

    Returns:
        Formatted timestamp string
    """
    if not timestamp or timestamp == 'unknown':
        return 'Unknown'

    try:
        # Handle different timestamp formats
        from datetime import datetime
        if isinstance(timestamp, str):
            # Try common formats
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d']:
                try:
                    dt = datetime.strptime(timestamp, fmt)
                    return dt.strftime('%H:%M:%S')
                except ValueError:
                    continue
        return str(timestamp)
    except Exception:
        return str(timestamp)