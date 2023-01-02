import unittest
import json

from Tests.test_base import TestBase

class TestApiEndpoints(TestBase):
    
    def test_test_route(self):
        response = self.client.get('/test')
        data = json.loads(response.get_data())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], True)
        self.assertEqual(data['service'], 'Amore Caching Service')

