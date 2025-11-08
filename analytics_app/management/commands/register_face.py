from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.conf import settings
import os
import face_recognition
import cv2
import numpy as np

class Command(BaseCommand):
    help = 'Register a face for an admin user'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username of the admin user')

    def handle(self, *args, **options):
        username = options['username']

        # Check if user exists and is staff
        try:
            user = User.objects.get(username=username)
            if not user.is_staff:
                raise CommandError(f'User {username} is not a staff member.')
        except User.DoesNotExist:
            raise CommandError(f'User {username} does not exist.')

        # Create faces directory if it doesn't exist
        faces_dir = os.path.join(settings.BASE_DIR, 'faces')
        os.makedirs(faces_dir, exist_ok=True)

        # Path for the face image
        face_path = os.path.join(faces_dir, f'{username}.jpg')

        # Capture face from webcam
        self.stdout.write(f'Capturing face for user {username}...')
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            raise CommandError('Could not open webcam.')

        face_captured = False
        while not face_captured:
            ret, frame = cap.read()
            if not ret:
                continue

            # Convert to RGB for face_recognition
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Detect faces
            face_locations = face_recognition.face_locations(rgb_frame)

            if face_locations:
                # Take the first face found
                top, right, bottom, left = face_locations[0]

                # Extract face
                face_image = rgb_frame[top:bottom, left:right]

                # Save the face image
                cv2.imwrite(face_path, cv2.cvtColor(face_image, cv2.COLOR_RGB2BGR))
                face_captured = True
                self.stdout.write(self.style.SUCCESS(f'Face captured and saved for user {username} at {face_path}'))
            else:
                self.stdout.write('No face detected. Please position yourself in front of the camera.')

            # Display the frame
            cv2.imshow('Capture Face', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

        if not face_captured:
            raise CommandError('Face capture was cancelled or failed.')
