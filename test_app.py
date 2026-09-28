import unittest
import json
import os
from app import app, FILE_NAME, SETTINGS_FILE, load_expenses, save_expenses, load_settings, save_settings

class ExpenseTrackerTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        # Backup original data
        self.original_expenses = load_expenses()
        self.original_settings = load_settings()

    def tearDown(self):
        # Restore original data
        save_expenses(self.original_expenses)
        save_settings(self.original_settings)

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
        self.assertIn('payment_method_summary', summary)

    def test_04_add_expense(self):
        new_item = {
            "amount": 350.50,
            "category": "Food",
            "payment_method": "UPI",
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
        self.assertEqual(data['data']['payment_method'], "UPI")
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
                                json={"amount": 99.0, "category": "Test", "payment_method": "Cash", "date": "2026-09-18"},
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

    def test_07_health_check(self):
        res = self.app.get('/health')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data['status'], 'healthy')

    def test_08_budget_get_and_post(self):
        # Update budget
        post_res = self.app.post('/api/budget',
                                 json={"monthly_budget": 45000.0},
                                 content_type='application/json')
        self.assertEqual(post_res.status_code, 200)

        # Get budget
        get_res = self.app.get('/api/budget')
        self.assertEqual(get_res.status_code, 200)
        data = json.loads(get_res.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['monthly_budget'], 45000.0)

    def test_09_sample_data_loader(self):
        res = self.app.post('/api/sample-data')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertGreater(data['count'], 0)

    def test_10_bulk_import_json(self):
        import_payload = [
            {"amount": 50.0, "category": "TestImport", "payment_method": "Cash", "date": "2026-09-01", "note": "Imp 1"},
            {"amount": 75.0, "category": "TestImport", "payment_method": "UPI", "date": "2026-09-02", "note": "Imp 2"}
        ]
        res = self.app.post('/api/expenses/import',
                            json=import_payload,
                            content_type='application/json')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['imported_count'], 2)

    def test_11_export_json(self):
        res = self.app.get('/api/export/json')
        self.assertEqual(res.status_code, 200)
        self.assertIn("attachment", res.headers.get("Content-Disposition", ""))


if __name__ == '__main__':
    unittest.main()
