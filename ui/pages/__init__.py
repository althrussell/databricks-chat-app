# ui/pages/__init__.py - Page module exports
from .base_page import BasePage
from .chat_page import ChatPage
from .history_page import HistoryPage
from .analytics_page import AnalyticsPage
from .settings_page import SettingsPage

__all__ = [
    'BasePage',
    'ChatPage', 
    'HistoryPage',
    'AnalyticsPage',
    'SettingsPage'
]