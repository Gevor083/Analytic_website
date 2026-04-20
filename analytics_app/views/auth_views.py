"""
Authentication views: login, logout, register, admin face verification, theme switching.
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
    """Handle username/password login.
    Regular users: log in immediately.
    Admin/staff users: store pending session, require face verification popup.
    """
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_staff or user.is_superuser:
                # Store pending admin id — face verification required before login
                request.session['pending_admin_id'] = user.id
                if is_ajax:
                    return JsonResponse({'status': 'face_required'})
                # Non-AJAX fallback (should not happen with our JS form)
                return render(request, 'analytics_app/login.html', {'face_required': True})
            else:
                login(request, user)
                next_url = request.GET.get('next', 'home')
                if is_ajax:
                    from django.urls import reverse
                    return JsonResponse({'status': 'ok', 'redirect': reverse(next_url) if '/' not in next_url else next_url})
                return redirect(next_url)

        logger.warning("Failed login attempt for username: %s", username)
        if is_ajax:
            return JsonResponse({'status': 'error', 'message': 'Invalid username or password.'}, status=401)
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


def admin_face_verify_view(request):
    """
    AJAX endpoint — verify face for a pending admin login.
    Called after successful username/password auth for staff users.
    Returns JSON: {"status": "ok", "redirect": "..."} or {"status": "error", "message": "..."}
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed.'}, status=405)

    pending_id = request.session.get('pending_admin_id')
    if not pending_id:
        return JsonResponse(
            {'status': 'error', 'message': 'Session expired. Please log in again.'},
            status=400
        )

    try:
        import face_recognition
        import cv2
        import numpy as np
        import base64
        import os
    except ImportError as e:
        logger.error("Face recognition dependencies not installed: %s", e)
        return JsonResponse(
            {'status': 'error', 'message': 'Face recognition is not available on this server.'},
            status=500
        )

    image_data = request.POST.get('image')
    if not image_data:
        return JsonResponse({'status': 'error', 'message': 'No image data received.'}, status=400)

    try:
        _, encoded = image_data.split(',', 1)
        image_bytes = base64.b64decode(encoded)
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    except Exception as e:
        logger.error("Error decoding face image: %s", e)
        return JsonResponse({'status': 'error', 'message': 'Invalid image data.'}, status=400)

    face_locations = face_recognition.face_locations(img)
    if not face_locations:
        return JsonResponse({'status': 'error', 'message': 'No face detected. Please try again.'}, status=400)

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

    if not known_encodings:
        return JsonResponse(
            {'status': 'error', 'message': 'No admin face profiles configured. Contact system administrator.'},
            status=400
        )

    matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.6)
    distances = face_recognition.face_distance(known_encodings, face_encoding)

    if True in matches:
        best_idx = int(np.argmin(distances))
        try:
            user = User.objects.get(id=pending_id, is_staff=True)
            del request.session['pending_admin_id']
            login(request, user)
            logger.info("Admin face login successful for user id=%s", pending_id)
            return JsonResponse({'status': 'ok', 'redirect': '/moderator_dashboard/'})
        except User.DoesNotExist:
            request.session.pop('pending_admin_id', None)
            return JsonResponse({'status': 'error', 'message': 'Admin user not found.'}, status=400)

    logger.warning("Admin face login failed for pending user id=%s", pending_id)
    return JsonResponse({'status': 'error', 'message': 'Face not recognized. Access denied.'}, status=401)


def face_login_view(request):
    """Legacy face login page — redirect to main login (face auth is now a popup)."""
    return redirect('login')


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
