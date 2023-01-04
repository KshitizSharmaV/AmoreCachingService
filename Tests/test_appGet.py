import pytest
import json
from unittest.mock import patch
from app import app
from Tests.test_base import async_mock_parent, async_mock_child

@pytest.fixture
def client():
    # Set up the Flask app and test client
    app.config['TESTING'] = True
    client = app.test_client()
    yield client


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
