"""
Authentication views module.
"""
from .register_view import RegisterView
from .login_view import LoginView
from .refresh_view import RefreshView
from .logout_view import LogoutView
from .protected_view import protected_endpoint

__all__ = [
    'RegisterView',
    'LoginView', 
    'RefreshView',
    'LogoutView',
    'protected_endpoint',
]