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
});
