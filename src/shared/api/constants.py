"""
Shared API constants.

Import this module wherever the API version prefix is needed, instead of
hard-coding the string literal "/api/v1".

Usage:
    from src.shared.api.constants import API_V1_PREFIX

    app.include_router(my_router, prefix=API_V1_PREFIX)
"""

API_V1_PREFIX: str = "/api/v1"
