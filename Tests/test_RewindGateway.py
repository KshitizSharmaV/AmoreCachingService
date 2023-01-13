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


@pytest.mark.asyncio
async def test_Rewind_given_swipe_task_sucess():
    
    with patch('Gateways.RewindGateway.LikesDislikes_delete_record_from_redis') as mock_f:
        await async_db.collection('LikesDislikes').document("user1").collection("Given").document("user2").delete()

        mock_f.return_value =mock_f({"current_user_id": "user1", "idToBeDeleted": "user2", "childCollectionName":"Given","swipeStatusBetweenUsers":"swipeStatusBetweenUsers"})

        future= await Rewind_given_swipe_task(current_user_id= "user1", swiped_user_id= "user2", swipeStatusBetweenUsers="like",logger = MagicMock())
        
        assert future==None
        
        
@pytest.mark.asyncio
async def test_Rewind_given_swipe_task_failure():
    
    with patch('Gateways.RewindGateway.LikesDislikes_delete_record_from_redis') as mock_f:
        mock_f.side_effect = Exception("Can't get profile")

        future= await Rewind_given_swipe_task(current_user_id= "user1", swiped_user_id= "user2", swipeStatusBetweenUsers="like",logger = MagicMock())
        
        assert future==False


@pytest.mark.asyncio
async def test_Rewind_received_swipe_task_sucess():
    
    with patch('Gateways.RewindGateway.LikesDislikes_delete_record_from_redis') as mock_f:
        await async_db.collection('LikesDislikes').document("user2").collection("Received").document("user1").delete()

        mock_f.return_value =mock_f({"user_id": "user1", "idToBeDeleted": "user2", "childCollectionName":"Given","swipeStatusBetweenUsers":"swipeStatusBetweenUsers"})

        future= await Rewind_received_swipe_task(current_user_id= "user1", swiped_user_id= "user2", swipeStatusBetweenUsers="like",logger = MagicMock())
        
        assert future==None
        

@pytest.mark.asyncio
async def test_Rewind_received_swipe_task_failure():
    
    with patch('Gateways.RewindGateway.LikesDislikes_delete_record_from_redis') as mock_f:
        mock_f.side_effect = Exception("Can't get profile")

        future= await Rewind_received_swipe_task(current_user_id= "user1", swiped_user_id= "user2", swipeStatusBetweenUsers="like",logger = MagicMock())
        
        assert future==False
        
        
