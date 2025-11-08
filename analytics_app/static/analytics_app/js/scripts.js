// JS ֆայլ՝ հիմնական դինամիկ համարները

document.addEventListener('DOMContentLoaded', () => {
    console.log('Analytics website loaded');

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

    // Loader animation for upload form
    const uploadForm = document.querySelector('form[method="post"]');
    if(uploadForm) {
        uploadForm.addEventListener('submit', (e) => {
            // Show loading overlay
            // showLoadingOverlay('');

            // Disable form submission to prevent multiple submits
            const submitBtn = uploadForm.querySelector('button[type="submit"]');
            if(submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="loader"></span> Uploading...';
            }
        });
    }

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
