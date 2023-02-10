import pytest
import json
from unittest.mock import patch, MagicMock
from app import app
from Tests.Utilities.test_base import redis_test_set, async_mock_child
from Gateways.LikesDislikesGatewayEXT import *

logger = configure_logger(__name__)

@pytest.mark.asyncio
async def test_LikesDislikes_fetch_userdata_from_firebase_or_redis_success():
    user_id="UserId1234"
    child_collection_name="Given"
    swipe_info="Likes"
    no_of_last_records=5
    with patch('Gateways.LikesDislikesGatewayEXT.redis_client') as mock_redis_client:
        mock_redis_client.zcard.return_value = 1
        with patch('Gateways.LikesDislikesGatewayEXT.LikesDislikes_fetch_data_from_redis') as mock_fetch_data_from_redis: 
            mock_fetch_data_from_redis.return_value =  await async_mock_child(return_value=['UserId345'])
            result = await LikesDislikes_fetch_userdata_from_firebase_or_redis(userId=user_id, 
                    childCollectionName=child_collection_name,
                    swipeStatusBetweenUsers=swipe_info,
                    no_of_last_records=no_of_last_records)
            assert result == ['UserId345']
    
    with patch('Gateways.LikesDislikesGatewayEXT.redis_client') as mock_redis_client:
        mock_redis_client.zcard.return_value = 0
        # this will be a firestore streaming 
        profile_docs = ['profile_doc_1','profile_doc_2']
        profile_ids = ['UserId123','UserId234']
        with patch('Gateways.LikesDislikesGatewayEXT.async_db') as mock_async_db: 
            mock_async_db.return_value.collection.return_value.document.return_value.where.return_value.order_by.return_value = profile_docs
            with patch('Gateways.LikesDislikesGatewayEXT.LikesDislikes_store_likes_dislikes_match_unmatch_to_redis') as mock_store_to_redis:
                mock_store_to_redis.return_value =  await async_mock_child(return_value=['UserId345'])
                result = await LikesDislikes_fetch_userdata_from_firebase_or_redis(userId=user_id, 
                        childCollectionName=child_collection_name,
                        swipeStatusBetweenUsers=swipe_info,
                        no_of_last_records=no_of_last_records)
                assert result == ['UserId345']

@pytest.mark.asyncio
async def test_LikesDislikes_fetch_userdata_from_firebase_or_redis_failure():
    user_id="UserId1234"
    child_collection_name="Given"
    swipe_info="Likes"
    no_of_last_records=5
    with patch('Gateways.LikesDislikesGatewayEXT.redis_client') as mock_redis_client:
        mock_redis_client.zcard.return_value = 1
        with patch('Gateways.LikesDislikesGatewayEXT.LikesDislikes_fetch_data_from_redis') as mock_fetch_data_from_redis: 
            mock_fetch_data_from_redis.side_effect = Exception("Raise a testing exception") 
            result = await LikesDislikes_fetch_userdata_from_firebase_or_redis(userId=user_id, 
                            childCollectionName=child_collection_name,
                            swipeStatusBetweenUsers=swipe_info,
                            no_of_last_records=no_of_last_records)
            assert result == []
        
@pytest.mark.asyncio
async def test_LikesDislikes_fetch_data_from_redis_success():
    user_id = "UserId1234"
    child_collection_name = "Given"
    swipe_info = "Likes"
    no_of_last_records = 5
    with patch('Gateways.LikesDislikesGatewayEXT.redis_client') as mock_redis_client:
        mock_redis_client.zrevrange.return_value = ['UserId345']
        result = await LikesDislikes_fetch_data_from_redis(userId=user_id,
            childCollectionName=child_collection_name,
            swipeStatusBetweenUsers=swipe_info,
            no_of_last_records=no_of_last_records)
        assert result == ['UserId345']

        result = await LikesDislikes_fetch_data_from_redis(userId=user_id,
            childCollectionName=child_collection_name,
            swipeStatusBetweenUsers=swipe_info)
        assert result == ['UserId345']

@pytest.mark.asyncio
async def test_LikesDislikes_fetch_data_from_redis_failure():
    user_id = "UserId1234"
    child_collection_name = "Given"
    swipe_info = "Likes"
    no_of_last_records = 5
    with patch('Gateways.LikesDislikesGatewayEXT.redis_client') as mock_redis_client:
        mock_redis_client.zrevrange.return_value = Exception("Testing exception raised")
        result = await LikesDislikes_fetch_data_from_redis(userId=user_id,
            childCollectionName=child_collection_name,
            swipeStatusBetweenUsers=swipe_info,
            no_of_last_records=no_of_last_records)
        assert result == []

@pytest.mark.asyncio
async def test_LikesDislikes_delete_record_from_redis_success():
    user_id = "UserId1234"
    idToBeDeleted = 'ProfileId123'
    idToBeDeleted_not_found = 'ProfileId_Fail'
    childCollectionName = "Given"
    swipeStatusBetweenUsers = "Likes"
    with patch('Gateways.LikesDislikesGatewayEXT.redis_client') as mock_redis_client:
        mock_redis_client.zrevrange.return_value = ['ProfileId123','ProfileId234']
        redisBaseKey = f"LikesDislikes:{idToBeDeleted}:{childCollectionName}:{swipeStatusBetweenUsers}"
        mock_redis_client.zrem.side_effect = lambda x, y: True
        result = await LikesDislikes_delete_record_from_redis(userId=user_id, idToBeDeleted=idToBeDeleted, childCollectionName=childCollectionName, swipeStatusBetweenUsers=swipeStatusBetweenUsers)
        assert result == True

        result = await LikesDislikes_delete_record_from_redis(userId=user_id, idToBeDeleted=idToBeDeleted_not_found, childCollectionName=childCollectionName, swipeStatusBetweenUsers=swipeStatusBetweenUsers)
        assert result == False

@pytest.mark.asyncio
async def test_LikesDislikes_delete_record_from_redis_failure():
    user_id = "UserId1234"
    idToBeDeleted = 'ProfileId123'
    idToBeDeleted_not_found = 'ProfileId_Fail'
    childCollectionName = "Given"
    swipeStatusBetweenUsers = "Likes"
    with patch('Gateways.LikesDislikesGatewayEXT.redis_client') as mock_redis_client:
        mock_redis_client.zrevrange.side_effect = Exception("Testing exception raised")
        redisBaseKey = f"LikesDislikes:{idToBeDeleted}:{childCollectionName}:{swipeStatusBetweenUsers}"
        mock_redis_client.zrem.side_effect = lambda x, y: True
        result = await LikesDislikes_delete_record_from_redis(userId=user_id, idToBeDeleted=idToBeDeleted, childCollectionName=childCollectionName, swipeStatusBetweenUsers=swipeStatusBetweenUsers)
        assert result == False

@pytest.mark.asyncio
async def test_LikesDislikes_async_store_swipe_task():
    swipeStatusBetweenUsers = 'Superlikes'
    firstUserId = 'user1'
    secondUserId = 'user2'
    childCollectionName = 'MatchUnmatch'
    upgradeLikeToSuperlike = True
    with patch('Gateways.LikesDislikesGatewayEXT.async_db') as mock_async_db: 
        mock_async_db.collection.return_value.document.return_value.collection.return_value.document.return_value.set.return_value = async_mock_child(return_value=True)
        with patch('Gateways.LikesDislikesGatewayEXT.redis_client') as mock_redis_client:
            mock_redis_client.zrem.return_value = True
            mock_redis_client.zadd.return_value = True
            result = await LikesDislikes_async_store_swipe_task(firstUserId=firstUserId, 
                                    secondUserId=secondUserId,
                                    childCollectionName=childCollectionName,
                                    swipeStatusBetweenUsers=swipeStatusBetweenUsers,
                                    upgradeLikeToSuperlike=upgradeLikeToSuperlike)
            assert result == True


@pytest.mark.asyncio
async def test_LikesDislikes_async_store_swipe_task_failure():
    swipeStatusBetweenUsers = 'Superlikes'
    firstUserId = 'user1'
    secondUserId = 'user2'
    childCollectionName = 'MatchUnmatch'
    upgradeLikeToSuperlike = True
    with patch('Gateways.LikesDislikesGatewayEXT.async_db') as mock_async_db: 
        mock_async_db.collection.return_value.document.return_value.collection.return_value.document.return_value.set.side_effect = Exception("Testing error")
        with patch('Gateways.LikesDislikesGatewayEXT.redis_client') as mock_redis_client:
            mock_redis_client.zrem.return_value = True
            mock_redis_client.zadd.return_value = True
            result = await LikesDislikes_async_store_swipe_task(firstUserId=firstUserId, 
                                    secondUserId=secondUserId,
                                    childCollectionName=childCollectionName,
                                    swipeStatusBetweenUsers=swipeStatusBetweenUsers,
                                    upgradeLikeToSuperlike=upgradeLikeToSuperlike)
            assert result == False

@pytest.mark.asyncio
async def test_LikesDislikes_fetch_users_given_swipes_success():
    user_id = 'UserId123'
    with patch("Gateways.LikesDislikesGatewayEXT.LikesDislikes_fetch_userdata_from_firebase_or_redis") as mock_firebase_or_redis:
        mock_firebase_or_redis.return_value = 'ProfileId123'
        result = await LikesDislikes_fetch_users_given_swipes(user_id)
        assert result == ['ProfileId123','ProfileId123','ProfileId123']

@pytest.mark.asyncio
async def test_LikesDislikes_fetch_users_given_swipes_failure():
    user_id = 'UserId123'
    with patch("Gateways.LikesDislikesGatewayEXT.LikesDislikes_fetch_userdata_from_firebase_or_redis") as mock_firebase_or_redis:
        mock_firebase_or_redis.side_effect = Exception("Testing exception")
        result = await LikesDislikes_fetch_users_given_swipes(user_id)
        assert result == False