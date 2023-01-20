import pytest
import asyncio
from google.cloud import firestore
from Gateways.RewindGateway import Rewind_task_function, Rewind_given_swipe_task, Rewind_received_swipe_task
from ProjectConf.FirestoreConf import async_db, db
from unittest.mock import patch
from redis.client import Redis
from app import app
from unittest.mock import MagicMock
import asynctest

from Tests.Utilities.test_base import async_mock_parent, async_mock_child

import unittest.mock
import logging

# Create a mock object for the logger
mock_log = unittest.mock.Mock()

# Configure the mock object to redirect logs to stdout
mock_log.addHandler(logging.StreamHandler())

@pytest.mark.asyncio
async def test_Rewind_task_function_success():
    with patch('Gateways.RewindGateway.Rewind_given_swipe_task') as mock_rewind, patch('Gateways.RewindGateway.Rewind_received_swipe_task') as mock_swipe:
        mock_rewind.return_value = await async_mock_child(return_value=[{"current_user_id": "user1", "swiped_user_id": "user2", "swipeStatusBetweenUsers":"like"}])
        mock_swipe.return_value = await async_mock_child(return_value=[{"current_user_id": "user1", "swiped_user_id": "user2", "swipeStatusBetweenUsers":"like"}])
        future= await Rewind_task_function(current_user_id= "user1", swiped_user_id= "user2", swipeStatusBetweenUsers="like",logger = MagicMock())
        assert future ==[mock_rewind.return_value,mock_swipe.return_value]


    
@pytest.mark.asyncio
async def test_Rewind_task_function_failure():
    with patch('Gateways.RewindGateway.Rewind_given_swipe_task') as mock_rewind, patch('Gateways.RewindGateway.Rewind_received_swipe_task') as mock_swipe:
        mock_rewind.side_effect = Exception("Can't get profile")
        mock_swipe.return_value = await async_mock_child(return_value=[{"current_user_id": "user1", "swiped_user_id": "user2", "swipeStatusBetweenUsers":"like"}])
        future= await Rewind_task_function(current_user_id= "user1", swiped_user_id= "user2", swipeStatusBetweenUsers="like",logger = MagicMock())
        assert future ==False

@pytest.mark.asyncio
async def test_Rewind_given_swipe_task_sucess(mocker):
    with patch('Gateways.RewindGateway.LikesDislikes_delete_record_from_redis') as mock_f:
        with patch('Gateways.RewindGateway.async_db') as mock_db:
            result = await Rewind_given_swipe_task(current_user_id= "user1", 
                                    swiped_user_id= "user2", 
                                    swipeStatusBetweenUsers="like",
                                    logger = mock_log)
            # Assert that the function returns True
            assert result == True
            
@pytest.mark.asyncio
async def test_Rewind_given_swipe_task_failure():
    with patch('Gateways.RewindGateway.LikesDislikes_delete_record_from_redis') as mock_f:
        mock_f.side_effect = Exception("Can't get profile")
        future= await Rewind_given_swipe_task(current_user_id= "user1", swiped_user_id= "user2", swipeStatusBetweenUsers="like",logger = MagicMock())
        assert future==False


@pytest.mark.asyncio
async def test_Rewind_received_swipe_task_sucess():
    with patch('Gateways.RewindGateway.LikesDislikes_delete_record_from_redis') as mock_f:
        with patch('ProjectConf.FirestoreConf.async_db') as mock_db:
            firestore_mock = mock_db.return_value
            firestore_mock.collection().document().collection().document().delete.return_value = asynctest.CoroutineMock()
            mock_f.return_value =mock_f({"user_id": "user1", "idToBeDeleted": "user2", "childCollectionName":"Given","swipeStatusBetweenUsers":"swipeStatusBetweenUsers"})
            result = await Rewind_received_swipe_task(current_user_id= "user1", 
                            swiped_user_id= "user2", 
                            swipeStatusBetweenUsers="like",
                            logger = MagicMock())
            assert result == True
            

@pytest.mark.asyncio
async def test_Rewind_received_swipe_task_failure():
    with patch('Gateways.RewindGateway.LikesDislikes_delete_record_from_redis') as mock_f:
        mock_f.side_effect = Exception("Can't get profile")
        future= await Rewind_received_swipe_task(current_user_id= "user1", swiped_user_id= "user2", swipeStatusBetweenUsers="like",logger = MagicMock())
        assert future==False
        
        
