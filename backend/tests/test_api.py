import csv
import io
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

import app as lead_finder_app


class LeadFinderApiTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_db = lead_finder_app.DB
        lead_finder_app.DB = Path(self.temp_dir.name) / 'test_leads.db'
        self.client = TestClient(lead_finder_app.app)
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)
        lead_finder_app.DB = self.original_db
        self.temp_dir.cleanup()

    def test_health_and_options_match_api_contract(self):
        health = self.client.get('/api/health')
        options = self.client.get('/api/options')

        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()['mode'], 'demo-data')
        self.assertFalse(health.json()['real_discovery'])
        self.assertEqual(options.status_code, 200)
        self.assertEqual(options.json()['countries'], ['UAE'])
        self.assertIn('Dubai', options.json()['cities'])

    def test_leads_returns_typed_records(self):
        response = self.client.get('/api/leads?limit=1')

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['demo'])
        self.assertEqual(len(payload['items']), 1)
        self.assertIn('created_at', payload['items'][0])
        self.assertEqual(payload['items'][0]['country'], 'UAE')

    def test_search_uses_defaults_and_accepts_valid_request(self):
        response = self.client.post('/api/search', json={'limit': 1})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['status'], 'completed')
        self.assertEqual(payload['requested'], 1)
        self.assertEqual(payload['accepted'], len(payload['items']))
        self.assertIn('notice', payload)

    def test_search_rejects_out_of_range_limit(self):
        response = self.client.post('/api/search', json={'limit': 201})

        self.assertEqual(response.status_code, 422)
        self.assertIn('detail', response.json())

    def test_search_rejects_missing_request_body(self):
        response = self.client.post('/api/search')

        self.assertEqual(response.status_code, 422)
        self.assertIn('detail', response.json())

    def test_search_rejects_unsupported_country(self):
        response = self.client.post('/api/search', json={'country': 'Canada'})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['detail'], 'This prototype currently supports UAE only.')

    def test_export_returns_filtered_csv(self):
        response = self.client.get('/api/export.csv?niche=Clinics')

        self.assertEqual(response.status_code, 200)
        rows = list(csv.DictReader(io.StringIO(response.text)))
        self.assertTrue(rows)
        self.assertTrue(all(row['niche'] == 'Clinics' for row in rows))

    def test_reset_demo_restores_seed_records(self):
        self.client.post('/api/reset-demo')
        response = self.client.get('/api/leads')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['items']), len(lead_finder_app.SEED))


if __name__ == '__main__':
    unittest.main()