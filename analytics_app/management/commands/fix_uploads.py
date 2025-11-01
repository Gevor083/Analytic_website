from django.core.management.base import BaseCommand
from django.conf import settings
from analytics_app.models import UploadedFile
import os
import shutil

class Command(BaseCommand):
    help = 'Move uploaded files from MEDIA_ROOT/uploads/ to MEDIA_ROOT (root uploads/) and update DB paths. Avoid overwriting existing files.'

    def _unique_dest(self, dest_path):
        # If dest_path exists, append _1, _2 etc before the file extension
        if not os.path.exists(dest_path):
            return dest_path
        base, ext = os.path.splitext(dest_path)
        counter = 1
        new_dest = f"{base}_{counter}{ext}"
        while os.path.exists(new_dest):
            counter += 1
            new_dest = f"{base}_{counter}{ext}"
        return new_dest

    def handle(self, *args, **options):
        media_root = settings.MEDIA_ROOT
        moved = 0
        skipped = 0
        errors = 0

        self.stdout.write(f"MEDIA_ROOT: {media_root}")
        for uf in UploadedFile.objects.all():
            try:
                name = uf.file.name  # relative storage path
                if not name:
                    skipped += 1
                    continue
                # normalize
                norm = name.replace('\\', '/')
                # If already at root (no directory) skip
                if '/' not in norm:
                    skipped += 1
                    continue
                # We want to move any files located in subfolders into MEDIA_ROOT root
                parts = norm.split('/')
                filename = parts[-1]
                new_rel = filename

                src = os.path.join(media_root, *norm.split('/'))
                dest = os.path.join(media_root, new_rel)

                if not os.path.exists(src):
                    self.stdout.write(self.style.WARNING(f"Source not found for UploadedFile id={uf.id}: {src} (skipping)"))
                    errors += 1
                    continue

                # Ensure unique destination (avoid overwriting)
                unique_dest = self._unique_dest(dest)
                dest_dir = os.path.dirname(unique_dest)
                os.makedirs(dest_dir or media_root, exist_ok=True)

                # Move file
                shutil.move(src, unique_dest)

                # Update DB file field to new relative path (use forward slashes)
                rel_path = os.path.relpath(unique_dest, media_root).replace('\\', '/')
                uf.file.name = rel_path
                uf.save(update_fields=['file'])
                moved += 1
                self.stdout.write(self.style.SUCCESS(f"Moved {src} -> {unique_dest} (id={uf.id})"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing UploadedFile id={uf.id}: {e}"))
                errors += 1

        self.stdout.write(self.style.SUCCESS(f"Completed: moved={moved}, skipped={skipped}, errors={errors}"))
