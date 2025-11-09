import os
import tempfile
from django.test import TestCase, override_settings
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from .models import UploadedFile
import pandas as pd
from io import StringIO


class UploadViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')

    def test_csv_upload_no_conversion(self):
        """Test uploading a CSV file - should not be converted."""
        csv_content = "name,age\nJohn,25\nJane,30"
        csv_file = ContentFile(csv_content.encode('utf-8'), name='test.csv')

        # Simulate POST request
        response = self.client.post('/upload/', {'file': csv_file})

        # Should redirect to result page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/result/', response.url)

        # Check that file was created with correct type
        uploaded_file = UploadedFile.objects.last()
        self.assertEqual(uploaded_file.file_type, 'csv')
        self.assertEqual(uploaded_file.user, None)  # Anonymous user

    def test_json_upload_conversion(self):
        """Test uploading a JSON file - should be converted to CSV."""
        json_content = '[\n  {"name": "John", "age": 25},\n  {"name": "Jane", "age": 30}\n]'
        json_file = ContentFile(json_content.encode('utf-8'), name='test.json')

        response = self.client.post('/upload/', {'file': json_file})

        self.assertEqual(response.status_code, 302)
        self.assertIn('/result/', response.url)

        uploaded_file = UploadedFile.objects.last()
        self.assertEqual(uploaded_file.file_type, 'csv')

        # Verify the file was converted correctly
        df = pd.read_csv(uploaded_file.file.path)
        self.assertEqual(len(df), 2)
        self.assertListEqual(list(df.columns), ['name', 'age'])

    def test_xlsx_upload_conversion(self):
        """Test uploading an XLSX file - should be converted to CSV."""
        # Create a temporary XLSX file
        df = pd.DataFrame({'name': ['John', 'Jane'], 'age': [25, 30]})
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            df.to_excel(tmp.name, index=False, engine='openpyxl')
            with open(tmp.name, 'rb') as f:
                xlsx_content = f.read()

        xlsx_file = ContentFile(xlsx_content, name='test.xlsx')

        response = self.client.post('/upload/', {'file': xlsx_file})

        self.assertEqual(response.status_code, 302)
        self.assertIn('/result/', response.url)

        uploaded_file = UploadedFile.objects.last()
        self.assertEqual(uploaded_file.file_type, 'csv')

        # Verify the file was converted correctly
        df_converted = pd.read_csv(uploaded_file.file.path)
        self.assertEqual(len(df_converted), 2)
        self.assertListEqual(list(df_converted.columns), ['name', 'age'])

        # Clean up
        os.unlink(tmp.name)

    def test_invalid_json_upload(self):
        """Test uploading invalid JSON file - should return error."""
        invalid_json = '{"name": "John", "age": }'  # Invalid JSON
        json_file = ContentFile(invalid_json.encode('utf-8'), name='invalid.json')

        response = self.client.post('/upload/', {'file': json_file})

        self.assertEqual(response.status_code, 200)  # Should render upload page with error
        self.assertContains(response, 'Error converting file to CSV')

    def test_unsupported_file_type(self):
        """Test uploading unsupported file type."""
        txt_content = "This is a text file"
        txt_file = ContentFile(txt_content.encode('utf-8'), name='test.txt')

        response = self.client.post('/upload/', {'file': txt_file})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Unsupported file type')

    def test_empty_file_upload(self):
        """Test uploading empty file."""
        empty_file = ContentFile(b'', name='empty.csv')

        response = self.client.post('/upload/', {'file': empty_file})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'The uploaded file is empty.')
