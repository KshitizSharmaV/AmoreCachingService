import pytest
import asyncio
from google.cloud import firestore
from Gateways.RewindGateway import *
from ProjectConf.FirestoreConf import async_db, db
from unittest.mock import patch
from redis.client import Redis
from app import app
from unittest.mock import MagicMock

from Tests.test_base import async_mock_parent, async_mock_child



@pytest.mark.asyncio
async def test_Rewind_task_function_success():
    
    
    #mock functions
    with patch('Gateways.RewindGateway.Rewind_given_swipe_task') as mock_rewind, patch('Gateways.RewindGateway.Rewind_received_swipe_task') as mock_swipe:
        
        mock_rewind.return_value = await async_mock_child(return_value=[{"current_user_id": "user1", "swiped_user_id": "user2", "swipeStatusBetweenUsers":"like"}])
        mock_swipe.return_value = await async_mock_child(return_value=[{"current_user_id": "user1", "swiped_user_id": "user2", "swipeStatusBetweenUsers":"like"}])
        
        future= await Rewind_task_function(current_user_id= "user1", swiped_user_id= "user2", swipeStatusBetweenUsers="like",logger = MagicMock())
        
        assert future ==[mock_rewind.return_value,mock_swipe.return_value]


    
@pytest.mark.asyncio
async def test_Rewind_task_function_failure():
    
    
    #mock functions
    with patch('Gateways.RewindGateway.Rewind_given_swipe_task') as mock_rewind, patch('Gateways.RewindGateway.Rewind_received_swipe_task') as mock_swipe:
        
        mock_rewind.side_effect = Exception("Can't get profile")
        mock_swipe.return_value = await async_mock_child(return_value=[{"current_user_id": "user1", "swiped_user_id": "user2", "swipeStatusBetweenUsers":"like"}])
        
        future= await Rewind_task_function(current_user_id= "user1", swiped_user_id= "user2", swipeStatusBetweenUsers="like",logger = MagicMock())
        
        assert future ==False
