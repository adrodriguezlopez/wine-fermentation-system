"""
Infrastructure layer for authentication module.

Contains repository implementations and external service integrations.
"""

from .repositories import UserRepository

__all__ = ["UserRepository"]
