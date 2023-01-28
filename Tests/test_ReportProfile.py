import pytest
import time
from ProjectConf.FirestoreConf import async_db, db
from unittest.mock import patch
from Tests.Utilities.test_base import async_mock_child
from Gateways.ReportProfile import Report_profile_task
from Tests.Utilities.test_base import redis_test_set

@pytest.mark.asyncio
async def test_report_profle_task_success():
    current_user_id = "UserId1"
    reported_profile_id = "UserId2"
    reason_given = "Test Reason"
    description_given = "Test Description"
    with patch('Gateways.ReportProfile.db') as db:
        with patch('Gateways.ReportProfile.redis_client.set') as mock_redis_set:
            db.collection.return_value.document.return_value.collection.return_value.document.return_value.set.side_effect= await async_mock_child(return_value=True)
            key = "ReportedProfile:{reported_profile_id}:{current_user_id}"
            store_doc =  {
                "reportedById": current_user_id,
                "idBeingReported": reported_profile_id,
                "reasonGiven": reason_given,
                "descriptionGiven": description_given,
                "timestamp": time.time()
            }
            mock_redis_set.side_effect = redis_test_set(key,store_doc)
            result= Report_profile_task(current_user_id= current_user_id, 
                    reported_profile_id= reported_profile_id, 
                    reason_given=reason_given,
                    description_given=description_given)
            result == True

@pytest.mark.asyncio
async def test_report_profle_task_failure():
    current_user_id = "UserId1"
    reported_profile_id = "UserId2"
    reason_given = "Test Reason"
    description_given = "Test Description"
    with patch('Gateways.ReportProfile.db') as db:
        with patch('Gateways.ReportProfile.redis_client.set') as mock_redis_set:
            db.collection.return_value.document.return_value.collection.return_value.document.return_value.set.side_effect= Exception("Exception Raised")
            key = "ReportedProfile:{reported_profile_id}:{current_user_id}"
            store_doc =  {
                "reportedById": current_user_id,
                "idBeingReported": reported_profile_id,
                "reasonGiven": reason_given,
                "descriptionGiven": description_given,
                "timestamp": time.time()
            }
            mock_redis_set.side_effect = redis_test_set(key,store_doc)
            result= Report_profile_task(current_user_id= current_user_id, 
                    reported_profile_id= reported_profile_id, 
                    reason_given=reason_given,
                    description_given=description_given)
            result == False