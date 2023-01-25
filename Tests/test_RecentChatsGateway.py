import pytest
from unittest.mock import patch, AsyncMock
from Gateways.RecentChatsGateway import RecentChats_Unmatch_Delete_Chat
from Tests.Utilities.test_base import client, async_mock_child




@pytest.mark.asyncio
async def test_RecentChats_Unmatch_Delete_Chat():
    
    # Set up the mocks
    with patch("Gateways.RecentChatsGateway.async_db") as mock_async_db:
        mock_recent_chat_ref = mock_async_db.collection.return_value.document.return_value.collection.return_value.document.return_value
        mock_recent_chat_ref.delete.side_effect = await async_mock_child(return_value=True)

        # Prepare the test data
        user_id_1 = "12345"
        user_id_2 = "67890"

        # Call the function to test
        result = await RecentChats_Unmatch_Delete_Chat(user_id_1, user_id_2)

        # Assert the expected results
        assert result == True
        
        