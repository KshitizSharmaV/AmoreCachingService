import pytest
from unittest.mock import patch, AsyncMock
from Gateways.MatchUnmatchGateway import *
from Tests.Utilities.test_base import async_mock_child
import asyncio
from unittest.mock import call



@pytest.mark.asyncio
async def test_MatchUnmatch_get_match_unmatch_nomatch_for_user_success():
    with patch("Gateways.MatchUnmatchGateway.MatchUnmatch_fetch_userdata_from_firebase_or_redis") as mock_fetch_userdata:
        userId = "123"
        mock_fetch_userdata.return_value = "mock data"
        result = await MatchUnmatch_get_match_unmatch_nomatch_for_user(userId)
        # assert that the function was called with the correct arguments
        assert mock_fetch_userdata.await_count == 3
        assert mock_fetch_userdata.await_args_list == [
            call(userId='123', childCollectionName='Match'),
            call(userId='123', childCollectionName='Unmatch'),
            call(userId='123', childCollectionName='NoMatch')
         ]
        assert result == ["mock data", "mock data", "mock data"]
        
@pytest.mark.asyncio
async def test_MatchUnmatch_store_match_or_nomatch_success():
    match_status = 'match'
    currentUserId = 'user1'
    swipedUserId = 'user2'

    with patch('Gateways.MatchUnmatchGateway.async_db') as mock_async_db:
        mock_current_doc_ref = mock_async_db.collection.return_value.document.return_value.collection.return_value.document.return_value
        mock_other_doc_ref = mock_async_db.collection.return_value.document.return_value.collection.return_value.document.return_value
        mock_current_doc_ref.set.side_effect = [async_mock_child(return_value=True), async_mock_child(return_value=True)]
        with patch('Gateways.MatchUnmatchGateway.redis_client') as mock_redis_client:
            mock_redis_client.sadd.return_value = None
            result = await MatchUnmatch_store_match_or_nomatch(currentUserId=currentUserId, 
                                                            swipedUserId=swipedUserId,
                                                            match_status=match_status)
            assert result == True

@pytest.mark.asyncio
async def test_MatchUnmatch_store_match_or_nomatch_failure():
    match_status = 'match'
    currentUserId = 'user1'
    swipedUserId = 'user2'
    """
    Special case - To mock two different Firestore calls in the same function, you need to use side_effect in the mock object. You can specify a list of return values and each time the mock is called, it will return the next value in the list.
    """
    with patch('Gateways.MatchUnmatchGateway.async_db') as mock_async_db:
        mock_current_doc_ref = mock_async_db.collection.return_value.document.return_value.collection.return_value.document.return_value
        mock_other_doc_ref = mock_async_db.collection.return_value.document.return_value.collection.return_value.document.return_value
        mock_current_doc_ref.set.side_effect = [Exception("Raise a test exception"), async_mock_child(return_value=True)]
        with patch('Gateways.MatchUnmatchGateway.redis_client') as mock_redis_client:
            mock_redis_client.sadd.return_value = None
            result = await MatchUnmatch_store_match_or_nomatch(currentUserId=currentUserId, swipedUserId=swipedUserId,match_status=match_status)
            assert result == False
    




 
