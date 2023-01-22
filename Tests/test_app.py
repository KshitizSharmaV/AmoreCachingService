import pytest
import json
from app import app
from Tests.Utilities.test_base import client

def test_test_route(client):
    response = client.get('/test')
    data = json.loads(response.get_data())
    assert response.status_code,200
    assert data['status'], True
    assert data['service'], 'Amore Caching Service'

