import pytest
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
        with patch('Gateways.NotificationGateway.redis_client') as mock_redis_client:
            key = f"FCMTokens:{fcm_data['userId']}:{fcm_data['deviceId']}"
            mock_check_redis_index_exists.set.side_effect = redis_test_set(key, fcm_data)
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
async def test_Notification_send_muticastmessage_to_userId_sucess():
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
    user_id = 'UserId123'
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
    
    
    """
    Since we are passing fictional fcm_token id the reponse will be a
    failure. The success_count = 0 and failure_count  = 1. So here we are
    just going to check if the failure_count = 1
    """
    assert response.failure_count == 1
        

@pytest.mark.asyncio
async def test_Notification_send_muticastmessage_to_userId_failure():
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
    user_id = 'UserId123'
    fcm_tokens = ['TestFCMToken123']
    notification = messaging.Notification(title=pay_load['title'], body=pay_load['body'])
    # Firestore analytical label and notification image
    notification_image = pay_load['notification_image'] if pay_load['notification_image'] else amoreicon_image
    fcm_options = messaging.APNSFCMOptions(analytics_label=pay_load['analytics_label'], image=notification_image)
    # Badge Count and Notification Category
    aps = messaging.Aps(badge=pay_load['badge_count'], category=pay_load['aps_category'])
    payload = messaging.APNSPayload(aps=aps)
    apns = messaging.APNSConfig(fcm_options=fcm_options, payload=payload)

    with patch('Gateways.NotificationGateway.messaging') as messaging_mock:
        messaging_mock.send_multicast.side_effect = Exception("Raise a test exception, can't send notification")
        response = Notification_send_muticastmessage_to_userId(user_id=user_id, 
                                                apns=apns,
                                                notification=notification,
                                                data=pay_load['data'],
                                                fcm_tokens=fcm_tokens, 
                                                dry_run=True)
        assert response == False
        


def test_Notification_failed_tokens_success():
    pay_load = {
        'title':'Test Notificaiton',
        'body':'Test Body',
        'analytics_label': "Message_test_notificatoin",
        'badge_count':1,
        'notification_image':None,
        'aps_category':'Message',
        'data':{'data':'none'}
    }
    user_id = 'UserId123'
    
    # Creating mock multicast response which is sent to Notification_failed_tokens for testing
    response = MagicMock()
    response.success_count = 3
    response.failure_count = 7
    status_code_list = [200, 404, 200, 403, 200, 429, 503, 500, 401, 420]
    multicast_responses = []
    for status_code in status_code_list:
        temp_response = MagicMock()
        if status_code == 200:
            temp_response.success = True
        else:
            temp_response.success = False
            temp_response.getheader.return_value =  1
            temp_response.exception.cause.status_code = status_code
            temp_response.exception.cause.side_effect = lambda x: f"Test Exception Code {status_code}"
        multicast_responses.append(temp_response)
    response.responses = multicast_responses
    
    fcm_tokens = ['token1', 'token2', 'token3', 'token4', 'token5','token6','token7','token8','token9','token10']
    
    with patch("Gateways.NotificationGateway.Notification_delete_fcm_token") as mock_delete_fcm_token:
        mock_delete_fcm_token.return_value = True
        with patch("Gateways.NotificationGateway.Notification_QUOTA_EXCEEDED") as mock_quota_Exceeded:
            mock_quota_Exceeded.return_value = None
            with patch("Gateways.NotificationGateway.Notification_UNAVAILABLE") as mock_unavailable:
                mock_quota_Exceeded.return_value = None
                with patch("Gateways.NotificationGateway.Notification_INTENRAL") as mock_internal:
                    mock_internal.return_value = None
                    failed_tokens = Notification_failed_tokens(user_id=user_id, pay_load=pay_load, response=response, fcm_tokens=fcm_tokens)

                    assert failed_tokens == ['token2','token4','token6','token7','token8','token9','token10']

def test_Notification_failed_tokens_failure():
    pay_load = {
        'title':'Test Notificaiton',
        'body':'Test Body',
        'analytics_label': "Message_test_notificatoin",
        'badge_count':1,
        'notification_image':None,
        'aps_category':'Message',
        'data':{'data':'none'}
    }
    user_id = 'UserId123'
    # Creating mock multicast response which is sent to Notification_failed_tokens for testing
    response = MagicMock()
    response.success_count = 3
    response.failure_count.side_effect = Exception("Test Failure")
    response = Notification_failed_tokens(user_id=user_id, pay_load=pay_load, response=response, fcm_tokens=['token1'])
    assert response == False

@pytest.mark.asyncio
async def test_Notification_design_and_multicast():
    pay_load = {
        'title':'Test Notificaiton',
        'body':'Test Body',
        'analytics_label': "Message_test_notificatoin",
        'badge_count':1,
        'notification_image':None,
        'aps_category':'Message',
        'data':{'data':'none'}
    }
    user_id = 'UserId123'
    dry_run = True
    
    with patch('Gateways.NotificationGateway.Notification_fetch_fcm_token_docs_for_userId') as mock_fetch_fcm_token_docs_for_userId:
        mock_fetch_fcm_token_docs_for_userId.return_value = {'fcm_token_docs':'fcm_token_docs'}
        with patch('Gateways.NotificationGateway.Notification_get_fcm_tokens_from_redis_docs') as mock_get_fcm_tokens_from_redis_docs:
            mock_get_fcm_tokens_from_redis_docs.return_value = ['token1']
            with patch('Gateways.NotificationGateway.Notification_send_muticastmessage_to_userId') as mock_multicast:
                mock_multicast.return_value = {'response':'Test Response'}
                with patch('Gateways.NotificationGateway.Notification_failed_tokens') as mock_failed_tokens:
                    mock_failed_tokens.return_value = ['token2']
                    result = await Notification_design_and_multicast(user_id=user_id, pay_load=pay_load, dry_run=dry_run)
                    assert result == {'response':'Test Response'}


def test_Notification_delete_fcm_token_status_success():
    user_id = "UserId123"
    fcm_token = ['token1','token2','token3']
    
    token_doc = MagicMock()
    fcm_token_child_mock = {
        "fcmToken":"token1",
        "timestamp":123,
        "deviceType":"iOS",
        "deviceId":"TestId1",
        "userId":"UserId123"
    }
    token_doc.json = json.dumps(fcm_token_child_mock)
    
    fcm_token_docs = [token_doc]
    with patch('Gateways.NotificationGateway.redis_client') as mock_redis_client:
        mock_redis_client.ft.return_value.search.return_value = fcm_token_docs
        with patch('Gateways.NotificationGateway.redis_client.json') as mock_redis_client_json:
            mock_redis_client_json.forget.side_effect = lambda x: True 
            with patch('Gateways.NotificationGateway.db') as mock_db:
                mock_db.collection.return_value.document.return_value.collection.return_value.where.return_value.get.side_effect = ['DocRef1']
                mock_db.delete.side_effect = lambda x: True
                result = Notification_delete_fcm_token(user_id=user_id,fcm_token=fcm_token)
                assert result == True

def test_Notification_delete_fcm_token_status_failure():
    user_id = "UserId123"
    fcm_token = ['token1','token2','token3']
    
    token_doc = MagicMock()
    fcm_token_child_mock = {
        "fcmToken":"token1",
        "timestamp":123,
        "deviceType":"iOS",
        "deviceId":"TestId1",
        "userId":"UserId123"
    }
    token_doc.json = json.dumps(fcm_token_child_mock)
    
    fcm_token_docs = [token_doc]
    with patch('Gateways.NotificationGateway.redis_client') as mock_redis_client:
        mock_redis_client.ft.return_value.search.return_value = fcm_token_docs
        with patch('Gateways.NotificationGateway.redis_client.json') as mock_redis_client_json:
            mock_redis_client_json.forget.side_effect = lambda x: True 
            with patch('Gateways.NotificationGateway.db') as mock_db:
                mock_db.collection.return_value.document.return_value.collection.return_value.where.return_value.get.side_effect = ['DocRef1']
                mock_db.delete.side_effect = Exception("Test exception raised")
                result = Notification_delete_fcm_token(user_id=user_id,fcm_token=fcm_token)
                assert result == False

def test_Notification_exponential_back_off():
    user_id = 'UserId123'
    fcm_token = ['token1']
    result = Notification_exponential_back_off(user_id=user_id,fcm_token=fcm_token)
    assert result == None

def test_Notification_UNAVAILABLE():
    user_id = 'UserId123'
    fcm_token = ['token1']
    result = Notification_exponential_back_off(user_id=user_id,fcm_token=fcm_token)
    assert result == None



def test_Notification_INTENRAL():
    user_id = 'UserId123'
    fcm_token = ['token1']
    result = Notification_INTENRAL(user_id=user_id,fcm_token=fcm_token)
    assert result == None

    

