import pytest
import json
import json
from unittest.mock import patch, MagicMock
from app import app
from Tests.Utilities.test_base import redis_test_set
from Gateways.NotificationGateway import *


@pytest.mark.asyncio
async def test_Notification_store_fcm_token_in_redis_success():
    fcm_data = {
        'userId' : "UserId123",
        'deviceId':'TestDeviceId'
    }
    with patch('Gateways.NotificationGateway.check_redis_index_exists') as mock_check_redis_index_exists:
        mock_check_redis_index_exists.return_value = True
        with patch('Gateways.NotificationGateway.redis_client.set') as mock_redis_client_set:
            key = f"FCMTokens:{fcm_data['userId']}:{fcm_data['deviceId']}"
            mock_redis_client_set.side_effect = redis_test_set(key, fcm_data)
            result = await Notification_store_fcm_token_in_redis(fcm_data=fcm_data)
            assert result == True



@pytest.mark.asyncio
async def test_Notification_store_fcm_token_in_redis_failure():
    fcm_data = {
        'userId' : "UserId123",
        'deviceId':'TestDeviceId'
    }
    with patch('Gateways.NotificationGateway.check_redis_index_exists') as mock_check_redis_index_exists:
        mock_check_redis_index_exists.side_effect = Exception("Raise a test exception")
        result = await Notification_store_fcm_token_in_redis(fcm_data=fcm_data)
        assert result == False


def test_Notification_fetch_fcm_token_docs_for_userId_success():
    user_id = 'UserId123'
    fcm_token_docs_mm = MagicMock()
    fcm_token_docs_mm.total = 1
    with patch('Gateways.NotificationGateway.check_redis_index_exists') as mock_check_redis_index_exists:
        mock_check_redis_index_exists.return_value = True
        with patch('Gateways.NotificationGateway.redis_client') as mock_redis_client:
            mock_redis_client.ft.return_value.search.return_value = fcm_token_docs_mm
            result = Notification_fetch_fcm_token_docs_for_userId(user_id=user_id)
            assert result.total == fcm_token_docs_mm.total


def test_Notification_fetch_fcm_token_docs_for_userId_success_none():
    """
    Test is designed to test if the function being tested returns None with No user id is passed
    """
    user_id = None 
    fcm_token_docs_mm = MagicMock()
    fcm_token_docs_mm.total = 1
    with patch('Gateways.NotificationGateway.check_redis_index_exists') as mock_check_redis_index_exists:
        mock_check_redis_index_exists.return_value = True
        with patch('Gateways.NotificationGateway.redis_client') as mock_redis_client:
            mock_redis_client.ft.return_value.search.return_value = fcm_token_docs_mm
            result = Notification_fetch_fcm_token_docs_for_userId(user_id=user_id)
            assert result == None


def test_Notification_fetch_fcm_token_docs_for_userId_failure():
    user_id = 'UserId123'
    fcm_token_docs = None
    with patch('Gateways.NotificationGateway.check_redis_index_exists') as mock_check_redis_index_exists:
        mock_check_redis_index_exists.return_value = True
        with patch('Gateways.NotificationGateway.redis_client') as redis_client:
            redis_client.ft.return_value.search.return_value = None
            result = Notification_fetch_fcm_token_docs_for_userId(user_id=user_id)
            assert result == False

def test_Notification_fetch_fcm_token_for_userId_deviceId_success():
    user_id = 'UserId123'
    device_id = 'TestDeviceId123'
    fcm_token_docs = {
        "fcmToken":"TestToken",
        "timestamp":1671287312.115757,
        "deviceType":"iOS",
        "deviceId":device_id,
        "userId":user_id
    }
    with patch('Gateways.NotificationGateway.redis_client') as mock_redis_client:
        mock_redis_client.json().get.return_value = fcm_token_docs
        result = Notification_fetch_fcm_token_for_userId_deviceId(user_id=user_id, device_id=device_id)
        assert result['userId'] == user_id
        assert result['deviceId'] == device_id

        # Userid is None
        result = Notification_fetch_fcm_token_for_userId_deviceId(user_id=None, device_id=device_id)
        assert result == None

def test_Notification_fetch_fcm_token_for_userId_deviceId_failure():
    user_id = 'UserId123'
    device_id = 'TestDeviceId123'
    fcm_token_docs = {
        "fcmToken":"TestToken",
        "timestamp":1671287312.115757,
        "deviceType":"iOS",
        "deviceId":device_id,
        "userId":user_id
    }
    with patch('Gateways.NotificationGateway.redis_client') as mock_redis_client:
        mock_redis_client.json().get.side_effect = Exception("Test exception raised")
        result = Notification_fetch_fcm_token_for_userId_deviceId(user_id=user_id, device_id=device_id)
        assert result==False


def test_Notification_get_fcm_tokens_from_redis_docs_sucess():
    fcm_token_docs = MagicMock()
    device = MagicMock()
    device.json = json.dumps({'fcmToken':'testFCMToken'})
    fcm_token_docs.docs = [device]
    result = Notification_get_fcm_tokens_from_redis_docs(fcm_token_docs=fcm_token_docs)
    assert result == ['testFCMToken']
    

def test_Notification_get_fcm_tokens_from_redis_docs_failure():
    fcm_token_docs = MagicMock()
    device = MagicMock()
    device.json = json.dumps({'fcmToken':'testFCMToken'})
    fcm_token_docs.docs = Exception("Raise test exception")
    result = Notification_get_fcm_tokens_from_redis_docs(fcm_token_docs=fcm_token_docs)
    assert result == False

@pytest.mark.asyncio
async def Notification_send_muticastmessage_to_userId_sucess():
    """
    Make use of the dry_run function to not actually send the notification
    """
    # Title and body of notification
    pay_load = {
        'title':'Test Notificaiton',
        'body':'Test Bodu',
        'analytics_label': "Message_test_notificatoin",
        'badge_count':1,
        'notification_image':None,
        'aps_category':'Message',
        'data':{'data':'none'}
    }
    user_id = 'TestId123'
    fcm_tokens = ['TestFCMToken123']
    notification = messaging.Notification(title=pay_load['title'], body=pay_load['body'])
    # Firestore analytical label and notification image
    notification_image = pay_load['notification_image'] if pay_load['notification_image'] else amoreicon_image
    fcm_options = messaging.APNSFCMOptions(analytics_label=pay_load['analytics_label'], image=notification_image)
    # Badge Count and Notification Category
    aps = messaging.Aps(badge=pay_load['badge_count'], category=pay_load['aps_category'])
    payload = messaging.APNSPayload(aps=aps)
    apns = messaging.APNSConfig(fcm_options=fcm_options, payload=payload)

    response = Notification_send_muticastmessage_to_userId(user_id=user_id, 
                                            apns=apns,
                                            notification=notification,
                                            data=pay_load['data'],
                                            fcm_tokens=fcm_tokens, 
                                            dry_run=True)
        

    