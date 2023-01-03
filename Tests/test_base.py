import unittest
from unittest.mock import patch, AsyncMock
import json
from app import app


async def async_mock_parent(return_value=None, side_effect=None):
    """Helper function to create an async mock"""
    mock = AsyncMock(return_value=return_value, side_effect=side_effect)
    return mock

async def async_mock_child(return_value=None):
    """Call this function when you want to await response from a function being mocked
    
    Args:
        return_value:Pass the return value you want to return from awaited function
    """
    "Used to await mock object response from functions"
    return return_value

