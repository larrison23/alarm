import pytest
import os
import json
from app import app

@pytest.fixture
def client(mocker):
    mocker.patch('app.STATE_FILE', 'state_test.json')

    with app.test_client() as test_client:
        yield test_client

    if os.path.exists('state_test.json'):
        os.remove('state_test.json')

def test_persistence(client):
    test_time = "06:45"
    client.post("/set-alarm-time", json={"time": test_time})

    assert os.path.exists('state_test.json')

    with open('state_test.json', "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data["last_time"] == test_time
    
    response = client.get("/")
    assert b"06:45" in response.data