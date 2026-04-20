"""
Authentication views: login, logout, register, face-login, theme switching.
"""

import logging

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.conf import settings
import json

logger = logging.getLogger(__name__)


def login_view(request):
    """Handle username/password login."""
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
        logger.warning("Failed login attempt for username: %s", username)
        return render(request, 'analytics_app/login.html', {'error': 'Invalid username or password.'})
    return render(request, 'analytics_app/login.html')


@require_POST
def logout_view(request):
    """Log the user out (POST only to prevent CSRF logout attacks)."""
    logout(request)
    return redirect('login')


def register_view(request):
    """Handle new user registration."""
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email    = request.POST.get('email',    '').strip()
        password = request.POST.get('password', '').strip()
        errors = []
        if not username:
            errors.append('Username is required.')
        if not email:
            errors.append('Email is required.')
        if not password:
            errors.append('Password is required.')
        if password and len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if username and User.objects.filter(username=username).exists():
            errors.append('Username already exists.')
        if email and User.objects.filter(email=email).exists():
            errors.append('Email already registered.')
        if errors:
            return render(request, 'analytics_app/register.html', {'error': ' '.join(errors)})
        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            login(request, user)
            messages.success(request, f'Welcome, {username}! Your account has been created.')
            return redirect('home')
        except Exception as e:
            return render(request, 'analytics_app/register.html', {'error': f'Error: {str(e)}'})
    return render(request, 'analytics_app/register.html')


def face_login_view(request):
    """Face-recognition login for admin/staff users."""
    if request.method == 'POST':
        try:
            import face_recognition
            import cv2
            import numpy as np
            import base64
            import os
        except ImportError as e:
            logger.error("Face recognition dependencies not installed: %s", e)
            return render(request, 'analytics_app/face_login.html',
                          {'error': 'Face recognition is not available on this server.'})

        image_data = request.POST.get('image')
        if not image_data:
            return render(request, 'analytics_app/face_login.html', {'error': 'No image data received.'})

        try:
            _, encoded = image_data.split(',', 1)
            image_bytes = base64.b64decode(encoded)
            np_arr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        except Exception as e:
            logger.error("Error decoding face image: %s", e)
            return render(request, 'analytics_app/face_login.html', {'error': 'Invalid image data.'})

        face_locations = face_recognition.face_locations(img)
        if not face_locations:
            return render(request, 'analytics_app/face_login.html', {'error': 'No face detected in the image.'})

        face_encoding = face_recognition.face_encodings(img, face_locations)[0]

        faces_dir = os.path.join(settings.BASE_DIR, 'faces')
        known_encodings, known_usernames = [], []

        if os.path.exists(faces_dir):
            for filename in os.listdir(faces_dir):
                if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    username = os.path.splitext(filename)[0]
                    image_path = os.path.join(faces_dir, filename)
                    try:
                        known_image = face_recognition.load_image_file(image_path)
                        locs = face_recognition.face_locations(known_image)
                        if locs:
                            enc = face_recognition.face_encodings(known_image, locs)[0]
                            known_encodings.append(enc)
                            known_usernames.append(username)
                    except Exception as e:
                        logger.error("Error loading face image %s: %s", filename, e)

        matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.6)
        distances = face_recognition.face_distance(known_encodings, face_encoding)

        if True in matches:
            best_idx = np.argmin(distances)
            matched_username = known_usernames[best_idx]
            try:
                user = User.objects.get(username=matched_username, is_staff=True)
                login(request, user)
                return redirect('/admin/')
            except User.DoesNotExist:
                return render(request, 'analytics_app/face_login.html',
                              {'error': 'Matched user is not an admin.'})
        return render(request, 'analytics_app/face_login.html', {'error': 'Face not recognized.'})

    return render(request, 'analytics_app/face_login.html')


@require_POST
def set_theme(request):
    """Persist the user's light/dark theme preference in the session."""
    try:
        data = json.loads(request.body)
        theme = data.get('theme', 'light')
        if theme in ['light', 'dark']:
            request.session['theme'] = theme
            return JsonResponse({'status': 'ok', 'theme': theme})
        return JsonResponse({'status': 'error', 'message': 'Invalid theme'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
