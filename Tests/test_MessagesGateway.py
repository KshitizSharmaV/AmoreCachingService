import pytest
from unittest.mock import patch, AsyncMock
from Gateways.MessagesGateway import *
from Tests.Utilities.test_base import client, async_mock_child
import asyncio
from ProjectConf.AsyncioPlugin import run_coroutine


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
async def test_match_two_profiles_for_direct_message_success():
    current_user_id= "UserId123"
    other_user_id = "UserId456"
    with patch('Gateways.MessagesGateway.LikesDislikes_async_store_likes_dislikes_superlikes_for_user') as mock_f:
        mock_f.return_value1 = await async_mock_child(return_value=True)
        mock_f.return_value2 = await async_mock_child(return_value=True)
        result = await match_two_profiles_for_direct_message(current_user_id=current_user_id, other_user_id=other_user_id)
        result == [True, True]

# TODO not working
@pytest.mark.asyncio
async def test_match_two_profiles_for_direct_message_failure():
    current_user_id= "UserId123"
    other_user_id = "UserId456"
    with patch('Gateways.MessagesGateway.LikesDislikes_async_store_likes_dislikes_superlikes_for_user') as mock_f:
        mock_f.side_effect = Exception("Raise Exception")
        result = await match_two_profiles_for_direct_message(current_user_id=current_user_id, other_user_id=other_user_id)
        assert result == False


         


