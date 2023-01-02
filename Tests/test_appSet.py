import pytest
from unittest.mock import patch
from app import app
from Tests.test_base import async_mock_parent, async_mock_child
from ProjectConf.AsyncioPlugin import run_coroutine
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

    print("Hellooooooo")

    # Set up the mocks
    with patch('appSet.get_last_given_swipe_from_firestore') as mock_get_last_given_swipe:
        mock_get_last_given_swipe.return_value = (swiped_user_id, last_swiped_info)

        with patch('appSet.Rewind_task_function') as mock_rewind_task:
            mock_rewind_task.return_value = await async_mock_parent(return_value=True)
            
            with patch('appSet.ProfilesGateway_get_profile_by_ids') as mock_get_profile:
                mock_get_profile.return_value =  await async_mock_child(return_value=[rewinded_user_info])
                
                # Send the request
                data = {'currentUserID': current_user_id}
                response = client.post('/rewindsingleswipegate', json=data)
                print(response)
                # Check the response
                assert response.status_code == 200
                assert response.json == rewinded_dict

    