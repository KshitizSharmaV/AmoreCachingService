from flask import Blueprint, jsonify, request

from ProjectConf.AsyncioPlugin import run_coroutine
from Utilities.LogSetup import logger

from Gateways.LikesDislikesGateway import LikesDislikes_async_store_likes_dislikes_superlikes_for_user
from Gateways.MatchUnmatchGateway import MatchUnmatch_unmatch_two_users
from Gateways.RewindGateway import Rewind_task_function, get_last_given_swipe_from_firestore
from Gateways.ReportProfile import Report_profile_task
from Gateways.GeoserviceGateway import GeoService_store_profiles
from Gateways.MessagesGateway import match_two_profiles_for_direct_message
from Gateways.ProfilesGateway import ProfilesGateway_get_profile_by_ids

app_set = Blueprint('appSet', __name__)

# store_likes_dislikes_superlikes store likes, dislikes and superlikes in own user id and other profile being acted on
@app_set.route('/storelikesdislikesGate', methods=['POST'])
def store_likes_dislikes_superlikes():
    """
    Endpoint to store likes, superlikes, dislikes, liked_by, disliked_by, superliked_by for users
    """
    try:
        """
        Body of Request contains following payloads:
        - current user id
        - swipe info: Like, Dislike, Superlikes
        - swiped profile id
        """
        currentUserId = request.get_json().get('currentUserId')
        swipeInfo = request.get_json().get('swipeInfo')
        swipedUserId = request.get_json().get('swipedUserId')
        upgradeLikeToSuperlike = request.get_json().get('upgradeLikeToSuperlike')

        # tupule to check if any request param is None
        future = run_coroutine(LikesDislikes_async_store_likes_dislikes_superlikes_for_user(currentUserId=currentUserId,
                                                                                            swipedUserId=swipedUserId,
                                                                                            swipeStatusBetweenUsers=swipeInfo,
                                                                                            upgradeLikeToSuperlike=upgradeLikeToSuperlike))
        future.result()
        logger.info(f"Storing {currentUserId} {swipeInfo} on {swipedUserId}")
        return jsonify({'status': 200})
    except Exception as e:
        logger.exception(f"Unable to store likes dislikes super likes {currentUserId}:{swipedUserId}:{swipeInfo} ")
        logger.exception(e)
        return jsonify({'status': 500, 'message': 'Unable to process request'}), 500


@app_set.route('/unmatchgate', methods=['POST'])
def unmatch():
    try:
        current_user_id = request.get_json().get('current_user_id')
        other_user_id = request.get_json().get('other_user_id')
        future = run_coroutine(MatchUnmatch_unmatch_two_users(current_user_id=current_user_id, 
                                                        other_user_id=other_user_id))
        future.result()
        logger.info(f"Successfully Unmatched {current_user_id} and {other_user_id}")
        return jsonify({'status': 200})
    except Exception as e:
        logger.exception(f"Unable to unmatch {current_user_id} and {other_user_id}")
        logger.exception(e)
        return jsonify({'status': 500, 'message': 'Unable to process request'}), 500


@app_set.route('/rewindsingleswipegate', methods=['POST'])
def rewind_single_swipe():
    """
    Rewind a single swipe:
        - get the last given swipe according to timestamp
        - rewind tasks
        - return the profile back to client
    """
    try:
        current_user_id = request.get_json().get('currentUserID')
        if current_user_id:
            swiped_user_id, swipeStatusBetweenUsers = get_last_given_swipe_from_firestore(current_user_id=current_user_id)
            future = run_coroutine(Rewind_task_function(current_user_id=current_user_id, 
                                                        swiped_user_id=swiped_user_id,
                                                        swipeStatusBetweenUsers=swipeStatusBetweenUsers))
            future.result()
            allProfilesData = run_coroutine(ProfilesGateway_get_profile_by_ids(profileIdList=[swiped_user_id]))
            allProfilesData = allProfilesData.result()
            rewinded_user_info = allProfilesData[0]
            rewinded_dict = {"rewindedUserCard": rewinded_user_info, "swipeStatusBetweenUsers": swipeStatusBetweenUsers}
            logger.info(f"Successfully rewinded {swipeStatusBetweenUsers} by {current_user_id}")
            return jsonify(rewinded_dict)
        else:
            logger.warning(f"Invalid current User ID")
            return jsonify({'status': 500})
    except Exception as e:
        logger.exception(f"Unable to rewind swipe by {current_user_id}")
        logger.exception(e)
        return jsonify({'status': 500, 'message': 'Unable to process request'}), 500


@app_set.route('/storeProfileInBackendGate', methods=['POST'])
def store_profile():
    """
    Stores Profile in Cache.
    Request Parameters:
        - profile: Dict/JSON containing Profile information of the currently logged-in user.
    Returns: Status Message for Amore Flask.
    """
    try:
        profile = request.get_json().get('profile')
        # Update the cache with profile data?
        future = run_coroutine(GeoService_store_profiles(profile=profile))
        result = future.result()
        logger.info(f"{profile['id']}: Successfully stored profile in Cache/DB")
        response = jsonify({'message': f"{profile['id']}: Successfully stored profile in Cache/DB"})
        response.status_code = 200
        return response
    except Exception as e:
        logger.exception(f"{profile['id']}: Unable to stored profile in Cache/DB")
        logger.exception(e)
        response = jsonify({'message': 'An error occured in API /storeProfileInBackendGate'})
        response.status_code = 400
        return response

@app_set.route('/reportprofilegate', methods=['POST'])
def report_profile():
    """
    Report Profile API:
        - Report Profile Task: View Function Docstring for explanation
        - Unmatch Task: View Function Docstring for explanation
    Returns: Status Message for Amore Flask.
    """
    current_user_id, reported_profile_id = None, None
    try:
        current_user_id = request.get_json().get('current_user_id')
        reported_profile_id = request.get_json().get('other_user_id')
        reason_given = request.get_json().get('reasonGiven')
        description_given = request.get_json().get('descriptionGiven')
        status = Report_profile_task(current_user_id=current_user_id, reported_profile_id=reported_profile_id,
                                     reason_given=reason_given, description_given=description_given)
        future = run_coroutine(MatchUnmatch_unmatch_two_users(current_user_id=current_user_id, 
                                                    other_user_id=reported_profile_id))
        future.result()
        logger.info(f"Successfully reported profile {reported_profile_id}")
        return jsonify({'status': 200})
    except Exception as e:
        logger.exception(f"Unable to report profile {reported_profile_id}")
        logger.exception(e)
        return jsonify({'status': 500, 'message': 'Unable to process request'}), 500



@app_set.route('/matchondirectmessageGate', methods=['POST'])
def match_profiles_on_direct_message():
    """
    Report Profile API:
        - Report Profile Task: View Function Docstring for explanation
        - Unmatch Task: View Function Docstring for explanation
    Returns: Status Message for Amore Flask.
    """
    current_user_id, other_user_id = None, None
    try:
        current_user_id = request.get_json().get('currentUserId')
        other_user_id = request.get_json().get('otherUserId')
        future = run_coroutine(
            match_two_profiles_for_direct_message(current_user_id=current_user_id, other_user_id=other_user_id))
        _ = future.result()
        logger.info(f"Successfully matched profile {current_user_id} and {other_user_id}")
        return jsonify({'status': 200})
    except Exception as e:
        logger.exception(f"Unable to match profiles {current_user_id} and {other_user_id}")
        logger.exception(e)
        return jsonify({'status': 500, 'message': 'Unable to process request'}), 500
