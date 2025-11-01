# Static Files and CSS

Let's examine the static files structure and styling:

## CSS Organization

### Base Styles (base.css)
```css
/* Reset and base styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Arial', sans-serif;
    line-height: 1.6;
    background: #f5f5f5;
    color: #333;
}

/* Layout */
.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 1rem;
}

/* Navigation */
nav {
    background: #0C4B8E;
    padding: 1rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

nav a {
    color: white;
    text-decoration: none;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    transition: background 0.3s;
}

nav a:hover {
    background: rgba(255,255,255,0.1);
}
```

### Components (components.css)
```css
/* Cards */
.card {
    background: white;
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* Buttons */
.btn {
    display: inline-block;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    border: none;
    cursor: pointer;
    font-weight: 500;
    transition: all 0.3s;
}

.btn-primary {
    background: #0C4B8E;
    color: white;
}

.btn-primary:hover {
    background: #0A3D7A;
}

/* Forms */
.form-group {
    margin-bottom: 1rem;
}

.form-control {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid #ddd;
    border-radius: 4px;
}

/* Alerts */
.alert {
    padding: 1rem;
    border-radius: 4px;
    margin-bottom: 1rem;
}

.alert-danger {
    background: #fee;
    color: #c33;
    border: 1px solid #fcc;
}

.alert-success {
    background: #efe;
    color: #3c3;
    border: 1px solid #cfc;
}
```

### Layout (layout.css)
```css
/* Grid system */
.row {
    display: flex;
    flex-wrap: wrap;
    margin: -0.5rem;
}

.col {
    flex: 1;
    padding: 0.5rem;
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .col {
        flex: 0 0 100%;
    }
}

/* Utilities */
.text-center { text-align: center; }
.text-right { text-align: right; }
.mb-1 { margin-bottom: 0.5rem; }
.mb-2 { margin-bottom: 1rem; }
.mb-3 { margin-bottom: 1.5rem; }
```

## Static File Organization

```
static/
├── analytics_app/
│   ├── css/
│   │   ├── base.css
│   │   ├── components.css
│   │   └── layout.css
│   ├── js/
│   │   └── scripts.js
│   └── images/
│       └── (project images)
```

## JavaScript Features (scripts.js)

```javascript
// Document ready handler
document.addEventListener('DOMContentLoaded', function() {
    // File upload handling
    const fileInput = document.querySelector('input[type="file"]');
    if(fileInput) {
        fileInput.addEventListener('change', function() {
            const fileName = this.files[0]?.name;
            if(fileName) {
                // Show selected filename
                const label = this.nextElementSibling;
                if(label) {
                    label.textContent = fileName;
                }
            }
        });
    }

    // Processing status updates
    const processingStatus = document.querySelector('.processing-status');
    if(processingStatus) {
        // Auto-refresh for processing status
        setInterval(() => {
            location.reload();
        }, 5000);
    }

    // Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const fileInput = this.querySelector('input[type="file"]');
            if(fileInput && fileInput.files.length === 0) {
                e.preventDefault();
                alert('Please select a file to upload.');
            }
        });
    });

    // Interactive features
    document.querySelectorAll('[data-toggle="tooltip"]').forEach(el => {
        // Initialize tooltips
        new bootstrap.Tooltip(el);
    });
});
```

## Style Features

1. **Responsive Design**
   - Mobile-first approach
   - Flexible grids
   - Media queries

2. **Component System**
   - Reusable patterns
   - Consistent styling
   - Easy maintenance

3. **Utilities**
   - Helper classes
   - Common adjustments
   - Quick formatting

4. **Theme Elements**
   - Color scheme
   - Typography
   - Spacing system

## CSS Best Practices

1. **Organization**
   - Modular structure
   - Clear naming
   - Logical grouping

2. **Performance**
   - Minimal selectors
   - Efficient rules
   - Optimized loading

3. **Maintainability**
   - Comments
   - Variables
   - Consistent formatting