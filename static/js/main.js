/**
 * Main JavaScript file for the Blockchain Data Marketplace Mockup
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    initTooltips();

    // Initialize scroll effects
    initScrollEffects();

    // Set active navigation
    setActiveNavigation();

    // Mobile menu adjustments
    adjustMobileMenu();

    // Initialize blockchain explorer effects if on that page
    if (document.querySelector('.blockchain-explorer')) {
        initBlockchainExplorer();
    }

    // Initialize data display features if on marketplace page
    if (document.querySelector('.marketplace-container')) {
        initMarketplace();
    }

    // Custom file input handling for dataset uploads
    initCustomFileInput();
});

/**
 * Initialize Bootstrap tooltips
 */
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            trigger: 'hover'
        });
    });
}

/**
 * Add subtle scroll effects
 */
function initScrollEffects() {
    // Add shadow to navbar on scroll
    window.addEventListener('scroll', function() {
        const navbar = document.getElementById('mainNav');
        if (navbar) {
            if (window.scrollY > 10) {
                navbar.classList.add('navbar-scrolled');
            } else {
                navbar.classList.remove('navbar-scrolled');
            }
        }

        // Reveal elements on scroll
        const revealElements = document.querySelectorAll('.reveal-on-scroll');
        revealElements.forEach(element => {
            const elementTop = element.getBoundingClientRect().top;
            const windowHeight = window.innerHeight;

            if (elementTop < windowHeight - 100) {
                element.classList.add('revealed');
            }
        });
    });
}

/**
 * Set active navigation based on current URL
 */
function setActiveNavigation() {
    const currentPath = window.location.pathname;

    // Remove all active classes first
    document.querySelectorAll('.navbar .nav-link').forEach(link => {
        link.classList.remove('active');
    });

    // Set active class based on path
    let activeLink = null;

    if (currentPath === '/') {
        activeLink = document.getElementById('nav-home');
    } else if (currentPath.startsWith('/marketplace')) {
        activeLink = document.getElementById('nav-marketplace');
    } else if (currentPath.startsWith('/blockchain')) {
        activeLink = document.getElementById('nav-blockchain');
    } else if (currentPath.startsWith('/training')) {
        activeLink = document.getElementById('nav-training');
    } else if (currentPath.startsWith('/admin')) {
        activeLink = document.getElementById('nav-admin');
    } else if (currentPath.startsWith('/upload')) {
        activeLink = document.querySelector('.nav-link[href="/upload-dataset"]');
    }

    if (activeLink) {
        activeLink.classList.add('active');
    }
}

/**
 * Adjust mobile menu behavior
 */
function adjustMobileMenu() {
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');

    if (navbarToggler && navbarCollapse) {
        // Close mobile menu when clicking outside
        document.addEventListener('click', function(event) {
            const isClickInside = navbarToggler.contains(event.target) || navbarCollapse.contains(event.target);

            if (!isClickInside && navbarCollapse.classList.contains('show')) {
                navbarToggler.click();
            }
        });

        // Close mobile menu when clicking on a nav link
        const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                if (navbarCollapse.classList.contains('show')) {
                    navbarToggler.click();
                }
            });
        });
    }
}

/**
 * Initialize blockchain explorer page features
 */
function initBlockchainExplorer() {
    // Toggle transaction details
    const transactionToggles = document.querySelectorAll('.transaction-toggle');
    transactionToggles.forEach(toggle => {
        toggle.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            const targetElement = document.getElementById(targetId);

            if (targetElement) {
                if (targetElement.classList.contains('d-none')) {
                    targetElement.classList.remove('d-none');
                    this.innerHTML = '<i class="bi bi-dash-circle"></i> Hide Details';
                } else {
                    targetElement.classList.add('d-none');
                    this.innerHTML = '<i class="bi bi-plus-circle"></i> Show Details';
                }
            }
        });
    });

    // Highlight blocks when selected in the chain visualization
    const blockElements = document.querySelectorAll('.block-element');
    blockElements.forEach(block => {
        block.addEventListener('click', function() {
            // Remove highlight from all blocks
            blockElements.forEach(b => b.classList.remove('block-selected'));

            // Add highlight to clicked block
            this.classList.add('block-selected');

            // Scroll to block details
            const blockId = this.getAttribute('data-block-id');
            const detailElement = document.getElementById('block-detail-' + blockId);

            if (detailElement) {
                detailElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
                detailElement.classList.add('highlight-detail');

                // Remove highlight after animation
                setTimeout(() => {
                    detailElement.classList.remove('highlight-detail');
                }, 2000);
            }
        });
    });
}

/**
 * Initialize marketplace page features
 */
function initMarketplace() {
    // Filter functionality
    const filterButtons = document.querySelectorAll('.filter-btn');
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            const filterValue = this.getAttribute('data-filter');

            // Remove active class from all buttons
            filterButtons.forEach(btn => btn.classList.remove('active'));

            // Add active class to clicked button
            this.classList.add('active');

            // Filter items
            const items = document.querySelectorAll('.marketplace-item');
            items.forEach(item => {
                if (filterValue === 'all') {
                    item.style.display = 'block';
                } else {
                    if (item.classList.contains(filterValue)) {
                        item.style.display = 'block';
                    } else {
                        item.style.display = 'none';
                    }
                }
            });
        });
    });

    // Search functionality
    const searchInput = document.getElementById('marketplace-search');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchQuery = this.value.toLowerCase();

            const items = document.querySelectorAll('.marketplace-item');
            items.forEach(item => {
                const itemName = item.querySelector('.item-name').textContent.toLowerCase();
                const itemDescription = item.querySelector('.item-description').textContent.toLowerCase();

                if (itemName.includes(searchQuery) || itemDescription.includes(searchQuery)) {
                    item.style.display = 'block';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    }

    // Sort functionality
    const sortSelect = document.getElementById('sort-select');
    if (sortSelect) {
        sortSelect.addEventListener('change', function() {
            const sortValue = this.value;
            const itemsContainer = document.querySelector('.marketplace-items');
            const items = Array.from(document.querySelectorAll('.marketplace-item'));

            items.sort((a, b) => {
                if (sortValue === 'price-low') {
                    const priceA = parseFloat(a.getAttribute('data-price'));
                    const priceB = parseFloat(b.getAttribute('data-price'));
                    return priceA - priceB;
                } else if (sortValue === 'price-high') {
                    const priceA = parseFloat(a.getAttribute('data-price'));
                    const priceB = parseFloat(b.getAttribute('data-price'));
                    return priceB - priceA;
                } else if (sortValue === 'date-new') {
                    const dateA = new Date(a.getAttribute('data-timestamp'));
                    const dateB = new Date(b.getAttribute('data-timestamp'));
                    return dateB - dateA;
                } else if (sortValue === 'date-old') {
                    const dateA = new Date(a.getAttribute('data-timestamp'));
                    const dateB = new Date(b.getAttribute('data-timestamp'));
                    return dateA - dateB;
                }
                return 0;
            });

            // Reorder items in DOM
            items.forEach(item => {
                itemsContainer.appendChild(item);
            });
        });
    }
}

/**
 * Initialize custom file input for dataset uploads
 */
function initCustomFileInput() {
    const fileInputs = document.querySelectorAll('.custom-file-input');
    fileInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const fileName = e.target.files[0]?.name || 'No file selected';
            const fileLabel = this.nextElementSibling;

            if (fileLabel) {
                fileLabel.textContent = fileName;
            }

            // Show preview for images if applicable
            const previewElement = document.getElementById(this.getAttribute('data-preview'));
            if (previewElement && e.target.files[0]) {
                const file = e.target.files[0];

                if (file.type.startsWith('image/')) {
                    const reader = new FileReader();

                    reader.onload = function(e) {
                        previewElement.style.backgroundImage = `url(${e.target.result})`;
                        previewElement.classList.add('has-preview');
                    };

                    reader.readAsDataURL(file);
                } else {
                    // Show file type icon for non-images
                    previewElement.style.backgroundImage = 'none';
                    previewElement.classList.add('has-preview', 'file-icon');

                    if (file.type.includes('csv') || file.name.endsWith('.csv')) {
                        previewElement.setAttribute('data-file-type', 'csv');
                    } else if (file.type.includes('json') || file.name.endsWith('.json')) {
                        previewElement.setAttribute('data-file-type', 'json');
                    } else if (file.type.includes('excel') || file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
                        previewElement.setAttribute('data-file-type', 'excel');
                    } else {
                        previewElement.setAttribute('data-file-type', 'generic');
                    }
                }
            }
        });
    });
}

/**
 * Toggle password visibility
 * @param {string} inputId - The ID of the password input
 * @param {string} toggleId - The ID of the toggle button
 */
function togglePasswordVisibility(inputId, toggleId) {
    const passwordInput = document.getElementById(inputId);
    const toggleButton = document.getElementById(toggleId);

    if (passwordInput && toggleButton) {
        if (passwordInput.type === 'password') {
            passwordInput.type = 'text';
            toggleButton.innerHTML = '<i class="bi bi-eye-slash"></i>';
        } else {
            passwordInput.type = 'password';
            toggleButton.innerHTML = '<i class="bi bi-eye"></i>';
        }
    }
}

/**
 * Copy text to clipboard
 * @param {string} text - The text to copy
 * @param {HTMLElement} button - The button element that was clicked
 */
function copyToClipboard(text, button) {
    navigator.clipboard.writeText(text).then(function() {
        const originalText = button.innerHTML;
        button.innerHTML = '<i class="bi bi-check-circle"></i> Copied!';
        button.classList.add('copied');

        setTimeout(() => {
            button.innerHTML = originalText;
            button.classList.remove('copied');
        }, 2000);
    }).catch(function(err) {
        console.error('Could not copy text: ', err);
    });
}

/**
 * Show or hide a loading spinner
 * @param {string} elementId - The ID of the container element
 * @param {boolean} show - Whether to show or hide the spinner
 */
function toggleLoadingSpinner(elementId, show) {
    const container = document.getElementById(elementId);

    if (container) {
        if (show) {
            container.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';
        } else {
            container.innerHTML = '';
        }
    }
}

/**
 * Format blockchain address for display
 * @param {string} address - The full blockchain address
 * @param {number} startChars - Number of characters to show at start
 * @param {number} endChars - Number of characters to show at end
 * @returns {string} Formatted address
 */
function formatAddress(address, startChars = 6, endChars = 4) {
    if (!address || address.length <= startChars + endChars) {
        return address;
    }

    return `${address.substring(0, startChars)}...${address.substring(address.length - endChars)}`;
}