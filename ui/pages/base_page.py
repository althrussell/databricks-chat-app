# ui/pages/base_page.py - Base class for all page renderers
from abc import ABC, abstractmethod

class BasePage(ABC):
    """Base class for all page renderers"""
    
    def __init__(self, state_manager, model_service, conversation_service):
        """Initialize base page"""
        self.state_manager = state_manager
        self.model_service = model_service
        self.conversation_service = conversation_service
    
    @abstractmethod
    def render(self):
        """Render the page content"""
        pass