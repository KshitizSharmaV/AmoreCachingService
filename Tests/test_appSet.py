import unittest
from unittest.mock import patch

from tempfile import TemporaryFile
import flask
from flask import Blueprint, current_app, jsonify, request
import json
import logging
import asyncio
import traceback
import pandas as pd
import json

from Tests.test_base import TestBase
from ProjectConf.AsyncioPlugin import run_coroutine
from ProjectConf.FirestoreConf import async_db, db
from Gateways.GradingScoresGateway import store_graded_profile_in_firestore_route
from Gateways.LikesDislikesGateway import LikesDislikes_async_store_likes_dislikes_superlikes_for_user
from Gateways.MatchUnmatchGateway import MatchUnmatch_unmatch_two_users
from Gateways.RewindGateway import Rewind_task_function, get_last_given_swipe_from_firestore
from Gateways.ReportProfile import Report_profile_task
from Gateways.GeoserviceGateway import GeoService_store_profiles
from Gateways.MessagesGateway import match_two_profiles_for_direct_message
from Gateways.ProfilesGateway import ProfilesGateway_get_profile_by_ids

class TestAppSet(TestBase):
    
    def test_store_likes_dislikes_superlikes(self):
        
        # Test successful request
        with patch.object(LikesDislikes_async_store_likes_dislikes_superlikes_for_user, '__call__', return_value=True):
            response = self.client.post('/storelikesdislikesGate', json={
                'currentUserId': 'user1',
                'swipeInfo': 'like',
                'swipedUserId': 'user2',
                'upgradeLikeToSuperlike': False
            })
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json(), {'status': 200})
