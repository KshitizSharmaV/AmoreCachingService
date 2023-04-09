
import pytest
from unittest.mock import patch

from Gateways.MatchUnmatchGateway import *
from Gateways.MatchUnmatchGatewayEXT import MatchUnmatch_delete_record_from_redis, RecentChats_Unmatch_Delete_Chat
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


@pytest.mark.asyncio
async def test_MatchUnmatch_send_message_notification_success():
    with patch('Gateways.MatchUnmatchGateway.Notification_design_and_multicast') as mock_notification_design_multicast:
        mock_notification_design_multicast.return_value = await async_mock_child(return_value=True)
        result= await MatchUnmatch_send_message_notification(user_id='UserId123')
        assert result==True

        
@pytest.mark.asyncio
async def test_MatchUnmatch_send_message_notification_failure():
    with patch('Gateways.MatchUnmatchGateway.Notification_design_and_multicast') as mock_notification_design_multicast:
        mock_notification_design_multicast.side_effect = Exception("Notification sending failed")
        result= await MatchUnmatch_send_message_notification(user_id='UserId123')
        assert result==False


@pytest.mark.asyncio
async def test_MatchUnmatch_check_match_between_users_success():
    swipedUserSwipe = 'Superlikes'
    currentUserId = "1"
    swipedUserId = "2"
    
    with patch('Gateways.MatchUnmatchGateway.async_db') as mock_async_db:         
        with patch('Gateways.MatchUnmatchGateway.LikesDislikes_fetch_users_given_swipes') as mock_fetch, patch('Gateways.MatchUnmatchGateway.MatchUnmatch_store_match_or_nomatch') as mock_match, patch('Gateways.MatchUnmatchGateway.MatchUnmatch_write_to_recent_chats') as mock_chats, patch('Gateways.MatchUnmatchGateway.MatchUnmatch_send_message_notification') as mock_not:
            likesGivenBySwipedUser='1'
            superlikesGivenBySwipedUser='1'
            mock_fetch.return_value = (likesGivenBySwipedUser, [], superlikesGivenBySwipedUser)

            result= await MatchUnmatch_check_match_between_users('1','2','Superlikes')
            assert result==True
             


@pytest.mark.asyncio
async def test_MatchUnmatch_check_match_between_users_failure():
    with patch('Gateways.MatchUnmatchGateway.async_db') as mock_async_db:
        with patch('Gateways.MatchUnmatchGateway.LikesDislikes_fetch_users_given_swipes') as mock_fetch, patch('Gateways.MatchUnmatchGateway.MatchUnmatch_store_match_or_nomatch') as mock_match, patch('Gateways.MatchUnmatchGateway.MatchUnmatch_write_to_recent_chats') as mock_chats, patch('Gateways.MatchUnmatchGateway.MatchUnmatch_send_message_notification') as mock_not:
            # Simulate the failure scenario
            mock_fetch.side_effect = Exception("Error while fetching the likes and dislikes")

            # Call the function
            result = await MatchUnmatch_check_match_between_users(currentUserId='1', swipedUserId='2', currentUserSwipe='Superlikes')

            # Verify that the function returns False
            assert result == False



@pytest.mark.asyncio
async def test_MatchUnmatch_fetch_userdata_from_firebase_or_redis_success():
    userId='UserId123'
    childCollectionName='Match'

    with patch('Gateways.MatchUnmatchGateway.async_db') as mock_async_db:
        with patch('Gateways.MatchUnmatchGateway.redis_client') as mock_redis_client:
            # Mocking redis_client by fetching the scard value
            mock_redis_client.scard.return_value = 1
            with patch('Gateways.MatchUnmatchGateway.MatchUnmatch_fetch_data_from_redis') as matchunnmatch_mock_redis_fetch:
                matchunnmatch_mock_redis_fetch.return_value = ['UserId234']
                result = await MatchUnmatch_fetch_userdata_from_firebase_or_redis(userId=userId, childCollectionName=childCollectionName)
                assert result == ['UserId234']
            
            mock_redis_client.scard.return_value = 0
            mock_async_db.collection.return_value.documen.return_value.collection.return_value.order_by.return_value = ['UserId234']
            with patch('Gateways.MatchUnmatchGateway.MatchUnmatch_store_match_unmatch_to_redis') as matchunnmatch_store:
                matchunnmatch_store.return_value = ['UserId234']
                result = await MatchUnmatch_fetch_userdata_from_firebase_or_redis(userId=userId, childCollectionName=childCollectionName)
                assert result == ['UserId234']
 
 

@pytest.mark.asyncio
async def test_MatchUnmatch_fetch_userdata_from_firebase_or_redis_failure():
    userId='UserId123'
    childCollectionName='Match'

    with patch('Gateways.MatchUnmatchGateway.async_db') as mock_async_db:
        with patch('Gateways.MatchUnmatchGateway.redis_client') as mock_redis_client:
            # Mocking redis_client by fetching the scard value
            mock_redis_client.scard.return_value = 1
            with patch('Gateways.MatchUnmatchGateway.MatchUnmatch_fetch_data_from_redis') as matchunnmatch_mock_redis_fetch:
                matchunnmatch_mock_redis_fetch.side_effect = []
                result = await MatchUnmatch_fetch_userdata_from_firebase_or_redis(userId=0, childCollectionName=childCollectionName)
                assert result == []
            
            mock_redis_client.scard.return_value = 0
            mock_async_db.collection.return_value.documen.return_value.collection.return_value.order_by.return_value = ['UserId234']
            with patch('Gateways.MatchUnmatchGateway.MatchUnmatch_fetch_data_from_redis') as matchunnmatch_mock_redis_fetch:
                matchunnmatch_mock_redis_fetch.side_effect = ['UserId234']
                assert result == []
            
 


@pytest.mark.asyncio
async def test_MatchUnmatch_fetch_data_from_redis_success():
    userId='UserId123'
    childCollectionName='Match'

    with patch('Gateways.MatchUnmatchGateway.async_db') as mock_async_db:
        with patch('Gateways.MatchUnmatchGateway.redis_client') as mock_redis_client:
            mock_redis_client.smembers.return_value = ['UserId234']
            # Mocking redis_client by fetching the scard value
            profileIds = list(mock_redis_client.smembers.return_value)
            result = await MatchUnmatch_fetch_data_from_redis(userId=userId, childCollectionName=childCollectionName)
            assert result == ['UserId234']
                
                
@pytest.mark.asyncio
async def test_MatchUnmatch_fetch_data_from_redis_failure():
    userId='UserId123'
    childCollectionName='Match'

    with patch('Gateways.MatchUnmatchGateway.async_db') as mock_async_db:
        with patch('Gateways.MatchUnmatchGateway.redis_client') as mock_redis_client:
            mock_redis_client.smembers.side_effect = Exception("Unablet to fetch")
            # Mocking redis_client by fetching the scard value
            profileIds = list(mock_redis_client.smembers.return_value)
            result = await MatchUnmatch_fetch_data_from_redis(userId=userId, childCollectionName=childCollectionName)
            assert result == []
                
           

def test_MatchUnmatch_calculate_the_match_success():
    
    
    assert MatchUnmatch_calculate_the_match("Likes", "Likes") == "Match"
    assert MatchUnmatch_calculate_the_match("Likes", "Superlikes") == "Match"
    assert MatchUnmatch_calculate_the_match("Likes", "Dislikes") == "NoMatch"
    assert MatchUnmatch_calculate_the_match("Superlikes", "Likes") == "Match"
    assert MatchUnmatch_calculate_the_match("Superlikes", "Dislikes") == "NoMatch"
    assert MatchUnmatch_calculate_the_match("Superlikes", "Superlikes") == "Match"
    assert MatchUnmatch_calculate_the_match("Dislikes", "Superlikes") == "NoMatch"
    assert MatchUnmatch_calculate_the_match("Dislikes", "Likes") == "NoMatch"
    assert MatchUnmatch_calculate_the_match("Dislikes", "Dislikes") == "NoMatch"


def test_MatchUnmatch_calculate_the_match_failure():
    
    assert MatchUnmatch_calculate_the_match(42, "Likes") == False
    
    
@pytest.mark.asyncio
async def test_MatchUnmatch_delete_record_from_redis_success():
    
    userId1='UserId123'
    userId2='UserId234'
    childCollectionName=None

    with patch('Gateways.MatchUnmatchGateway.async_db') as mock_async_db:
        with patch('Gateways.MatchUnmatchGateway.redis_client') as mock_redis_client:
            mock_redis_client.smembers.return_value = ['UserId234']
            # Mocking redis_client by fetching the scard value
            allUserMatchOrUnmatches = list(mock_redis_client.smembers.return_value)
            result = await MatchUnmatch_delete_record_from_redis(user_id_1=userId1, user_id_2= None, childCollectionName=childCollectionName)
            assert result == True


@pytest.mark.asyncio
async def test_MatchUnmatch_delete_record_from_redis_failure():
    
    userId1='UserId123'
    userId2='UserId234'
    childCollectionName=None

    with patch('Gateways.MatchUnmatchGateway.async_db') as mock_async_db:
        with patch('Gateways.MatchUnmatchGateway.redis_client') as mock_redis_client:
            mock_redis_client.smembers.side_effect = Exception("No value")
            # Mocking redis_client by fetching the scard value
            allUserMatchOrUnmatches = list(mock_redis_client.smembers.return_value)
            result = await MatchUnmatch_delete_record_from_redis(user_id_1=userId1, user_id_2= None, childCollectionName=childCollectionName)
            assert result == False

@pytest.mark.asyncio
async def test_RecentChats_Unmatch_Delete_Chat_success():
    # Set up the mocks
    with patch("Gateways.MatchUnmatchGateway.async_db") as mock_async_db:
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
    with patch("Gateways.MatchUnmatchGateway.async_db") as mock_async_db:
        mock_recent_chat_ref = mock_async_db.collection.return_value.document.return_value.collection.return_value.document.return_value
        mock_recent_chat_ref.delete.side_effect = Exception("Can't get profiles for the ID")
        # Prepare the test data
        user_id_1 = "12345"
        user_id_2 = "67890"
        # Call the function to test
        result = await RecentChats_Unmatch_Delete_Chat(user_id_1, user_id_2)
        # Assert the expected results
        assert result == False
        
        