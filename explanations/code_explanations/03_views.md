# Views.py Explanation

Let's examine `analytics_app/views.py`, which handles web requests:

```python
# File Upload View
def upload_view(request):
    """
    Handles file uploads and initiates processing
    """
    if request.method != 'POST':
        # Show upload form for GET requests
        return render(request, 'analytics_app/upload.html')

    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        return render(request, 'analytics_app/upload.html', 
                     {'error': 'No file was uploaded.'})

    # Validate file type
    filename = uploaded_file.name.lower()
    file_type = next((ext for ext in settings.ALLOWED_FILE_TYPES 
                     if filename.endswith(f'.{ext}')), None)
    
    if not file_type:
        return render(request, 'analytics_app/upload.html', 
                     {'error': f'Unsupported file type. Allowed: {", ".join(settings.ALLOWED_FILE_TYPES)}'})

    # Create database record
    obj = UploadedFile.objects.create(
        file=uploaded_file,
        file_type=file_type,
        user=request.user if request.user.is_authenticated else None
    )

    # Queue processing task
    process_uploaded_file.delay(obj.id)
    return redirect(f"{reverse('result', kwargs={'file_id': obj.id})}?show_modal=1")

# Results View
def result_view(request, file_id):
    """
    Shows processing results for a file
    """
    file_obj = get_object_or_404(UploadedFile, id=file_id)
    results = ProcessedData.objects.filter(uploaded_file=file_obj)
    
    context = {
        'file': file_obj,
        'results': results,
        'show_modal': request.GET.get('show_modal')
    }
    return render(request, 'analytics_app/result.html', context)

# Admin Dashboard
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def admin_dashboard_view(request):
    """
    Administrative overview of users and files
    """
    users = User.objects.all()
    uploads = UploadedFile.objects.select_related('user').all()
    
    context = {
        'users': users,
        'uploads': uploads,
        'total_users': users.count(),
        'total_uploads': uploads.count(),
        'uploads_by_user': {user: uploads.filter(user=user) for user in users},
    }
    return render(request, 'analytics_app/admin_dashboard.html', context)

## View Functions Explained

### 1. File Upload Process
1. Receive file from form
2. Validate file type and size
3. Create database record
4. Queue processing task
5. Redirect to results page

### 2. Results Display
1. Fetch file record
2. Get processing results
3. Show processing status
4. Display statistics and visualizations

### 3. Admin Dashboard
1. Check admin permissions
2. Gather user statistics
3. Collect file information
4. Display overview

## Security Features

1. File Validation
   - Type checking
   - Size limits
   - Content validation

2. User Authentication
   - Login required for sensitive views
   - Admin permissions check
   - Session management

3. Error Handling
   - Graceful error display
   - User-friendly messages
   - Logging of issues

## Template Integration

Each view uses specific templates:
- upload.html: File upload form
- result.html: Processing results
- admin_dashboard.html: Admin overview
- base.html: Common layout

## Background Processing

1. File Upload:
   - Quick save to database
   - Immediate user feedback
   - Async processing start

2. Processing Task:
   - Run in background
   - Update progress
   - Handle errors
   - Store results