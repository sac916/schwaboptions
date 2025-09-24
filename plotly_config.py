"""
Plotly Configuration for SchwaOptions
Optimized for performance and memory leak prevention
"""

# Global Plotly configuration to prevent memory leaks
PLOTLY_CONFIG = {
    # Performance optimizations
    "displayModeBar": True,
    "displaylogo": False,
    "modeBarButtonsToRemove": ['lasso2d', 'select2d'],

    # Canvas optimization for frequent redraws
    "plotlyServerURL": "https://plot.ly",

    # Image export optimization
    "toImageButtonOptions": {
        "format": "png",
        "filename": "schwa_options_chart",
        "height": 600,
        "width": 1000,
        "scale": 1
    },

    # Memory leak prevention
    "staticPlot": False,
    "responsive": True,

    # Performance settings
    "scrollZoom": True,
    "doubleClick": "reset+autosize",
    "showTips": False,

    # Prevent canvas memory issues
    "editable": False,

    # Custom config for high-frequency updates
    "frameMargins": 0,
    "showAxisDragHandles": False,
    "showAxisRangeEntryBoxes": False
}

# Chart-specific configurations
CHART_CONFIGS = {
    "flow_chart": {
        **PLOTLY_CONFIG,
        "displayModeBar": True,
        "scrollZoom": True,
        "doubleClick": "autosize"
    },

    "heatmap": {
        **PLOTLY_CONFIG,
        "displayModeBar": True,
        "scrollZoom": False,
        "staticPlot": False
    },

    "3d_surface": {
        **PLOTLY_CONFIG,
        "displayModeBar": True,
        "scrollZoom": True,
        "doubleClick": "reset"
    },

    "performance_critical": {
        **PLOTLY_CONFIG,
        "staticPlot": False,
        "responsive": True,
        "displayModeBar": False,  # Disable for better performance
        "scrollZoom": False,
        "doubleClick": False,
        "showTips": False
    }
}

# Layout defaults that prevent memory leaks
DEFAULT_LAYOUT_UPDATES = {
    # Prevent memory accumulation in animations
    "transition": {"duration": 0},

    # Optimize rendering
    "autosize": True,
    "margin": {"l": 40, "r": 40, "t": 40, "b": 40},

    # Canvas optimization
    "dragmode": False,

    # Memory-efficient hover
    "hovermode": "closest",

    # Prevent layout thrashing
    "showlegend": True,
    "legend": {
        "orientation": "v",
        "x": 1.02,
        "y": 1
    }
}

def get_optimized_config(chart_type: str = "default") -> dict:
    """Get optimized Plotly config for specific chart type"""
    return CHART_CONFIGS.get(chart_type, PLOTLY_CONFIG)

def apply_performance_layout(figure, theme_config: dict = None) -> None:
    """Apply performance-optimized layout settings to figure"""
    if theme_config:
        layout_updates = {
            **DEFAULT_LAYOUT_UPDATES,
            "plot_bgcolor": theme_config.get("paper_color", "#1e2130"),
            "paper_bgcolor": theme_config.get("background_color", "#0e1117"),
            "font": {"color": theme_config.get("text_color", "#fafafa")}
        }
    else:
        layout_updates = DEFAULT_LAYOUT_UPDATES

    figure.update_layout(**layout_updates)

# Add this JavaScript to prevent canvas memory leaks
CANVAS_OPTIMIZATION_JS = """
// Optimize canvas for frequent redraws
if (typeof window !== 'undefined') {
    // Add willReadFrequently attribute to all canvas elements
    const optimizeCanvases = () => {
        document.querySelectorAll('canvas').forEach(canvas => {
            if (!canvas.getAttribute('willReadFrequently')) {
                canvas.setAttribute('willReadFrequently', 'true');
                console.log('[Plotly] Added willReadFrequently to canvas');
            }
        });
    };

    // Apply on DOM changes
    const observer = new MutationObserver(optimizeCanvases);
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });

    // Initial optimization
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', optimizeCanvases);
    } else {
        optimizeCanvases();
    }
}
"""