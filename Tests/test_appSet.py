import pytest
from unittest.mock import patch
from app import app
from Tests.test_base import async_mock_parent, async_mock_child
from ProjectConf.FirestoreConf import async_db, db
from Gateways.GradingScoresGateway import store_graded_profile_in_firestore_route
from Gateways.LikesDislikesGateway import LikesDislikes_async_store_likes_dislikes_superlikes_for_user
from Gateways.MatchUnmatchGateway import MatchUnmatch_unmatch_two_users
from Gateways.RewindGateway import Rewind_task_function, get_last_given_swipe_from_firestore
from Gateways.ReportProfile import Report_profile_task
from Gateways.GeoserviceGateway import GeoService_store_profiles
from Gateways.MessagesGateway import match_two_profiles_for_direct_message
from Gateways.ProfilesGateway import ProfilesGateway_get_profile_by_ids

@pytest.fixture
def client():
    # Set up the Flask app and test client
    app.config['TESTING'] = True
    client = app.test_client()
    yield client
        
def test_store_likes_dislikes_superlikes(client):
    
    # Test successful request
    with patch.object(LikesDislikes_async_store_likes_dislikes_superlikes_for_user, '__call__', return_value=True):
        response = client.post('/storelikesdislikesGate', json={
            'currentUserId': 'user1',
            'swipeInfo': 'like',
            'swipedUserId': 'user2',
            'upgradeLikeToSuperlike': False
        })
        assert response.status_code, 200
        assert response.get_json(), {'status': 200}
    
def test_unmatch(client):
    # Test successful request
    with patch.object(MatchUnmatch_unmatch_two_users, '__call__', return_value=True):
        response = client.post('/unmatchgate', json={
            'current_user_id': 'user1',
            'other_user_id': 'user2'
        })
        assert response.status_code, 200
        assert response.get_json(), {'status': 200}
    
@pytest.mark.asyncio
async def test_rewind_single_swipe(client):
    # Set up the test data
    current_user_id = 'user1'
    swiped_user_id = 'user2'
    last_swiped_info = 'LIKE'
    rewinded_user_info = {'id': swiped_user_id, 'name': 'User 2'}
    rewinded_dict = {'rewindedUserCard': rewinded_user_info, 'swipeStatusBetweenUsers': last_swiped_info}

    # Set up the mocks
    with patch('appSet.get_last_given_swipe_from_firestore') as mock_get_last_given_swipe:
        mock_get_last_given_swipe.return_value = (swiped_user_id, last_swiped_info)

        with patch('appSet.Rewind_task_function') as mock_rewind_task:
            mock_rewind_task.return_value = await async_mock_child(return_value=True)
            
            with patch('appSet.ProfilesGateway_get_profile_by_ids') as mock_get_profile:
                mock_get_profile.return_value =  await async_mock_child(return_value=[rewinded_user_info])
                
                # Send the request
                data = {'currentUserID': current_user_id}
                response = client.post('/rewindsingleswipegate', json=data)
                # Check the response
                assert response.status_code == 200
                assert response.json == rewinded_dict

@pytest.mark.asyncio
async def test_store_profile_success(client):
    # Set up the test data
    profile = {'id':'UserId1','FirstName':'Test'}
        # Set up the mocks
    with patch('appSet.GeoService_store_profiles') as mock_geo_store_profile:
        mock_geo_store_profile.return_value = await async_mock_child(return_value=True)

        # Send the request
        data = {'profile': profile}
        response = client.post('/storeProfileInBackendGate', json=data)
        # Check the response
        assert response.status_code == 200
        assert response.json == {'message': f"{profile['id']}: Successfully stored profile in Cache/DB"}

@pytest.mark.asyncio
async def test_store_profile_failure(client):
    # Set up the test data
    profile = {'id':'UserId1','FirstName':'Test'}
    # Set up the mocks
    with patch('appSet.GeoService_store_profiles') as mock_geo_store_profile:
        mock_geo_store_profile.side_effect = Exception('Error storing profile')
        # Send the request
        data = {'profile': profile}
        response = client.post('/storeProfileInBackendGate', json=data)
        # Check the response
        assert response.status_code == 400

@pytest.mark.asyncio
async def test_report_profile_success(client):
   
    # Set up the mocks
    with patch('appSet.Report_profile_task') as report_profile_task:
        report_profile_task.return_value = True
        with patch('appSet.MatchUnmatch_unmatch_two_users') as unmatch_two_users:
            unmatch_two_users.return_value = await async_mock_child(return_value=True)
        data = {
            'current_user_id' : 'UserId1',
            'other_user_id' : 'UserId2',
            'reasonGiven': 'Test Report',
            'descriptionGiven': 'Test Report',
        }
        response = client.post('/reportprofilegate', json=data)
        # Check the response
        assert response.status_code == 200
        

@pytest.mark.asyncio
async def test_report_profile_failure(client):
    # Set up the test data
    current_user_id = 'UserId1'
    reported_profile_id = 'UserId2'
    reason_given = 'Test Report'
    description_given = 'Test Report'
    
    # Set up the mocks
    with patch('appSet.Report_profile_task') as report_profile_task:
        with patch('appSet.MatchUnmatch_unmatch_two_users') as unmatch_two_users:
            unmatch_two_users.side_effect = Exception("Can't unmatch users")
            data = {
                'current_user_id' : 'UserId1',
                'reported_profile_id' : 'UserId2',
                'reason_given': 'Test Report',
                'description_given': 'Test Report',
            }
            response = client.post('/reportprofilegate', json=data)
            # Check the response
            assert response.status_code == 500

@pytest.mark.asyncio
async def test_match_profiles_on_direct_message_success(client):
    # Set up the test data
    current_user_id = 'UserId1'
    other_user_id = 'UserId2'
    
    # Set up the mocks
    with patch('appSet.match_two_profiles_for_direct_message') as match_two_profiles_for_direct_message:
        match_two_profiles_for_direct_message.return_value = True
        data = {
            'current_user_id' : 'UserId1',
            'other_user_id' : 'UserId2'
            }
        response = client.post('/matchondirectmessageGate', json=data)
        # Check the response
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_match_profiles_on_direct_message_failure(client):
    # Set up the test data
    current_user_id = 'UserId1'
    other_user_id = 'UserId2'
    
    # Set up the mocks
    with patch('appSet.match_two_profiles_for_direct_message') as match_two_profiles_for_direct_message:
        match_two_profiles_for_direct_message.side_effect = Exception("Can't match profiles on direct message")
        data = {
            'current_user_id' : 'UserId1',
            'other_user_id' : 'UserId2'
            }
        response = client.post('/matchondirectmessageGate', json=data)
        # Check the response
        assert response.status_code == 500
        
