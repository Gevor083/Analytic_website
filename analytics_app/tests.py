"""
Comprehensive test suite for the analytics app.
Covers: uploads, auth, ownership/permissions, API, utils, tasks, delete & reanalyze.
"""

import os
import json
import tempfile
from io import StringIO

import pandas as pd
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from .models import UploadedFile, ProcessedData
from .utils import (
    make_json_serializable,
    get_numeric_fields,
    get_categorical_fields,
    detect_outliers_iqr,
    group_and_calculate_stats,
    apply_filter,
    apply_sort,
    generate_text_insights,
)


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════

CSV_CONTENT = "name,age,salary\nAlice,30,50000\nBob,25,40000\nCarol,35,60000\n"


def _make_csv_file(content=CSV_CONTENT, name='test.csv'):
    return ContentFile(content.encode('utf-8'), name=name)


def _make_processed_file(user=None, content=CSV_CONTENT):
    """Create and process an UploadedFile synchronously for test setup."""
    f = UploadedFile.objects.create(
        file=_make_csv_file(content),
        file_type='csv',
        user=user,
        processed=True,
        num_rows=3,
    )
    df = pd.read_csv(StringIO(content))
    for col in df.select_dtypes(include='number').columns:
        series = df[col]
        ProcessedData.objects.create(
            uploaded_file=f,
            column_name=col,
            data_type='numeric',
            value=float(series.mean()),
            stats={
                'mean': float(series.mean()),
                'std': float(series.std()),
                'min': float(series.min()),
                'max': float(series.max()),
                'count': int(series.count()),
                'missing': 0,
                'outliers': {'count': 0, 'values': []},
                'histogram': {'bins': [], 'counts': []},
                'sample_values': series.tolist(),
            },
        )
    return f


# ══════════════════════════════════════════════════════════════════════════════
# Utils tests
# ══════════════════════════════════════════════════════════════════════════════

class UtilsTestCase(TestCase):
    def setUp(self):
        self.df = pd.DataFrame({
            'age':    [25, 30, 35, 100],   # 100 is an outlier
            'salary': [40000, 50000, 60000, 45000],
            'dept':   ['Eng', 'HR', 'Eng', 'HR'],
        })

    def test_make_json_serializable_nan(self):
        import numpy as np
        result = make_json_serializable(float('nan'))
        self.assertIsNone(result)

    def test_make_json_serializable_numpy(self):
        import numpy as np
        result = make_json_serializable(np.int64(42))
        self.assertEqual(result, 42)
        self.assertIsInstance(result, int)

    def test_get_numeric_fields(self):
        fields = get_numeric_fields(self.df)
        self.assertIn('age', fields)
        self.assertIn('salary', fields)
        self.assertNotIn('dept', fields)

    def test_get_categorical_fields(self):
        fields = get_categorical_fields(self.df)
        self.assertIn('dept', fields)

    def test_detect_outliers_iqr(self):
        result = detect_outliers_iqr(self.df['age'])
        self.assertEqual(result['count'], 1)
        self.assertIn(100, result['values'])

    def test_detect_outliers_non_numeric(self):
        result = detect_outliers_iqr(self.df['dept'])
        self.assertEqual(result, {'count': 0, 'values': []})

    def test_group_and_calculate_stats(self):
        result = group_and_calculate_stats(self.df, 'dept', 'salary')
        self.assertTrue(len(result) > 0)
        self.assertIn('x', result[0])
        self.assertIn('y', result[0])
        self.assertIn('stats', result[0])

    def test_group_missing_column(self):
        result = group_and_calculate_stats(self.df, 'nonexistent', 'salary')
        self.assertEqual(result, [])

    def test_apply_filter_eq(self):
        filtered = apply_filter(self.df, 'dept', 'eq', 'Eng')
        self.assertEqual(len(filtered), 2)

    def test_apply_filter_gt(self):
        filtered = apply_filter(self.df, 'age', 'gt', '30')
        self.assertTrue(all(filtered['age'] > 30))

    def test_apply_filter_bad_column(self):
        filtered = apply_filter(self.df, 'nope', 'eq', 'x')
        self.assertEqual(len(filtered), len(self.df))

    def test_apply_sort_asc(self):
        sorted_df = apply_sort(self.df, 'age', 'asc')
        self.assertEqual(sorted_df.iloc[0]['age'], 25)

    def test_apply_sort_desc(self):
        sorted_df = apply_sort(self.df, 'age', 'desc')
        self.assertEqual(sorted_df.iloc[0]['age'], 100)

    def test_generate_text_insights_with_missing(self):
        df_missing = self.df.copy()
        df_missing.loc[0, 'age'] = None
        stats = {'age': {'missing': 1, 'outliers': {'count': 0}}}
        insights = generate_text_insights(df_missing, stats)
        self.assertTrue(any('missing' in i.lower() for i in insights))


# ══════════════════════════════════════════════════════════════════════════════
# Upload view tests
# ══════════════════════════════════════════════════════════════════════════════

class UploadViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='uploader', password='pass123')

    def test_csv_upload_redirects(self):
        resp = self.client.post('/upload/', {'file': _make_csv_file()})
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/result/', resp.url)

    def test_csv_upload_anonymous(self):
        resp = self.client.post('/upload/', {'file': _make_csv_file()})
        self.assertEqual(resp.status_code, 302)
        obj = UploadedFile.objects.last()
        self.assertIsNone(obj.user)

    def test_csv_upload_authenticated(self):
        self.client.login(username='uploader', password='pass123')
        resp = self.client.post('/upload/', {'file': _make_csv_file()})
        self.assertEqual(resp.status_code, 302)
        obj = UploadedFile.objects.last()
        self.assertEqual(obj.user, self.user)

    def test_json_upload_converted_to_csv(self):
        json_content = '[{"name":"Alice","age":30},{"name":"Bob","age":25}]'
        f = ContentFile(json_content.encode(), name='test.json')
        resp = self.client.post('/upload/', {'file': f})
        self.assertEqual(resp.status_code, 302)
        obj = UploadedFile.objects.last()
        self.assertEqual(obj.file_type, 'csv')

    def test_xlsx_upload_converted(self):
        df = pd.DataFrame({'name': ['Alice', 'Bob'], 'age': [30, 25]})
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            df.to_excel(tmp.name, index=False, engine='openpyxl')
            with open(tmp.name, 'rb') as fh:
                xlsx_content = fh.read()
        os.unlink(tmp.name)
        f = ContentFile(xlsx_content, name='test.xlsx')
        resp = self.client.post('/upload/', {'file': f})
        self.assertEqual(resp.status_code, 302)
        obj = UploadedFile.objects.last()
        self.assertEqual(obj.file_type, 'csv')

    def test_invalid_file_type(self):
        f = ContentFile(b'hello', name='test.txt')
        resp = self.client.post('/upload/', {'file': f})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Unsupported file type')

    def test_empty_file(self):
        f = ContentFile(b'', name='empty.csv')
        resp = self.client.post('/upload/', {'file': f})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'empty')

    def test_invalid_json(self):
        f = ContentFile(b'{bad json}', name='bad.json')
        resp = self.client.post('/upload/', {'file': f})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Error converting')

    def test_get_upload_page(self):
        resp = self.client.get('/upload/')
        self.assertEqual(resp.status_code, 200)


# ══════════════════════════════════════════════════════════════════════════════
# Auth view tests
# ══════════════════════════════════════════════════════════════════════════════

class AuthViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='authuser', password='pass123', email='auth@test.com'
        )

    def test_login_success(self):
        resp = self.client.post('/login/', {'username': 'authuser', 'password': 'pass123'})
        self.assertEqual(resp.status_code, 302)

    def test_login_invalid(self):
        resp = self.client.post('/login/', {'username': 'authuser', 'password': 'wrong'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Invalid')

    def test_logout_post_only(self):
        self.client.login(username='authuser', password='pass123')
        # POST should work
        resp = self.client.post('/logout/')
        self.assertEqual(resp.status_code, 302)

    def test_logout_get_rejected(self):
        self.client.login(username='authuser', password='pass123')
        resp = self.client.get('/logout/')
        self.assertEqual(resp.status_code, 405)

    def test_register_success(self):
        resp = self.client.post('/register/', {
            'username': 'newuser', 'email': 'new@test.com', 'password': 'secure123'
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_register_duplicate_username(self):
        resp = self.client.post('/register/', {
            'username': 'authuser', 'email': 'other@test.com', 'password': 'secure123'
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'already exists')

    def test_register_short_password(self):
        resp = self.client.post('/register/', {
            'username': 'newuser2', 'email': 'n2@test.com', 'password': 'abc'
        })
        self.assertContains(resp, 'at least 6')


# ══════════════════════════════════════════════════════════════════════════════
# Ownership / permission tests
# ══════════════════════════════════════════════════════════════════════════════

class OwnershipTestCase(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='pass')
        self.other = User.objects.create_user(username='other', password='pass')
        self.file_obj = _make_processed_file(user=self.owner)

    def test_owner_can_delete(self):
        self.client.login(username='owner', password='pass')
        url = reverse('delete_file', kwargs={'file_id': self.file_obj.id})
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(UploadedFile.objects.filter(id=self.file_obj.id).exists())

    def test_other_cannot_delete(self):
        self.client.login(username='other', password='pass')
        url = reverse('delete_file', kwargs={'file_id': self.file_obj.id})
        resp = self.client.post(url)
        # Should 404 (ownership mismatch)
        self.assertEqual(resp.status_code, 404)
        self.assertTrue(UploadedFile.objects.filter(id=self.file_obj.id).exists())

    def test_anonymous_delete_redirects_to_login(self):
        url = reverse('delete_file', kwargs={'file_id': self.file_obj.id})
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn('login', resp.url.lower())

    def test_result_view_owner_ok(self):
        self.client.login(username='owner', password='pass')
        url = reverse('result', kwargs={'file_id': self.file_obj.id})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_result_view_other_forbidden(self):
        self.client.login(username='other', password='pass')
        url = reverse('result', kwargs={'file_id': self.file_obj.id})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 403)

    def test_api_results_owner_ok(self):
        self.client.login(username='owner', password='pass')
        url = reverse('api_analysis_results', kwargs={'file_id': self.file_obj.id})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_api_results_other_forbidden(self):
        self.client.login(username='other', password='pass')
        url = reverse('api_analysis_results', kwargs={'file_id': self.file_obj.id})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)


# ══════════════════════════════════════════════════════════════════════════════
# API view tests
# ══════════════════════════════════════════════════════════════════════════════

class APIViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='apiuser', password='pass')
        self.client.login(username='apiuser', password='pass')
        self.file_obj = _make_processed_file(user=self.user)

    def test_api_all_files(self):
        resp = self.client.get('/api/files/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('files', data)
        self.assertEqual(len(data['files']), 1)

    def test_api_analysis_results_structure(self):
        url = reverse('api_analysis_results', kwargs={'file_id': self.file_obj.id})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('file_info', data)
        self.assertIn('analysis_results', data)

    def test_api_requires_login(self):
        self.client.logout()
        resp = self.client.get('/api/files/')
        self.assertEqual(resp.status_code, 302)


# ══════════════════════════════════════════════════════════════════════════════
# My-uploads pagination test
# ══════════════════════════════════════════════════════════════════════════════

class MyUploadsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='upuser', password='pass')
        self.client.login(username='upuser', password='pass')
        # Create 30 processed files
        for _ in range(30):
            UploadedFile.objects.create(
                file=_make_csv_file(),
                file_type='csv',
                user=self.user,
                processed=True,
            )

    def test_my_uploads_renders(self):
        resp = self.client.get('/my_uploads/')
        self.assertEqual(resp.status_code, 200)

    def test_my_uploads_paginated(self):
        resp = self.client.get('/my_uploads/')
        # Default 25 per page — page 1 of 2
        self.assertIn('page_obj', resp.context)

    def test_my_uploads_requires_login(self):
        self.client.logout()
        resp = self.client.get('/my_uploads/')
        self.assertEqual(resp.status_code, 302)


# ══════════════════════════════════════════════════════════════════════════════
# Health check
# ══════════════════════════════════════════════════════════════════════════════

class HealthCheckTestCase(TestCase):
    def test_health_ok(self):
        resp = self.client.get('/health/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b'OK')


# ══════════════════════════════════════════════════════════════════════════════
# Model __str__ tests
# ══════════════════════════════════════════════════════════════════════════════

class ModelStrTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='struser', password='pass')
        self.file_obj = UploadedFile.objects.create(
            file=_make_csv_file(name='sample.csv'),
            file_type='csv',
            user=self.user,
        )

    def test_uploaded_file_str(self):
        s = str(self.file_obj)
        self.assertIn('UploadedFile', s)

    def test_processed_data_str(self):
        pd_obj = ProcessedData.objects.create(
            uploaded_file=self.file_obj,
            column_name='age',
            data_type='numeric',
            value=30.0,
            stats={},
        )
        s = str(pd_obj)
        self.assertIn('age', s)
