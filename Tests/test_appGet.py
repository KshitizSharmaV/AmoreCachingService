import pytest
import json
from unittest.mock import patch
from app import app
from Tests.Utilities.test_base import async_mock_parent, async_mock_child
from Tests.Utilities.test_base import client


@pytest.mark.asyncio
async def test_get_profiles_by_ids_success(client):
    # Set up the test data
    profileIdList = ['user1','user2']
    # Set up the mocks
    with patch('appGet.ProfilesGateway_get_profile_by_ids') as mock_get_profile_by_ids:
        mock_get_profile_by_ids.return_value = await async_mock_child(return_value=[{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}])
        data = {'profileIdList': profileIdList}
        response = client.get('/getprofilesbyids', json=data)
        # Check the response
        assert response.status_code == 200
        
        
@pytest.mark.asyncio
async def test_get_profiles_by_ids_failure(client):
    # Set up the test data
    profileIdList = ['user1','user2']
    # Set up the mocks
    with patch('appGet.ProfilesGateway_get_profile_by_ids') as mock_get_profile_by_ids:
        mock_get_profile_by_ids.side_effect = Exception("Can't get profiles for the ID")
        data = {'profileIdList': profileIdList}
        response = client.get('/getprofilesbyids', json=data)
        # Check the response
        assert response.status_code == 401
        
@pytest.mark.asyncio
async def test_fetch_geo_recommendations_success(client):
    # Set up the test data
    userId='123'
    # Set up the mocks
    with patch('appGet.RecommendationSystem') as mock_recommendation_system, patch('appGet.check_redis_index_exists') as mock_check_redis_index_exists:
        mock_recommendation_system.return_value.build_recommendations.return_value = [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}]

        mock_check_redis_index_exists.return_value = True
        data = {'userId': '6546','profilesAlreadyInDeck':['userId1','userId2'],'filterdata':{'age':7,'sex':'male'}}
        response = client.post('/fetchGeoRecommendationsGate', json=data)                                                                            
         # Check the response
        assert response.status_code == 200
            
        
@pytest.mark.asyncio
async def test_fetch_geo_recommendations_failure(client):
    # Set up the test data
    profileIdList = ['user1','user2']
    # Set up the mocks
    with patch('appGet.ProfilesGateway_get_profile_by_ids') as mock_get_profile_by_ids:
        mock_get_profile_by_ids.side_effect = Exception("Can't get profiles for the ID")
        data = {'profileIdList': profileIdList}
        response = client.post('/fetchGeoRecommendationsGate', json=data)
        # Check the response
        assert response.status_code == 400   
   
     
@pytest.mark.asyncio
async def test_get_likes_dislikes_for_user_route_success(client):
    #Set up the test day
    #Set up the mocks
    with patch('appGet.LikesDislikes_fetch_userdata_from_firebase_or_redis') as mock_func:
        mock_func.return_value=await async_mock_child(return_value=['user1','user2'])
        data={'currentUserId':'user1','childCollectionName':1231,'matchFor':'dsag','noOfLastRecords':21}
        response=client.get('/getlikesdislikesforuser',json=data)
        
        #check response
        assert response.status_code ==200


@pytest.mark.asyncio
async def test_get_likes_dislikes_for_user_route_failure(client):
    #Set up the test day
    #Set up the mocks
    with patch('appGet.LikesDislikes_fetch_userdata_from_firebase_or_redis') as mock_func:
        mock_func.side_effect=Exception("Can't get likes/dislikes of the user.")
        data={'currentUserId':'user1','childCollectionName':1231,'matchFor':'dsag','noOfLastRecords':21}
        response=client.get('/getlikesdislikesforuser',json=data)
        
        #check response
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_profiles_already_seen_by_user_route_success(client):
    # Set up the test data
    # Set up the mocks
    with patch('appGet.LikesDislikes_get_profiles_already_seen_by_id') as mock_func:
        mock_func.return_value = await async_mock_child(return_value=['user2'])
        data = {'currentUserId': 'userId'}
        response = client.get('/getprofilesalreadyseen', json=data)
        # Check the response
        assert response.status_code == 200
             
        
@pytest.mark.asyncio
async def test_get_profiles_already_seen_by_user_route_failure(client):
    # Set up the test data
    # Set up the mocks
    with patch('appGet.LikesDislikes_get_profiles_already_seen_by_id') as mock_func:
        mock_func.side_effect = Exception("Can't get profiles already seen by the user.")
        data = {'profileIdList': 'userId1'}
        response = client.get('/getprofilesalreadyseen', json=data)
        # Check the response
        assert response.status_code == 401
        

@pytest.mark.asyncio
async def test_load_match_unmatch_profiles_success(client):
    # Set up the test data
    # Set up the mocks
    with patch('appGet.MatchUnmatch_fetch_userdata_from_firebase_or_redis') as mock_func_parent:
        mock_func_parent.return_value=await async_mock_child(return_value=['user1','user2'])
        with patch('appGet.ProfilesGateway_get_profile_by_ids') as mock_func:
            mock_func.return_value = await async_mock_child(return_value=[{"id": 'user1', "name": "John"}, {"id": 'user2', "name": "Jane"}] )
            data = {'currentUserId': 'user2', 'fromCollection': 'Match'}
            response = client.post('/loadmatchesunmatchesgate', json=data)
            # Check the response
            assert response.status_code == 200
                
        
@pytest.mark.asyncio
async def test_load_match_unmatch_profiles_failure(client):
    # Set up the test data
    # Set up the mocks
    with patch('appGet.MatchUnmatch_fetch_userdata_from_firebase_or_redis') as mock_func_parent:
        mock_func_parent.return_value=await async_mock_child(return_value=['user1','user2'])
        with patch('appGet.ProfilesGateway_get_profile_by_ids') as mock_func:
            mock_func.side_effect = Exception("Can't get profiles already seen by the user.")            
            data = {'currentUserId': 'user2', 'fromCollection': 'Match'}
            response = client.post('/loadmatchesunmatchesgate', json=data)
            # Check the response
            assert response.status_code == 401


