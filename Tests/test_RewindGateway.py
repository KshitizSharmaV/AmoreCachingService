import pytest
import asyncio
from google.cloud import firestore
from Gateways.RewindGateway import Rewind_task_function, Rewind_given_swipe_task, Rewind_received_swipe_task
from Gateways import RewindGateway
from ProjectConf.FirestoreConf import async_db, db
from unittest.mock import patch, AsyncMock
from redis.client import Redis
from app import app
from unittest.mock import MagicMock
import asynctest

from Tests.Utilities.test_base import async_mock_child

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
        future= await Rewind_task_function(current_user_id= "user1", swiped_user_id= "user2", swipeStatusBetweenUsers="like")
        assert future ==[mock_rewind.return_value,mock_swipe.return_value]


    
@pytest.mark.asyncio
async def test_Rewind_task_function_failure():
    with patch('Gateways.RewindGateway.Rewind_given_swipe_task') as mock_rewind, patch('Gateways.RewindGateway.Rewind_received_swipe_task') as mock_swipe:
        mock_rewind.side_effect = Exception("Can't get profile")
        mock_swipe.return_value = await async_mock_child(return_value=[{"current_user_id": "user1", "swiped_user_id": "user2", "swipeStatusBetweenUsers":"like"}])
        future= await Rewind_task_function(current_user_id= "user1", swiped_user_id= "user2", swipeStatusBetweenUsers="like")
        assert future ==False

@pytest.mark.asyncio
async def test_Rewind_given_swipe_task_sucess():
    with patch('Gateways.RewindGateway.LikesDislikes_delete_record_from_redis') as mock_f:
        with patch('Gateways.RewindGateway.async_db') as mock_db:
            mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value.delete.side_effect = async_mock_child
            result = await Rewind_given_swipe_task(current_user_id= "user1", swiped_user_id= "user2", swipeStatusBetweenUsers="like")
            assert result == True


@pytest.mark.asyncio
async def test_Rewind_given_swipe_task_failure():
    with patch('Gateways.RewindGateway.LikesDislikes_delete_record_from_redis') as mock_f:
        with patch('Gateways.RewindGateway.async_db') as mock_db:
            mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value.delete.side_effect = async_mock_child
            mock_f.side_effect = Exception("Raise an exception")
            result = await Rewind_given_swipe_task(current_user_id= "user1", swiped_user_id= "user2", swipeStatusBetweenUsers="like")
            assert result == False


@pytest.mark.asyncio
async def test_Rewind_received_swipe_task_sucess():
    with patch('Gateways.RewindGateway.LikesDislikes_delete_record_from_redis') as mock_f:
        with patch('Gateways.RewindGateway.async_db') as mock_db:
            mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value.delete.side_effect = async_mock_child
            result = await Rewind_received_swipe_task(current_user_id= "user1", swiped_user_id= "user2", swipeStatusBetweenUsers="like")
            assert result == True
            

@pytest.mark.asyncio
async def test_Rewind_received_swipe_task_failure():
    with patch('Gateways.RewindGateway.LikesDislikes_delete_record_from_redis') as mock_f:
        with patch('Gateways.RewindGateway.async_db') as mock_db:
            mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value.delete.side_effect = async_mock_child
            mock_f.side_effect = Exception("Raise an exception")
            result= await Rewind_received_swipe_task(current_user_id= "user1", swiped_user_id= "user2", swipeStatusBetweenUsers="like")
            assert result == False
        
        
