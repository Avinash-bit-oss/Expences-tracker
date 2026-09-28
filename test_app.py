import unittest
import json
import os
from app import app, FILE_NAME, load_expenses, save_expenses

class ExpenseTrackerTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        # Backup original data
        self.original_expenses = load_expenses()

    def tearDown(self):
        # Restore original data
        save_expenses(self.original_expenses)

    def test_01_get_home_page(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Expense Tracker", response.data)

    def test_02_get_expenses(self):
        response = self.app.get('/api/expenses')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIsInstance(data['data'], list)

    def test_03_get_summary(self):
        response = self.app.get('/api/summary')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        summary = data['data']
        self.assertIn('total', summary)
        self.assertIn('category_summary', summary)
        self.assertIn('monthly_summary', summary)

    def test_04_add_expense(self):
        new_item = {
            "amount": 350.50,
            "category": "Food",
            "date": "2026-09-18",
            "note": "Unit test lunch"
        }
        response = self.app.post('/api/expenses',
                                json=new_item,
                                content_type='application/json')
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['amount'], 350.50)
        created_id = data['data']['id']

        # Verify it can be fetched
        get_res = self.app.get('/api/expenses')
        get_data = json.loads(get_res.data)
        found = any(exp['id'] == created_id for exp in get_data['data'])
        self.assertTrue(found)

        # Clean up by deleting
        del_res = self.app.delete(f'/api/expenses/{created_id}')
        self.assertEqual(del_res.status_code, 200)

    def test_05_delete_expense(self):
        # First add one
        add_res = self.app.post('/api/expenses',
                                json={"amount": 99.0, "category": "Test", "date": "2026-09-18"},
                                content_type='application/json')
        add_data = json.loads(add_res.data)
        temp_id = add_data['data']['id']

        # Delete it
        del_res = self.app.delete(f'/api/expenses/{temp_id}')
        self.assertEqual(del_res.status_code, 200)
        del_data = json.loads(del_res.data)
        self.assertTrue(del_data['success'])

        # Try to delete again (should fail with 404)
        del_again = self.app.delete(f'/api/expenses/{temp_id}')
        self.assertEqual(del_again.status_code, 404)

    def test_06_validation_error(self):
        # Negative amount
        res = self.app.post('/api/expenses', json={"amount": -10, "category": "Food"})
        self.assertEqual(res.status_code, 400)

        # Empty category
        res2 = self.app.post('/api/expenses', json={"amount": 100, "category": ""})
        self.assertEqual(res2.status_code, 400)

if __name__ == '__main__':
    unittest.main()
