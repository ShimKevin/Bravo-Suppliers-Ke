// static/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Mobile menu toggle
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const mobileMenu = document.getElementById('mobileMenu');
    
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', function() {
            mobileMenu.classList.toggle('show');
        });
    }

    // Initialize cart count from session storage
    const cartCount = sessionStorage.getItem('cart_count');
    if (cartCount) {
        document.querySelectorAll('.cart-count').forEach(el => {
            el.textContent = cartCount;
        });
    }

    // Cart quantity controls
    document.querySelectorAll('.cart-quantity-btn').forEach(button => {
        button.addEventListener('click', function() {
            const form = this.closest('form');
            const input = form.querySelector('.cart-quantity');
            let quantity = parseInt(input.value);
            
            if (this.classList.contains('minus')) {
                if (quantity > 1) {
                    input.value = quantity - 1;
                    // Trigger form submission
                    form.dispatchEvent(new Event('submit'));
                }
            } else {
                input.value = quantity + 1;
                // Trigger form submission
                form.dispatchEvent(new Event('submit'));
            }
        });
    });

    // ðŸ†• ENHANCED: Update cart quantities via AJAX with silent removal
    document.querySelectorAll('.update-quantity-form').forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const form = this;
            const url = form.action;
            const formData = new FormData(form);
            
            fetch(url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {
                if (!response.ok) throw new Error('Network response was not ok');
                return response.json();
            })
            .then(data => {
                if(data.success) {
                    // Update cart totals dynamically
                    document.querySelectorAll('.cart-subtotal').forEach(el => {
                        el.textContent = `KSh ${data.subtotal.toFixed(2)}`;
                    });
                    document.querySelectorAll('.cart-discounts').forEach(el => {
                        el.textContent = `-KSh ${data.discounts.toFixed(2)}`;
                    });
                    document.querySelectorAll('.cart-total').forEach(el => {
                        el.textContent = `KSh ${data.total.toFixed(2)}`;
                    });
                    
                    // Update cart count in navbar
                    document.querySelectorAll('.cart-count').forEach(el => {
                        el.textContent = data.cart_count;
                    });
                    sessionStorage.setItem('cart_count', data.cart_count);
                    
                    // ðŸ†• SILENTLY remove item if quantity is 0 (no flash message)
                    if(data.removed) {
                        const itemElement = form.closest('.cart-item');
                        if (itemElement) {
                            itemElement.style.opacity = '0';
                            setTimeout(() => {
                                itemElement.remove();
                                // If cart is empty, show empty cart message
                                if (document.querySelectorAll('.cart-item').length === 0) {
                                    document.querySelector('.cart-items-container').innerHTML = 
                                        '<div class="alert alert-info text-center">Your cart is empty</div>';
                                }
                            }, 300);
                        }
                    }
                }
            })
            .catch(error => {
                console.error('Error updating cart:', error);
                // Fallback: submit form normally if AJAX fails
                form.submit();
            });
        });
    });

    // Handle category clicks to show/hide subcategories
    const categoryLinks = document.querySelectorAll('.category-link');
    
    categoryLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const categoryId = this.getAttribute('data-category-id');
            const subcategories = document.getElementById(`subcategories-${categoryId}`);
            
            // Hide all other subcategories
            document.querySelectorAll('.subcategories').forEach(el => {
                if (el.id !== `subcategories-${categoryId}`) {
                    el.style.display = 'none';
                }
            });
            
            // Toggle current subcategories
            if (subcategories.style.display === 'block') {
                subcategories.style.display = 'none';
            } else {
                subcategories.style.display = 'block';
            }
        });
    });

    // ENHANCED ADD TO CART FUNCTIONALITY

    // Enhanced add to cart functionality for forms - prevent default behavior and use AJAX
    document.querySelectorAll('form[action*="add_to_cart"]').forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const url = this.action;
            const formData = new FormData(this);
            const submitButton = this.querySelector('button[type="submit"]');
            
            // Show loading state
            const originalText = submitButton.innerHTML;
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Adding...';
            submitButton.disabled = true;
            
            fetch(url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {
                if (!response.ok) throw new Error('Network response was not ok');
                return response.json();
            })
            .then(data => {
                if(data.success) {
                    // Update cart count in navbar
                    document.querySelectorAll('.cart-count').forEach(el => {
                        el.textContent = data.cart_count;
                        el.style.display = 'block';
                    });
                    sessionStorage.setItem('cart_count', data.cart_count);
                    
                    // Show subtle notification
                    showCartNotification(data.message || 'Product added to cart!');
                } else {
                    // Show error message
                    showCartNotification(data.message || 'Error adding product to cart', 'error');
                }
            })
            .catch(error => {
                console.error('Error adding to cart:', error);
                // Fallback: submit the form normally
                this.submit();
            })
            .finally(() => {
                // Restore button state
                submitButton.innerHTML = originalText;
                submitButton.disabled = false;
            });
        });
    });

    // Function to show cart notification
    function showCartNotification(message, type = 'success') {
        // Remove existing notifications
        const existingNotifications = document.querySelectorAll('.cart-notification');
        existingNotifications.forEach(notification => notification.remove());
        
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `cart-notification ${type === 'error' ? 'bg-danger' : 'bg-success'}`;
        notification.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas ${type === 'error' ? 'fa-exclamation-triangle' : 'fa-check-circle'} me-2"></i>
                <span>${message}</span>
            </div>
        `;
        
        // Add styles if not already present
        if (!document.querySelector('#cart-notification-styles')) {
            const styles = document.createElement('style');
            styles.id = 'cart-notification-styles';
            styles.textContent = `
                .cart-notification {
                    position: fixed;
                    top: 200px;
                    right: 20px;
                    color: white;
                    padding: 12px 16px;
                    border-radius: 8px;
                    z-index: 9999;
                    opacity: 0;
                    transform: translateX(100px);
                    transition: all 0.3s ease;
                    font-size: 14px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                    max-width: 300px;
                }
                .cart-notification.show {
                    opacity: 1;
                    transform: translateX(0);
                }
            `;
            document.head.appendChild(styles);
        }
        
        // Add to page
        document.body.appendChild(notification);
        
        // Show notification
        setTimeout(() => notification.classList.add('show'), 10);
        
        // Auto hide after 1 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    // Search functionality
    const searchForm = document.getElementById('search-form');
    const searchInput = document.getElementById('search-input');
    const searchResults = document.getElementById('search-results');

    if (searchForm && searchInput && searchResults) {
        let searchTimeout;
        
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const query = this.value.trim();
            
            if (query.length < 2) {
                searchResults.style.display = 'none';
                return;
            }
            
            searchTimeout = setTimeout(() => {
                fetch(`/search?q=${encodeURIComponent(query)}&ajax=1`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.products && data.products.length > 0) {
                            displaySearchResults(data.products);
                        } else {
                            displayNoResults();
                        }
                    })
                    .catch(error => {
                        console.error('Search error:', error);
                        searchResults.style.display = 'none';
                    });
            }, 300);
        });

        function displaySearchResults(products) {
            let html = '<div class="search-results-list">';
            products.slice(0, 5).forEach(product => {
                html += `
                    <div class="search-result-item">
                        <a href="/product/${product.id}" class="d-flex align-items-center text-decoration-none text-dark">
                            <img src="${product.image ? '/static/uploads/' + product.image : '/static/images/no-image.png'}" 
                                 alt="${product.name}" class="search-result-img">
                            <div class="search-result-info">
                                <h6 class="mb-1">${product.name}</h6>
                                <div class="product-price">
                                    <span class="text-primary fw-bold">KSh ${product.price}</span>
                                    ${product.discount > 0 ? `<span class="text-danger small">-${product.discount}%</span>` : ''}
                                </div>
                            </div>
                        </a>
                    </div>
                `;
            });
            html += '</div>';
            searchResults.innerHTML = html;
            searchResults.style.display = 'block';
        }

        function displayNoResults() {
            searchResults.innerHTML = `
                <div class="search-no-results p-3 text-center">
                    <p class="mb-0 text-muted">No products found</p>
                </div>
            `;
            searchResults.style.display = 'block';
        }

        // Hide search results when clicking outside
        document.addEventListener('click', function(e) {
            if (!searchForm.contains(e.target)) {
                searchResults.style.display = 'none';
            }
        });
    }

    // Mobile navigation functionality
    const mobileNavToggle = document.querySelector('.mobile-hamburger button');
    const mobileNavDrawer = document.querySelector('.mobile-nav-drawer');
    const mobileNavOverlay = document.querySelector('.mobile-nav-overlay');
    const mobileNavClose = document.querySelector('.mobile-nav-close');

    if (mobileNavToggle && mobileNavDrawer) {
        mobileNavToggle.addEventListener('click', function() {
            mobileNavDrawer.classList.add('active');
            mobileNavOverlay.classList.add('active');
            document.body.style.overflow = 'hidden';
        });

        function closeMobileNav() {
            mobileNavDrawer.classList.remove('active');
            mobileNavOverlay.classList.remove('active');
            document.body.style.overflow = '';
        }

        if (mobileNavClose) {
            mobileNavClose.addEventListener('click', closeMobileNav);
        }

        if (mobileNavOverlay) {
            mobileNavOverlay.addEventListener('click', closeMobileNav);
        }
    }

    // Product image lazy loading
    const productImages = document.querySelectorAll('img[data-src]');
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                    imageObserver.unobserve(img);
                }
            });
        });

        productImages.forEach(img => imageObserver.observe(img));
    } else {
        // Fallback for browsers without IntersectionObserver
        productImages.forEach(img => {
            img.src = img.dataset.src;
            img.removeAttribute('data-src');
        });
    }

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Hot sales animation pause on hover
    const hotSalesRows = document.querySelectorAll('.hot-sales-row');
    hotSalesRows.forEach(row => {
        row.addEventListener('mouseenter', function() {
            this.style.animationPlayState = 'paused';
        });
        
        row.addEventListener('mouseleave', function() {
            this.style.animationPlayState = 'running';
        });
    });

    // Form validation enhancement
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = this.querySelectorAll('[required]');
            let valid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    valid = false;
                    field.classList.add('is-invalid');
                } else {
                    field.classList.remove('is-invalid');
                }
            });
            
            if (!valid) {
                e.preventDefault();
                // Scroll to first invalid field
                const firstInvalid = this.querySelector('.is-invalid');
                if (firstInvalid) {
                    firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    firstInvalid.focus();
                }
            }
        });
    });

    // Initialize any carousels if present
    const carousels = document.querySelectorAll('.carousel');
    carousels.forEach(carousel => {
        new bootstrap.Carousel(carousel);
    });

    // ðŸ†• AUTO-DISMISS FLASH MESSAGES
    // Auto-dismiss flash messages after 4 seconds
    const flashMessages = document.querySelectorAll('.alert-dismissible');
    flashMessages.forEach(message => {
        setTimeout(() => {
            if (message.parentNode) {
                const bsAlert = new bootstrap.Alert(message);
                bsAlert.close();
            }
        }, 4000);
    });
    
    // Also close flash messages when clicking anywhere
    document.addEventListener('click', function() {
        flashMessages.forEach(message => {
            if (message.parentNode) {
                const bsAlert = new bootstrap.Alert(message);
                bsAlert.close();
            }
        });
    });
});