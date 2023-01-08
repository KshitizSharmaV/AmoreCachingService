import pytest
from unittest.mock import MagicMock
from unittest.mock import patch
from Gateways.LikesDislikesGateway import LikesDislikes_async_store_likes_dislikes_superlikes_for_user, LikesDislikes_get_profiles_already_seen_by_id
from Tests.test_base import async_mock_child


@pytest.mark.asyncio
async def test_LikesDislikes_async_store_likes_dislikes_superlikes_for_user():
    
    # Set up the mocks
    with patch('Gateways.LikesDislikesGateway.LikesDislikes_async_store_swipe_task') as store_swipe_task:
        store_swipe_task.return_value = await async_mock_child(return_value=True)
        with patch('Gateways.MatchUnmatchGateway.MatchUnmatch_check_match_between_users') as check_match_between_users:
            check_match_between_users.return_value = await async_mock_child(return_value=True)
            future = await LikesDislikes_async_store_likes_dislikes_superlikes_for_user(
                currentUserId="UserId1",
                swipedUserId="UserId2",
                swipeStatusBetweenUsers="Match",
                upgradeLikeToSuperlike=True,
                logger = MagicMock())
            assert future == [True,True,True]