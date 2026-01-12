import pytest
from homebridge_api import HomebridgeClient
from datetime import datetime, timezone

@pytest.fixture
def hb_client():
    client = HomebridgeClient("http://10.0.0.227:8581", "admin", "password123")
    client.token = "fake_token"
    client.headers = {"Authorization": "Bearer fake_token"}
    return client

@pytest.fixture
def mock_config():
    """Returns the JSON structure provided by Homebridge."""
    return [
        {
            "name": "Homebridge Dummy",
            "accessories": [
                {
                    "id": "morning_switch",
                    "schedule": {
                        "cronCustom": "30 12 * * *" # 12:30 PM GMT
                    }
                }
            ]
        }
    ]

def test_login_success(hb_client, mocker):
    mock_post = mocker.patch('requests.post')

    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"access_token": "fake_token"}

    token = hb_client.login()

    assert token == "fake_token"
    assert hb_client.token == "fake_token"
    mock_post.assert_called_once()

def test_get_alarm_time(hb_client, mock_config, mocker):
    mocker.patch.object(hb_client, 'get_full_config', return_value=mock_config)

    now = datetime.now()
    gmt_dt = datetime(now.year, now.month, now.day, 12, 30, tzinfo=timezone.utc)
    expected_local = gmt_dt.astimezone().strftime("%H:%M")

    actual_time = hb_client.get_alarm_time()

    assert actual_time == expected_local

