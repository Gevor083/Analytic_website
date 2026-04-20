// JS ֆայլ՝ հիմնական դինամիկ համարները

document.addEventListener('DOMContentLoaded', () => {
    console.log('Analytics website loaded');

    // Theme toggling logic
    const themeToggleBtn = document.getElementById('themeToggle');
    const themeIcon = themeToggleBtn ? themeToggleBtn.querySelector('i') : null;

    if (themeToggleBtn) {
        // Initial setup based on what's rendered by the backend to body class
        const initialIsDark = document.body.classList.contains('dark-mode');
        if (themeIcon) {
            themeIcon.classList.replace('fa-moon', initialIsDark ? 'fa-sun' : 'fa-moon');
            themeIcon.classList.replace('fa-sun', initialIsDark ? 'fa-sun' : 'fa-moon'); // ensure Fallback 
        }

        themeToggleBtn.addEventListener('click', () => {
            document.body.classList.toggle('dark-mode');
            const isDark = document.body.classList.contains('dark-mode');
            const selectedTheme = isDark ? 'dark' : 'light';
            localStorage.setItem('theme', selectedTheme);

            if (themeIcon) {
                if (isDark) {
                    themeIcon.classList.replace('fa-moon', 'fa-sun');
                } else {
                    themeIcon.classList.replace('fa-sun', 'fa-moon');
                }
            }

            // Sync with backend
            fetch('/set_theme/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ theme: selectedTheme })
            }).then(response => response.json())
              .catch(err => console.error('Error setting theme:', err));
        });
    }

    // CSRF token helper for fetch
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Navbar hover effect enhancement (optional)
    const navLinks = document.querySelectorAll('header nav ul.main-nav li a');

    navLinks.forEach(link => {
        link.addEventListener('mouseenter', () => {
            link.style.transform = 'scale(1.05)';
            link.style.transition = 'transform 0.2s';
        });
        link.addEventListener('mouseleave', () => {
            link.style.transform = 'scale(1)';
        });
    });

    // Smooth scroll for anchor links (if any)
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const target = document.querySelector(link.getAttribute('href'));
            if(target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });

    // File input alert on upload page (optional)
    const uploadInput = document.querySelector('input[type="file"]');
    if(uploadInput) {
        uploadInput.addEventListener('change', () => {
            const fileName = uploadInput.files[0]?.name;
            if(fileName) {
                alert(`Selected file: ${fileName}`);
            }
        });
    }

    // Loader animation for upload form (exclude login/ajax forms and logout)
    const forms = document.querySelectorAll('form[method="post"]:not(#login-form):not(#face-login-form):not([action*="logout"])');
    forms.forEach(form => {
        form.addEventListener('submit', (e) => {
            // Show loading overlay
            showLoadingOverlay('');

            // Disable form submission to prevent multiple submits
            const submitBtn = form.querySelector('button[type="submit"]');
            if(submitBtn) {
                // Ignore if it's the logout button
                if (submitBtn.innerText.trim() !== 'Logout') {
                    submitBtn.disabled = true;
                    submitBtn.innerHTML = ' Processing...';
                }
            }
        });
    });

    // Loader for chart generation
    const generateChartBtn = document.getElementById('generateChartBtn');
    if(generateChartBtn) {
        generateChartBtn.addEventListener('click', () => {
            showLoadingOverlay('Generating chart...');
        });
    }
});

function showLoadingOverlay(message) {
    // Remove existing overlay if any
    const existingOverlay = document.querySelector('.loading-overlay');
    if(existingOverlay) {
        existingOverlay.remove();
    }

    // Create overlay
    const overlay = document.createElement('div');
    overlay.className = 'loading-overlay';
    overlay.innerHTML = `
        <div style="text-align: center;">
            <div class="loader"></div>
            <div class="loading-text">${message}</div>
        </div>
    `;

    document.body.appendChild(overlay);
}

function hideLoadingOverlay() {
    const overlay = document.querySelector('.loading-overlay');
    if(overlay) {
        overlay.remove();
    }
}
