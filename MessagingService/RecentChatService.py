import sys
import os.path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

import traceback
import os
import threading
import time
import logging
from time import strftime
from datetime import datetime
from dataclasses import asdict, dataclass
from logging.handlers import TimedRotatingFileHandler
from ProjectConf.FirestoreConf import db, async_db
from google.cloud import firestore
from MessagingService.Helper import *


# Log Settings
LOG_FILENAME = datetime.now().strftime("%H_%M_%d_%m_%Y")+".log"
if not os.path.exists('Logs/MessagingService/'):
    os.makedirs('Logs/MessagingService/')
logHandler = TimedRotatingFileHandler(f"Logs/MessagingService/{LOG_FILENAME}",when="midnight")
logFormatter = logging.Formatter(f'%(asctime)s %(levelname)s %(threadName)s : %(message)s')
logHandler.setFormatter(logFormatter)
logger = logging.getLogger(f'Logs/MessagingService/{LOG_FILENAME}')
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)


def message_update_handler(given_user_id, other_user_id):
    try:
        new_messages = db.collection("Messages").document(given_user_id).collection(other_user_id).where(u'otherUserUpdated', u'==', False).stream()
        for message in new_messages:
            message_data = ChatText.from_dict(message.to_dict())
            message_data.otherUserUpdated = True
            db.collection("Messages").document(other_user_id).collection(given_user_id).add(asdict(message_data))
            db.collection("Messages").document(given_user_id).collection(other_user_id).document(message.id).update({'otherUserUpdated':True})
        logger.info(f'{given_user_id} & {other_user_id}: written to message collection')
        return
    except Exception as e:
        logger.error(f"{given_user_id} & {other_user_id}: error occured while writting to Messages collection")
        logger.error(traceback.format_exc())
        return False               

    
# When a user sends new message the RecentChats and Messages collections are updated, the listener listens RecentChats to update and calls this function
def recent_chat_update_handler(given_user_id=None):
    try:
        # we fetch only the new recent chats by Checking if otherUserUpdated is not True
        new_recent_chats = db.collection("RecentChats").document(given_user_id).collection("Messages").where(u'otherUserUpdated', u'==', False).stream()
        logger.info(f'Itering over UserIds where otherUserUpdated == False')
        for chat in new_recent_chats:
            # Get the id of the other user
            other_user_id = chat.id
            # Recent Chat data from Given User's RecentChats
            chat_data = chat.to_dict()
            chat_data = ChatConversation.from_dict(chat_data)
            # Get the data for other user whose chat needs to be updated
            given_user_data =  db.collection("Profiles").document(given_user_id).get().to_dict()
            given_user_data["id"] = given_user_id
            # Create data for other user's RecentChats
            chat_data_for_other_user = chat_data
            chat_data_for_other_user.user = ChatUser.from_dict(given_user_data)
            chat_data_for_other_user.otherUserUpdated = True
            # Update the data for the other user
            db.collection("RecentChats").document(other_user_id).collection("Messages").document(given_user_id).set(asdict(chat_data_for_other_user))
            logger.info(f'{other_user_id}: successfully(other_user_id) written in RecentChats')
            # set the otherUserUpdated = True for given user, because we have processed this new recent chat
            db.collection("RecentChats").document(given_user_id).collection("Messages").document(other_user_id).update({'otherUserUpdated':True})
            logger.info(f'{given_user_id}: otherUserUpdated(given_user_id) was set as True')
            message_update_handler(given_user_id=given_user_id, other_user_id=other_user_id)
        # set the wasUpdated = False, because we processed the change
        db.collection("RecentChats").document(given_user_id).update({'wasUpdated':False})
        return
    except Exception as e:
        logger.error(f"{given_user_id}: Error occrured while processing the new message in recent_chat_update_handler")
        logger.error(traceback.format_exc())
        return False               



# here each change that is listened to is processed
# each change can be of 3 types Added, Modified or Removed, these are 3 properties of firebase itself
# we only want to action when a new message is sent
def recent_chat_update_event_check(change=None):
    try:
        if change.type.name == 'ADDED':
            logger.info(f'{change.document.id}: listener message was added')
            recent_chat_update_handler(given_user_id=change.document.id)
        elif change.type.name == 'MODIFIED':
            logger.info(f'{change.document.id}: listener message was modified')
        elif change.type.name == 'REMOVED':
            logger.info(f'{change.document.id}: listener message was removed/overwritten by other message')
    except Exception as e:
        logger.error(f"{change.document.id}: Error occrured in the messaging listener")
        logger.error(traceback.format_exc())
        return False               

# this function will be called every time firebase hears a change on a document in LikesDislikes
def recent_chat_update_listener(col_snapshot, changes, read_time):
    _ = [recent_chat_update_event_check(change=change) for change in changes]


callback_done = threading.Event()
if __name__ == '__main__':
    query_watch = None
    try:
        logger.info("Messaging Service Triggered")
        # Query the documents inside RecentChats collection where wasUpdated == true
        # if wasUpdated == true that means the given user sent a new message
        col_query = db.collection(u'RecentChats').where(u'wasUpdated', '==', True)
        # Watch the collection query
        query_watch = col_query.on_snapshot(recent_chat_update_listener)
        while True:
            time.sleep(1)
    except Exception as e:
        logger.error("Main: Error occured in triggering Messaging Service")
        logger.error(traceback.format_exc())
        logger.warning("Main:Un-suscribed from Messaging Service")
    finally:
        # Unsuscribe from all the listeners
        print("Finally was executed")
        logger.error("Error: Recent Chat Service was Unsubscribed")
        query_watch.unsubscribe()
    callback_done.set()
