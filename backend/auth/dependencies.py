"""
Authentication dependencies
"""
from .jwt import get_current_admin
from fastapi import Depends

get_current_admin_dependency = Depends(get_current_admin)

