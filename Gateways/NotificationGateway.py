from __future__ import annotations
import json
import time
from firebase_admin import messaging
from redis.commands.json.path import Path
from redis.commands.search.query import Query
from ProjectConf.RedisConf import redis_client, try_creating_fcm_index_for_redis, check_redis_index_exists
from ProjectConf.FirestoreConf import db
from tenacity import Retrying, RetryError, stop_after_attempt, wait_exponential

from Utilities.LogSetup import configure_logger

logger = configure_logger(__name__)

amoreicon_image = "https://drive.google.com/file/d/1GPbFM842dpeu8XZXhN5oSm8dKPsUg-k2/view?usp=sharing"

async def Notification_store_fcm_token_in_redis(fcm_data=None):
    """
    Store Notifications in Redis Cache.
        - Write/Update current Notification data in Redis
    :param profile: Notification Dict/JSON
    
    :return: Status of store action as Boolean
    """
    try:
      # Check if the index already exists for redis
      if not check_redis_index_exists(index="idx:FCMTokens"):
        try_creating_fcm_index_for_redis()

      key = f"FCMTokens:{fcm_data['userId']}:{fcm_data['deviceId']}"
      redis_client.json().set(key, Path.root_path(), fcm_data)
      logger.info(f"Notification stored/updated in cache with key: {key}")
      return True
    except Exception as e:
      logger.exception(f"FCMTokens:{fcm_data['userId']}:{fcm_data['deviceId']} unable to store fcm token")
      logger.exception(f"{fcm_data}")
      logger.exception(e)
      return False

def Notification_fetch_fcm_token_docs_for_userId(user_id=None):
    """
      Returns the fcm tokens for a user id from the redis
        - Creates a redis query
        - Queries on the FCMTokens for a userId
        - Get the list of fcm token for the userId
        
      param user_id: string
    """
    try:
      # Check if the index already exists for redis
      if not check_redis_index_exists(index="idx:FCMTokens"):
        try_creating_fcm_index_for_redis()
      
      query_list = [] 
      if user_id is not None:
        query_list.append(f"@userId:{user_id}")
        query = " ".join(query_list)
        fcm_token_docs = redis_client.ft("idx:FCMTokens").search(Query(query_string=query))
        logger.info(f"Fetched {fcm_token_docs.total} FCMTokens for {user_id}")
        return fcm_token_docs
      else:
        logger.error("userId can't be None")
        return None
    except Exception as e:
        logger.exception(f"Unable to fetch FCMTokens for the {user_id}")
        logger.exception(e)
        return False


def Notification_fetch_fcm_token_for_userId_deviceId(user_id=None, device_id=None):
  """Returns the fcm tokens for a user id and device id from the redis
        - Fetch a single FCMToken record using the userId and deviceId
    
    param user_id: string
    param deviceId: string
    
    Raises:
      FCMToken missing error
  """
  try:
    if (user_id is not None) and (device_id is not None):
      key = f"FCMTokens:{user_id}:{device_id}"
      record = redis_client.json().get(key)
      return record
    logger.error("FCMToken:{device_id} user_id:{user_id} or deviceId can't be None")
    return None
  except Exception as e:
        logger.exception(f"Unable to fetch FCMTokens for the {user_id}")
        logger.exception(e)
        return False

def Notification_get_fcm_tokens_from_redis_docs(fcm_token_docs=None):
  """Accepts FCMToken redis documents object and returns a fcm token list
  
  param fcm_token_docs: Redis documents

  Returns: 
    List of fcm tokens
  """
  try:
    fcm_tokens = []
    for device in fcm_token_docs.docs:
        device_json = json.loads(device.json)
        fcm_tokens.append(device_json['fcmToken'])
    return fcm_tokens
  except Exception as e:
    logger.exception(f'Unable to return fcm token list for {fcm_token_docs}')
    logger.exception(e)
    return False


def Notification_send_muticastmessage_to_userId(user_id=None, apns=None, notification=None, data=None, fcm_tokens=None, dry_run=None):
  """
    Call this function to send a notification to all devices of a user id

    param user_id: String
    param apns: firebase_admin.messaging.APNSConfig
    param notification: firebase_admin.messaging.Notification object
    param data: payLoad needed to be delivered to device other than the notification
    pram dry_run: Bool
  """
  try:
    logger.info(f'Notification will be sent to {len(fcm_tokens)} devices for {user_id}')

    # TODO Add time_to_live=28 default to the message payload
    # TODO Add collapsible or non-collapsible message type
    # Check the JSON representation of the MultiCastMessage here
    # https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages
    message = messaging.MulticastMessage(notification=notification,data=data,tokens=fcm_tokens,apns=apns)
    response = messaging.send_multicast(message, dry_run)
    return response
  except Exception as e:
      logger.exception(f'Unable to send Notification to the {user_id}')
      logger.exception(e)
      return False


def Notification_failed_tokens(user_id=None, pay_load=None, response=None, fcm_tokens=None):
    '''
    Returns the number of failed token in the FCM respones if any

    param response: Multicast response from Firebase Cloud Messaging 
    param fcm_tokens: List of registrations tokens to which messages were broadcasted
    '''
    try:
      logger.info('Notification sent successfully to {0} devices'.format(response.success_count))
      failed_tokens = []
      if response.failure_count > 0:
        responses = response.responses
        for idx, resp in enumerate(responses):
            if not resp.success:
                # The order of responses corresponds to the order of the registration tokens.
                # Error Codes List: https://firebase.google.com/docs/reference/fcm/rest/v1/ErrorCode
                retry_after_delay = resp.getheader("Retry-After")
                
                if resp.exception.cause.status_code == 404:
                  # UNREGISTERED
                  logger.warning(f"UNREGISTERED Deleting expired FCM Token for user {user_id}")
                  # Delete the FCMToken for the user
                  resp = Notification_delete_fcm_token(user_id=user_id, fcm_token=fcm_tokens[idx]) 
                
                elif resp.exception.cause.status_code == 403:
                  # SENDER_ID_MISMATCH
                  logger.error(f"SENDER_ID_MISMATC incorrect {user_id}. Check the SENDER ID in the Cloud Messaging of firestore prohect settings")
                  logger.error(f"Payload:{pay_load}")
                  logger.error(resp.exception.cause)
                  # TODO Send alert email out

                elif resp.exception.cause.status_code == 429:
                  # QUOTA_EXCEEDED
                  logger.error(f"QUOTA_EXCEEDED for {user_id} {fcm_tokens[idx]}")
                  Notification_QUOTA_EXCEEDED(user_id=user_id, fcm_token=fcm_tokens[idx], retry_after_delay=retry_after_delay)
                  
                elif resp.exception.cause.status_code == 503:
                  # UNAVAILABLE
                  logger.error(f"UNAVAILABLE {user_id} {fcm_tokens[idx]}")
                  Notification_UNAVAILABLE(user_id=user_id, fcm_token=fcm_tokens[idx], retry_after_delay=retry_after_delay)
                
                elif resp.exception.cause.status_code == 500:
                  # INTERNAL
                  logger.error(f"INTERNAL error {user_id} {fcm_tokens[idx]}, retry backoff with timeout")
                  logger.error(resp.exception.cause)
                  Notification_INTENRAL(user_id=user_id, fcm_token=fcm_tokens[idx], retry_after_delay=retry_after_delay)

                elif resp.exception.cause.status_code == 401:
                  # THIRD_PARTY_AUTH_ERROR
                  logger.error(f"THIRD_PARTY_AUTH_ERROR, Check the validity of your development and production credentials. {user_id}.")
                  logger.error(resp.exception.cause)
                  # TODO Send alert email out
                
                else:
                  logger.error(f"UNSPECIFIED_ERROR {user_id} {fcm_tokens[idx]}.")

                failed_tokens.append(fcm_tokens[idx])
        logger.info('Notification failed for {0} tokens'.format(len(failed_tokens)))
      return failed_tokens
    except Exception as e:
      logger.exception(f"Unable to analyze the multicast response {response}")
      logger.exception(e)
      return False

async def Notification_design_and_multicast(user_id=None, pay_load=None, dry_run=True):
    """ Sends multicast notification to all devices of a userId

    Args:
      user_id: String of userId
      pay_load: Payload for notification. This paload consist of many attributes which are used
      to build the notification itself
      dry_run: Will not send multicast notification if set True; Default is True
    Returns:
      Boolean value if the notification was sent successfully
    """
    # Title and body of notification
    notification = messaging.Notification(title=pay_load['title'], body=pay_load['body'])
    # Firestore analytical label and notification image
    notification_image = pay_load['notification_image'] if pay_load['notification_image'] else amoreicon_image
    fcm_options = messaging.APNSFCMOptions(analytics_label=pay_load['analytics_label'], image=notification_image)
    # Badge Count and Notification Category
    aps = messaging.Aps(badge=pay_load['badge_count'], category=pay_load['aps_category'])
    payload = messaging.APNSPayload(aps=aps)
    apns = messaging.APNSConfig(fcm_options=fcm_options, payload=payload)

    # Logic to send notifications
    fcm_token_docs = Notification_fetch_fcm_token_docs_for_userId(user_id=user_id)
    fcm_tokens = Notification_get_fcm_tokens_from_redis_docs(fcm_token_docs=fcm_token_docs)
    if len(fcm_tokens) == 0:
        logger.error(f"No DeviceId and FCMToken record found for the userid {user_id}")
        return 
    response = Notification_send_muticastmessage_to_userId(user_id=user_id, 
                                            apns=apns,
                                            notification=notification,
                                            data=pay_load['data'],
                                            fcm_tokens=fcm_tokens, 
                                            dry_run=dry_run)
    failed_tokens = Notification_failed_tokens(user_id=user_id, pay_load=None, response=response, 
                                    fcm_tokens=fcm_tokens)
    return response

def Notification_delete_fcm_token(user_id=None, fcm_token=None):
  """Deletes FCMToken from redis and firestore
  Delete FCM Token record from redis
  Deletes the record from firestore

  : param user_id: user id for which the profile has to be deleted
  : param fcm_token: delete the fcm token to be deleted from firestore
  """
  try:
    logger.info(f"Deleting FCMToken for {user_id}")
    #TODO Deletes FCM Token record from redis
    fcm_redis_query = f"@fcmToken:{fcm_token}"
    fcm_token_docs = redis_client.ft("idx:FCMTokens").search(Query(query_string=fcm_redis_query))
    for token_doc in fcm_token_docs:
      token_doc = json.loads(token_doc.json)
      key = f"FCMTokens:{token_doc['userId']}:{token_doc['deviceId']}"
      redis_client.json().forget(key)
    #TODO Deletes the record from firestore
    doc_ref = db.collection('FCMTokens').document(user_id).collection('Devices').where(u'fcmToken', '==', fcm_token).get()
    for doc in doc_ref:
      db.delete(doc)

  except Exception as e:
    logger.exception(f"Unable to delete FCMToken {user_id} {fcm_token}")
    return False
  
def Notification_exponential_back_off(user_id=None, fcm_token=None, retry_after_delay=1):
    """The Notificaton exponential back off should honour all google policies around FCM
    https://firebase.google.com/docs/reference/fcm/rest/v1/ErrorCode

    TODO Add a logic in place to back off sending of individiual messages

    param user_id
    param fcm_token
    """
    try:
      default_delay = 0.2 # delay between two different messages in the pipeline
      time.sleep(default_delay)
      retryer = Retrying(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=retry_after_delay, max=5), reraise=True)
      return
    except RetryError:
      return

def Notification_UNAVAILABLE(user_id=None, fcm_token=None, retry_after_delay=1):
    """The server couldn't process the request in time. Retry the same request, but you must:
    TODO Honor the Retry-After header if it is included in the response from the FCM Connection Server.
    TODO Implement exponential back-off in your retry
    TODO Delay next message independently by an additional random amount to avoid issuing a new request for all messages at the same time.
    """
    Notification_exponential_back_off(user_id=user_id, fcm_token=fcm_token, retry_after_delay=retry_after_delay)
    return 

def Notification_QUOTA_EXCEEDED(user_id=None, fcm_token=None, retry_after_delay=1):
  """QUOTA_EXCEEDED: This error can be caused by exceeded message rate quota, exceeded device message rate quota, or exceeded topic message rate quota.
    TODO Handle Message rate exceeded - Decrease the message rate overall
      Createa global message variable using which we can throttle the speed of sending all notifications
    TODO HandleDevice message rate exceeded - The rate of messages to particular device is too high
      For individual device tracking create a variable in the redis to track if the notificatoins to this device
      needs to be throttled(may be keep track of exponential back off time for the device)
    
    https://firebase.google.com/docs/cloud-messaging/concept-options#device_throttling

    param user_id
    param fcm_token
  """
  time.sleep(10)
  Notification_exponential_back_off(user_id=user_id, fcm_token=fcm_token, retry_after_delay=retry_after_delay)
  return 

def Notification_INTENRAL(user_id=None, fcm_token=None, retry_after_delay=1):
  """INTENRAL: 
    TODO Retry the same request following request and Honor the Retry-After(Timeout)
    
    param user_id
    param fcm_token
  """
  Notification_exponential_back_off(user_id=user_id, fcm_token=fcm_token, retry_after_delay=retry_after_delay)
  return

def Notification_expire():
  """Pass Notification details to the message and expire the notification

  TODO Handling event when the user device is switched off. We don't want to send a swarm of messages to user when
  user device wakes up. Lets say a user phone is switched off for a day, the person received 10 messages and 20 matches
  we don't want to barrage user with a lot of notifications. 

https://firebase.google.com/docs/cloud-messaging/concept-options#device_throttling
    
  param time_to_live: default value of a notification expiration is 28 days from a fcm server
  param collapse: not sure about this functionality may not be required for now

  """
  return


if __name__ == "__main__":
  Notification_expire()