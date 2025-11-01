# Templates Explanation

Let's examine the template structure in `analytics_app/templates/`:

## Base Template (base.html)
```html
{% load static %}
<!DOCTYPE html>
<html>
<head>
    <title>{% block title %}Analytics Website{% endblock %}</title>
    <!-- CSS and JS includes -->
    <link rel="stylesheet" href="{% static 'analytics_app/css/base.css' %}">
    <link rel="stylesheet" href="{% static 'analytics_app/css/components.css' %}">
</head>
<body>
    <!-- Navigation -->
    <nav>
        <a href="{% url 'index' %}">Home</a>
        <a href="{% url 'upload' %}">Upload</a>
        {% if user.is_authenticated %}
            <a href="{% url 'my_uploads' %}">My Uploads</a>
            <a href="{% url 'logout' %}">Logout</a>
        {% else %}
            <a href="{% url 'login' %}">Login</a>
        {% endif %}
    </nav>

    <!-- Main Content -->
    <main>
        {% block content %}
        {% endblock %}
    </main>
</body>
</html>
```

## Upload Form (upload.html)
```html
{% extends 'analytics_app/base.html' %}

{% block content %}
<div class="upload-section">
    <h2>Upload File</h2>
    
    {% if error %}
        <div class="alert alert-danger">{{ error }}</div>
    {% endif %}
    
    <form method="post" enctype="multipart/form-data">
        {% csrf_token %}
        <input type="file" name="file" accept=".csv,.json,.sql">
        <button type="submit">Upload</button>
    </form>
</div>
{% endblock %}
```

## Results Display (result.html)
```html
{% extends 'analytics_app/base.html' %}

{% block content %}
<div class="results-section">
    <h2>Processing Results</h2>
    
    {% if file.processed %}
        {% for result in results %}
            <div class="result-card">
                <h3>{{ result.column_name }}</h3>
                <ul>
                    <li>Mean: {{ result.stats.mean }}</li>
                    <li>Median: {{ result.stats.median }}</li>
                    <li>Standard Deviation: {{ result.stats.std }}</li>
                </ul>
            </div>
        {% endfor %}
    {% else %}
        <div class="processing-status">
            Processing... Please wait.
        </div>
    {% endif %}
</div>
{% endblock %}
```

## Template Features Explained

### 1. Template Inheritance
- Base template defines layout
- Child templates extend base
- Block system for content areas

### 2. Static Files
- CSS organization
- JavaScript includes
- Asset management

### 3. Dynamic Content
- User status checks
- Error messages
- Processing status
- Results display

### 4. Forms
- File upload handling
- CSRF protection
- Validation feedback

### 5. Navigation
- Conditional links
- User authentication
- Current page highlight

## CSS Organization

1. Base Styles (base.css)
```css
/* Layout and typography */
body {
    font-family: Arial, sans-serif;
    line-height: 1.6;
    margin: 0;
    padding: 0;
}

/* Navigation */
nav {
    background: #333;
    padding: 1rem;
}

/* Container layouts */
.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 1rem;
}
```

2. Components (components.css)
```css
/* Cards and modules */
.result-card {
    background: #fff;
    border-radius: 8px;
    padding: 1rem;
    margin: 1rem 0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* Forms and inputs */
.upload-section form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

/* Alert messages */
.alert {
    padding: 1rem;
    border-radius: 4px;
    margin: 1rem 0;
}
```

## JavaScript Integration

1. File Upload
```javascript
// Handle file selection
const uploadInput = document.querySelector('input[type="file"]');
uploadInput.addEventListener('change', () => {
    const fileName = uploadInput.files[0]?.name;
    if(fileName) {
        // Update UI with selected file
    }
});
```

2. Results Page
```javascript
// Auto-refresh for processing status
if(!document.querySelector('.results-data')) {
    setTimeout(() => {
        location.reload();
    }, 5000);
}
```