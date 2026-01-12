"""Testing for HB Client"""
from datetime import datetime, timezone
import pytest
from homebridge_api import HomebridgeClient

@pytest.fixture
def hb_client():
    """Initializes the HB Client"""
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
    """Tests the login for HB Client"""
    mock_post = mocker.patch('requests.post')

    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"access_token": "fake_token"}

    token = hb_client.login()

    assert token == "fake_token"
    assert hb_client.token == "fake_token"
    mock_post.assert_called_once()

def test_get_alarm_time(hb_client, mock_config, mocker):
    """Tests the get_alarm function from HB Client"""
    mocker.patch.object(hb_client, 'get_full_config', return_value=mock_config)

    now = datetime.now()
    gmt_dt = datetime(now.year, now.month, now.day, 12, 30, tzinfo=timezone.utc)
    expected_local = gmt_dt.astimezone().strftime("%H:%M")

    actual_time = hb_client.get_alarm_time()

    assert actual_time == expected_local

    # Test when get_full_config runs into an error
    mocker.patch.object(hb_client, 'get_full_config', return_value=None)
    gmt_error = datetime(now.year, now.month, now.day, 12, 0, tzinfo=timezone.utc)
    expected_error = gmt_error.strftime("%H:%M")

    actual_time = hb_client.get_alarm_time()
    assert actual_time == expected_error

def test_update_time(hb_client, mock_config, mocker):
    """Tests the update_alarm time from HB Client"""
    mocker.patch.object(hb_client, 'get_full_config', return_value=mock_config)
    mock_post = mocker.patch('requests.post')
    mock_post.return_value.status_code = 200

    hb_client.update_morning_alarm("08:00")

    args, kwargs = mock_post.call_args
    updated_config = kwargs['json']

    new_cron = updated_config[0]['accessories'][0]['schedule']['cronCustom']

    assert "*" in new_cron
    assert len(new_cron.split()) == 5
