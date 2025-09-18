"""
Base module class for all dashboard modules
"""
from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any, Optional
from dash import html

class BaseModule(ABC):
    """Base class for all dashboard modules"""
    
    def __init__(self, module_id: str, name: str, description: str):
        self.module_id = module_id
        self.name = name  
        self.description = description
        self.data = None
        
    @abstractmethod
    def create_layout(self, ticker: str) -> html.Div:
        """Create the module layout"""
        pass
        
    @abstractmethod
    def update_data(self, ticker: str, **kwargs) -> Optional[pd.DataFrame]:
        """Update module data"""
        pass
        
    @abstractmethod
    def create_visualizations(self) -> Dict[str, Any]:
        """Create module-specific visualizations"""
        pass
        
    def get_status(self) -> Dict[str, Any]:
        """Get module status info"""
        return {
            "has_data": self.data is not None,
            "data_count": len(self.data) if self.data is not None else 0,
            "last_updated": getattr(self, "_last_updated", None)
        }