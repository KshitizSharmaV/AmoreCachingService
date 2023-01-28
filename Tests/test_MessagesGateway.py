import pytest
from unittest.mock import patch, AsyncMock
from Gateways.MessagesGateway import *
from Tests.Utilities.test_base import client, async_mock_child
import asyncio



@pytest.mark.asyncio
async def test_unmatch_task_recent_chats_success():
    
    # Set up the mocks
    with patch("Gateways.MessagesGateway.async_db") as mock_async_db:
        mock_recent_chat_ref = mock_async_db.collection.return_value.document.return_value.collection.return_value.document.return_value
        mock_recent_chat_ref.delete.return_value = asyncio.Future()
        mock_recent_chat_ref.delete.return_value.set_result(True)
        

        # Prepare the test data
        user_id_1 = "12345"
        user_id_2 = "67890"

        # Call the function to test
        result = await unmatch_task_recent_chats(user_id_1, user_id_2)

        # Assert the expected results
        assert result == None
    
    
@pytest.mark.asyncio
async def test_match_two_profiles_for_direct_message():
    
    profileIdList = ['user1','user2']
    # Set up the mocks
    with patch('Gateways.LikesDislikes_async_store_likes_dislikes_superlikes_for_user') as mock_f:
        mock_f.return_value1 = await async_mock_child(return_value=[{"currentUserId": "123", "swipedUserId": "456", "swipeStatusBetweenUsers":'Superlikes'}])
        mock_f.return_value2 = await async_mock_child(return_value=[{"currentUserId": "456", "swipedUserId": "123", "swipeStatusBetweenUsers":'Superlikes'}])

        
        # Check the response
        pass
    


