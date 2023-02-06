import pytest
from unittest.mock import patch, AsyncMock
from Gateways.MatchUnmatchGateway import RecentChats_Unmatch_Delete_Chat
from Tests.Utilities.test_base import client, async_mock_child
import asyncio




@pytest.mark.asyncio
async def test_RecentChats_Unmatch_Delete_Chat_success():
    
    # Set up the mocks
    with patch("Gateways.RecentChatsGateway.async_db") as mock_async_db:
        mock_recent_chat_ref = mock_async_db.collection.return_value.document.return_value.collection.return_value.document.return_value
        mock_recent_chat_ref.delete.return_value = asyncio.Future()
        mock_recent_chat_ref.delete.return_value.set_result(True)
        

        # Prepare the test data
        user_id_1 = "12345"
        user_id_2 = "67890"

        # Call the function to test
        result = await RecentChats_Unmatch_Delete_Chat(user_id_1, user_id_2)

        # Assert the expected results
        assert result == True
        

@pytest.mark.asyncio
async def test_RecentChats_Unmatch_Delete_Chat_failure():
    
    # Set up the mocks
    with patch("Gateways.RecentChatsGateway.async_db") as mock_async_db:
        mock_recent_chat_ref = mock_async_db.collection.return_value.document.return_value.collection.return_value.document.return_value
        mock_recent_chat_ref.delete.side_effect = Exception("Can't get profiles for the ID")

        # Prepare the test data
        user_id_1 = "12345"
        user_id_2 = "67890"

        # Call the function to test
        result = await RecentChats_Unmatch_Delete_Chat(user_id_1, user_id_2)

        # Assert the expected results
        assert result == False
        
        