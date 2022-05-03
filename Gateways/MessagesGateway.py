

# after unmatch call this function, to remove profiles from recentchats too
async def unmatch_task_recent_chats(profileId1 = None, profileId2 = None, async_db=None):
    recent_chat_ref = async_db.collection('RecentChats').document(profileId1).collection("Messages").document(profileId2)
    await recent_chat_ref.delete()

