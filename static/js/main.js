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

    // Update cart quantities via AJAX
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
                    
                    // Remove item if quantity is 0
                    if(data.removed) {
                        form.closest('.cart-item').remove();
                    }
                }
            })
            .catch(error => {
                console.error('Error updating cart:', error);
                alert('Error updating cart. Please refresh the page.');
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
});