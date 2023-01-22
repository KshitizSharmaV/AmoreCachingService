import pytest
from unittest.mock import MagicMock
from unittest.mock import patch
from Gateways.LikesDislikesGateway import LikesDislikes_async_store_likes_dislikes_superlikes_for_user, LikesDislikes_get_profiles_already_seen_by_id
from Tests.Utilities.test_base import async_mock_child


@pytest.mark.asyncio
async def test_LikesDislikes_async_store_likes_dislikes_superlikes_for_user_success():
    with patch('Gateways.LikesDislikesGateway.LikesDislikes_async_store_swipe_task') as store_swipe_task:
        store_swipe_task.return_value = await async_mock_child(return_value=True)
        with patch('Gateways.MatchUnmatchGateway.MatchUnmatch_check_match_between_users') as check_match_between_users:
            check_match_between_users.return_value = await async_mock_child(return_value=True)
            future = await LikesDislikes_async_store_likes_dislikes_superlikes_for_user(
                currentUserId="UserId1",
                swipedUserId="UserId2",
                swipeStatusBetweenUsers="Match",
                upgradeLikeToSuperlike=True)
            assert future == [True,True,True]
            
      
@pytest.mark.asyncio
async def test_LikesDislikes_async_store_likes_dislikes_superlikes_for_user_failure():
    with patch('Gateways.LikesDislikesGateway.LikesDislikes_async_store_swipe_task') as store_swipe_task:
        store_swipe_task.side_effect = Exception("Can't get likes and dislikes for user id")
        with patch('Gateways.MatchUnmatchGateway.MatchUnmatch_check_match_between_users') as check_match_between_users:
            check_match_between_users.return_value = await async_mock_child(return_value=True)
            future = await LikesDislikes_async_store_likes_dislikes_superlikes_for_user(
                currentUserId="UserId1",
                swipedUserId="UserId2",
                swipeStatusBetweenUsers="Match",
                upgradeLikeToSuperlike=True)
            assert future == False     

      
@pytest.mark.asyncio
async def test_LikesDislikes_get_profiles_already_seen_by_id():
    # Set up the mocks
    with patch('Gateways.LikesDislikesGateway.LikesDislikes_fetch_userdata_from_firebase_or_redis') as fetch_user_data:
        fetch_user_data.return_value = await async_mock_child(return_value=[{'user1':'abc'},{'user2':'xyz'}])
        result = await LikesDislikes_get_profiles_already_seen_by_id(userId="UserId1",childCollectionName="ABC")
        assert result == [{'user1':'abc'},{'user2':'xyz'},{'user1':'abc'},{'user2':'xyz'},{'user1':'abc'},{'user2':'xyz'}]
