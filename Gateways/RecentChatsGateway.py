from ProjectConf.FirestoreConf import async_db

async def RecentChats_Unmatch_Delete_Chat(user_id_1: str = None, user_id_2: str = None):
    """
    Delete the recent chat from firestore
    :param user_id_1: Current User's UID
    :param user_id_2: Other User's UID
    :return:
    """
    recent_chat_ref = async_db.collection('RecentChats').document(user_id_1).collection("Messages").document(user_id_2)
    await recent_chat_ref.delete()
    return