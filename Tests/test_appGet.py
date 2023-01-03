import pytest
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
async def test_get_profiles_by_ids(client):
    # Set up the test data
    profileIdList = ['user1','user2']
    # Set up the mocks
    with patch('appSet.ProfilesGateway_get_profile_by_ids') as mock_get_profile_by_ids:
        mock_get_profile_by_ids.return_value = await async_mock_child(return_value=[{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}])
        data = {'profileIdList': profileIdList}
        response = client.post('/rewindsingleswipegate', json=data)
        # Check the response
        assert response.status_code == 200
        