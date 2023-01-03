import pytest
from unittest.mock import MagicMock
from unittest.mock import patch
from Gateways.LikesDislikesGateway import LikesDislikes_async_store_likes_dislikes_superlikes_for_user, LikesDislikes_get_profiles_already_seen_by_id
from Gateways.LikesDislikesGatewayEXT import LikesDislikes_fetch_userdata_from_firebase_or_redis, \
    LikesDislikes_async_store_swipe_task
from Gateways.MatchUnmatchGateway import MatchUnmatch_check_match_between_users
from ProjectConf.AsyncioPlugin import run_coroutine
from app import app

#TODO - @Piyush to fix this testcase
@pytest.mark.asyncio
async def test_LikesDislikes_async_store_likes_dislikes_superlikes_for_user():
    # Set up mock dependencies
    with patch.object(LikesDislikes_async_store_swipe_task, "__call__", return_value=True):
        with patch.object(MatchUnmatch_check_match_between_users, "__call__", return_value=True):
            # Call the function being tested
            future = run_coroutine(LikesDislikes_async_store_likes_dislikes_superlikes_for_user(
                currentUserId="UserId1",
                swipedUserId="UserId2",
                swipeStatusBetweenUsers="Match",
                upgradeLikeToSuperlike=True,
                logger = MagicMock()))
            res = future.result()
            