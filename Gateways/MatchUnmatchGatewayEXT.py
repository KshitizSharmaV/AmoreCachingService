""""
Matching Engine Translated Here
"""


from datetime import datetime
import time
from ProjectConf.FirestoreConf import async_db
from Gateways.ProfilesGateway import ProfilesGateway_get_profile_by_ids
from Gateways.LikesDislikesGatewayEXT import LikesDislikes_fetch_userdata_from_firebase_or_redis

async def MatchUnmatch_check_match_between_users(currentUserId=None, swipedUserId=None, currentUserSwipe=None, redisClient=None, logger=None):
    '''
    Check the match between both users
        : If the swipe given is like or superlike
            : Fetch the Likes or Superlikes Given by the Swiped id
            : If swipedUserId has also swiped a 'Like' or '' on currentUserId
                : Write to Match collection for both users in firestore
                : Get profile data from redis/firestore - Need information to write to RecentChat in firestore
                : Write to Recent Chats collection for both users in firestore
                : Update redis with new matches for both users
        : Else:
            : User gave a dislike no need to calculate a match
    '''
    try:
        # If the swipe given is Likes or Superlikes
        if currentUserSwipe == "Likes" or currentUserSwipe == "Superlikes":
            
            # Fetch list of Given Likes by receiver
            likesGivenBySwipedUser = await LikesDislikes_fetch_userdata_from_firebase_or_redis(userId=swipedUserId, 
                                                        collectionNameChild="Given", 
                                                        swipeStatusBetweenUsers="Likes",
                                                        redisClient=redisClient, 
                                                        logger=logger)
            # Fetch list of Given Superlikes  by receiver
            superlikesGivenBySwipedUser = await LikesDislikes_fetch_userdata_from_firebase_or_redis(userId=swipedUserId, 
                                                        collectionNameChild="Given", 
                                                        swipeStatusBetweenUsers="Superlikes",
                                                        redisClient=redisClient, 
                                                        logger=logger)  
            
            # Check if swipedUserId has also swiped on currentUserId
            if currentUserId in (likesGivenBySwipedUser + superlikesGivenBySwipedUser):
                logger.info(f'{currentUserId} & {swipedUserId} swiped on each other, its a Match')
                
                # Write Match to firestore
                query = async_db.collection("LikesDislikes").document(currentUserId).collection("Match").document(swipedUserId)
                await query.set({"id": swipedUserId, "timestamp": time.time()})

                query = async_db.collection("LikesDislikes").document(swipedUserId).collection("Match").document(currentUserId)
                await query.set({"id": currentUserId, "timestamp": time.time()})
                
                # Fetch the user data for current user and swiped user id
                currentUserData = await ProfilesGateway_get_profile_by_ids(redisClient=redisClient, profileIdList=[currentUserId], logger=logger, async_db=async_db)
                currentUserData = currentUserData.pop()
                swipedUserData = await ProfilesGateway_get_profile_by_ids(redisClient=redisClient, profileIdList=[swipedUserId], logger=logger, async_db=async_db)
                swipedUserData = swipedUserData.pop()

                # Write match to recent chats
                query = async_db.collection("RecentChats").document(currentUserId).collection("Messages").document(swipedUserId)
                await query.set({"fromId": currentUserId, 
                                    "toId": swipedUserId, 
                                    "timestamp": datetime.now(), 
                                    "lastText": "", 
                                    "user": {
                                        "firstName": swipedUserData["firstName"], 
                                        "lastName": swipedUserData["lastName"], 
                                        "image1": swipedUserData["image1"], 
                                        "id": swipedUserId
                                    }, 
                                    "otherUserUpdated": True, 
                                    "directMessageApproved": True})


                query = async_db.collection("RecentChats").document(swipedUserId).collection("Messages").document(currentUserId)
                await query.set({"fromId": swipedUserId, 
                        "toId": currentUserId, 
                        "timestamp": datetime.now(), 
                        "lastText": "", 
                        "user": {
                            "firstName": currentUserData["firstName"], 
                            "lastName": currentUserData["lastName"], 
                            "image1": currentUserData["image1"], 
                            "id": currentUserId
                        }, 
                        "otherUserUpdated": True, 
                        "directMessageApproved": True})                                                                                                        

                # Write Match to redis
                redisClient.sadd(f"MatchUnmatch:{currentUserId}:Match",swipedUserId)
                redisClient.sadd(f"MatchUnmatch:{swipedUserId}:Match",currentUserId)
                logger.info(f"Match successfully written in redis/firestore for {swipedUserId} & {currentUserId}")    
            else:
                logger.info(f"{swipedUserId} didn't either swiped on {currentUserId} OR gave a dislike")    
        else:
            # User gave a dislike no need to calculate a match
            logger.info(f"{currentUserId} gave {swipedUserId} a dislike ")
        return True
    except Exception as e:
        logger.error(f"Unable to calcualte the match {currentUserId} {swipedUserId}")
        logger.exception(e)
        return False


# logic to check the match between the 2 users
def MatchUnmatch_calculate_the_match(firstUserSwipe=None,secondUserSwipe=None, logger=None):
    try:
        if firstUserSwipe == "Likes":
            if secondUserSwipe == "Likes": return "Match"
            if secondUserSwipe == "Superlikes": return "Match"
            if secondUserSwipe == "Dislikes": return "NoMatch"
        elif firstUserSwipe == "Superlikes":
            if secondUserSwipe == "Like": return "Match"
            if secondUserSwipe == "Dislikes": return "NoMatch"
            if secondUserSwipe == "Superlikes": return "Match"
        elif firstUserSwipe == "Dislikes":
            if secondUserSwipe == "Superlikes": return "NoMatch"
            if secondUserSwipe == "Likes": return "NoMatch"
            if secondUserSwipe == "Dislikes": return "NoMatch"
    except Exception as e:
        logger.error(f"Unable to calcualte the match {firstUserSwipe} {secondUserSwipe}")
        logger.exception(e)
        return False