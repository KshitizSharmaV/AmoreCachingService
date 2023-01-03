import pytest
import json
from app import app


@pytest.fixture
def client():
    # Set up the Flask app and test client
    app.config['TESTING'] = True
    client = app.test_client()
    yield client
        

def test_test_route(client):
    response = client.get('/test')
    data = json.loads(response.get_data())
    assert response.status_code,200
    assert data['status'], True
    assert data['service'], 'Amore Caching Service'

