import pytest
from unittest.mock import patch, AsyncMock
from Gateways.MatchUnmatchGateway import *
from Tests.Utilities.test_base import client, async_mock_child
import asyncio
from unittest.mock import call



@pytest.mark.asyncio
async def test_MatchUnmatch_get_match_unmatch_nomatch_for_user_success():
    
    with patch("Gateways.MatchUnmatchGateway.MatchUnmatch_fetch_userdata_from_firebase_or_redis") as mock_fetch_userdata:
        
        userId = "123"

        # set the return value of the mock function
        mock_fetch_userdata.return_value = "mock data"

        # call the function under test
        result = await MatchUnmatch_get_match_unmatch_nomatch_for_user(userId)

        # assert that the function was called with the correct arguments
        assert mock_fetch_userdata.await_count == 3
        assert mock_fetch_userdata.await_args_list == [
            call(userId='123', childCollectionName='Match'),
            call(userId='123', childCollectionName='Unmatch'),
            call(userId='123', childCollectionName='NoMatch')
         ]


        # assert that the function returned the expected result
        assert result == ["mock data", "mock data", "mock data"]
        
    
    
@pytest.mark.asyncio
async def test_MatchUnmatch_send_message_notification_success():
    
    with patch("Gateways.MatchUnmatchGateway.datetime") as mock_datetime:
        mock_date_str = mock_datetime.today.return_value.strftime.return_value
        
        # Prepare the test data
        pay_load = {
        'title':"You have a new Match 😍 !! ",
        'body':"Let's break the 🧊 🔨",
        'analytics_label': "Match" + mock_date_str,
        'badge_count':1,
        'notification_image':None,
        'aps_category':'Match',
        'data':{'data':None}
        }

        with patch("Gateways.MatchUnmatchGateway.Notification_design_and_multicast") as mock_not:
            
            
            # Call the function to test
            result = await mock_not(user_id="user_id", pay_load=pay_load, dry_run=False)

            # Assert the expected results
            assert result
        


 
