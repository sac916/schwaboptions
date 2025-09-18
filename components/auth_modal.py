"""
Authentication modal component for seamless Schwab API authentication
"""
import dash_bootstrap_components as dbc
from dash import html, dcc
from config import THEME_CONFIG

def create_auth_modal():
    """Create the authentication modal component"""
    return dbc.Modal([
        dbc.ModalHeader([
            html.H4([
                html.I(className="fas fa-key me-2"),
                "Schwab API Authentication"
            ], className="modal-title")
        ]),
        dbc.ModalBody([
            # Auth status indicator
            html.Div(id="auth-modal-status", children=[
                dbc.Alert([
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    "Authentication required to access Schwab API data."
                ], color="warning", className="mb-3")
            ]),

            # Step 1: Authorization URL
            html.Div([
                html.H6([
                    html.Span("1", className="badge bg-primary me-2"),
                    "Get Authorization"
                ], className="mb-2"),
                html.P([
                    "Click the button below to generate a fresh authorization URL, then click the link to authenticate with Schwab."
                ], className="text-muted small mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Button([
                            html.I(className="fas fa-link me-2"),
                            "Generate Auth URL"
                        ],
                        id="generate-auth-url-btn",
                        color="primary",
                        className="w-100 mb-2")
                    ], width=12)
                ]),
                html.Div(id="auth-url-container", className="mb-3")
            ], className="auth-step mb-4"),

            # Step 2: Callback URL input
            html.Div([
                html.H6([
                    html.Span("2", className="badge bg-success me-2"),
                    "Paste Callback URL"
                ], className="mb-2"),
                html.P([
                    "After authorizing with Schwab, copy the complete URL from your browser's address bar and paste it below."
                ], className="text-muted small mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.InputGroup([
                            dbc.Input(
                                id="callback-url-input",
                                placeholder="https://127.0.0.1/?code=...",
                                type="url",
                                className="form-control-sm"
                            ),
                            dbc.Button([
                                html.I(className="fas fa-check me-1"),
                                "Authenticate"
                            ],
                            id="process-callback-btn",
                            color="success",
                            disabled=True)
                        ])
                    ], width=12)
                ])
            ], className="auth-step mb-4"),

            # Processing indicator
            html.Div([
                dbc.Spinner(
                    html.Div(id="auth-processing-status"),
                    size="sm",
                    color="primary"
                )
            ], id="auth-processing", style={"display": "none"})
        ]),
        dbc.ModalFooter([
            dbc.Row([
                dbc.Col([
                    html.Small([
                        html.I(className="fas fa-info-circle me-1"),
                        "Make sure your Schwab app callback URL is set to: ",
                        html.Code("https://127.0.0.1")
                    ], className="text-muted")
                ], width="auto"),
                dbc.Col([
                    dbc.Button("Cancel", id="auth-modal-close", color="secondary", className="ms-auto")
                ], width="auto")
            ], className="w-100 align-items-center justify-content-between")
        ])
    ],
    id="auth-modal",
    is_open=False,
    backdrop="static",
    keyboard=False,
    size="lg",
    className="auth-modal")

def create_auth_success_alert():
    """Create success alert for completed authentication"""
    return dbc.Alert([
        html.I(className="fas fa-check-circle me-2"),
        html.Strong("Authentication Successful! "),
        "Your Schwab API connection is now active and ready to use."
    ], color="success", dismissable=True, duration=5000)

def create_auth_error_alert(error_message):
    """Create error alert for failed authentication"""
    return dbc.Alert([
        html.I(className="fas fa-exclamation-circle me-2"),
        html.Strong("Authentication Failed: "),
        error_message
    ], color="danger", dismissable=True)

def create_auth_url_display(auth_url):
    """Create the authorization URL display component"""
    return dbc.Card([
        dbc.CardBody([
            html.P("Click the link below to authenticate with Schwab:", className="mb-2 small"),
            html.Div([
                html.A([
                    html.I(className="fas fa-external-link-alt me-2"),
                    "Open Schwab Authentication"
                ],
                href=auth_url,
                target="_blank",
                className="btn btn-outline-primary btn-sm w-100 mb-2"),
                html.Details([
                    html.Summary("Show full URL", className="text-muted small"),
                    html.Code(auth_url, className="small text-break")
                ])
            ])
        ])
    ], className="border-primary", style={"borderWidth": "2px"})

def create_token_expiry_warning(expires_in_seconds):
    """Create warning for expiring tokens"""
    if expires_in_seconds > 600:  # More than 10 minutes
        color = "success"
        icon = "fas fa-check-circle"
        message = f"Token expires in {int(expires_in_seconds / 60)} minutes"
    elif expires_in_seconds > 300:  # 5-10 minutes
        color = "warning"
        icon = "fas fa-clock"
        message = f"Token expires in {int(expires_in_seconds / 60)} minutes - consider refreshing soon"
    else:  # Less than 5 minutes
        color = "danger"
        icon = "fas fa-exclamation-triangle"
        message = "Token expires soon - please re-authenticate"

    return dbc.Alert([
        html.I(className=f"{icon} me-2"),
        message
    ], color=color, className="mb-0")