import pytest
import json
from unittest.mock import patch
from app import app
from Tests.Utilities.test_base import client, async_mock_parent, async_mock_child

@pytest.mark.sync
def test_route_success(client):
    response = client.get('/test')
    data = json.loads(response.get_data())
    assert response.status_code,200
    assert data['status'], True
    assert data['service'], 'Amore Caching Service'

@pytest.mark.sync
def test_route_failure(client):
    with patch("app.json.dumps") as mock_json_dumps:
        mock_json_dumps.side_effect = Exception("Raise an exception")
        response = client.get('/test')
        assert response.status_code,500

        
