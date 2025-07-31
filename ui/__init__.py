# ui/__init__.py - UI module exports
from .styling import apply_executive_styling
from .sidebar import SidebarRenderer
from .main_content import MainContentRenderer

__all__ = [
    'apply_executive_styling',
    'SidebarRenderer',
    'MainContentRenderer'
]