import unittest
from unittest.mock import patch, MagicMock
import json
from app import app

class TestBase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['DEBUG'] = False
        
        self.client = self.app.test_client()
        pass
    

    def tearDown(self):
        # Tear down code goes here
        pass


