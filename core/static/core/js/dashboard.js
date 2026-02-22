/* ========================================
   LIFE QUEST - DASHBOARD JAVASCRIPT
   Toast Notifications & Interactivity
   ======================================== */

document.addEventListener('DOMContentLoaded', function () {
    console.log('✓ Dashboard initialized');

    // Initialize Toast Notifications
    initializeToasts();

    // Initialize Event Listeners
    initializeEventListeners();

    // Initialize Bootstrap Tooltips
    initializeTooltips();
});

/* ========== TOAST NOTIFICATION SYSTEM ========== */

/**
 * Show a toast notification
 * @param {string} message - The notification message
 * @param {string} type - Type: 'success', 'error', 'info'
 * @param {number} duration - Duration to display in milliseconds (default 3000)
 */
function showToast(message, type = 'info', duration = 3000) {
    const container = getToastContainer();

    // Determine icon based on type
    let icon = 'ℹ';
    if (type === 'success') icon = '✓';
    if (type === 'error') icon = '✕';

    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast-notification ${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${icon}</span>
        <span class="toast-message">${message}</span>
    `;

    container.appendChild(toast);

    // Auto-dismiss
    setTimeout(() => {
        toast.classList.add('removing');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

/**
 * Get or create the toast container
 * @returns {Element} Toast container element
 */
function getToastContainer() {
    let container = document.querySelector('.toast-container');

    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    return container;
}

/**
 * Initialize existing Django message alerts as toasts
 */
function initializeToasts() {
    // Convert Django messages to toasts and remove them
    const alerts = document.querySelectorAll('.alert');

    alerts.forEach(alert => {
        const message = alert.textContent.trim();
        const type = alert.classList.contains('alert-success') ? 'success' :
            alert.classList.contains('alert-error') ? 'error' : 'info';

        showToast(message, type, 4000);
        alert.remove();
    });
}

/* ========== EVENT LISTENERS ========== */

function initializeEventListeners() {
    // Complete task buttons
    const completeButtons = document.querySelectorAll('[data-action="complete"]');
    completeButtons.forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            const taskTitle = this.dataset.taskTitle || 'Task';
            this.style.opacity = '0.6';
            setTimeout(() => {
                window.location.href = this.href;
            }, 200);
        });
    });

    // Delete task buttons
    const deleteButtons = document.querySelectorAll('[data-action="delete"]');
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            if (confirm('Are you sure you want to delete this quest?')) {
                window.location.href = this.href;
            }
        });
    });

    // Logout form
    const logoutForm = document.querySelector('form[data-action="logout"]');
    if (logoutForm) {
        logoutForm.addEventListener('submit', function () {
            const btn = this.querySelector('button[type="submit"]');
            if (btn) {
                btn.innerHTML = '⏳ Logging out...';
                btn.disabled = true;
            }
        });
    }

    // Task form submission
    const taskForm = document.querySelector('form[data-action="add-task"]');
    if (taskForm) {
        taskForm.addEventListener('submit', function () {
            const btn = this.querySelector('button[type="submit"]');
            if (btn) {
                btn.innerHTML = '➕ Adding...';
                btn.disabled = true;
            }
        });
    }
}

/* ========== BOOTSTRAP TOOLTIPS ========== */

function initializeTooltips() {
    // Initialize any tooltips if using Bootstrap
    if (typeof bootstrap !== 'undefined') {
        const tooltipElements = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltipElements.forEach(el => {
            new bootstrap.Tooltip(el);
        });
    }
}

/* ========== UTILITY FUNCTIONS ========== */

/**
 * Trigger a sound effect (optional)
 * @param {string} type - Sound type: 'success', 'error', etc.
 */
function playSound(type = 'success') {
    // Optional: Add sound effects using Web Audio API or HTML5 Audio
    // For now, this is a placeholder
    console.log('Sound:', type);
}

/**
 * Animate a count-up number
 * @param {Element} element -  The element to animate
 * @param {number} target - Target number
 * @param {number} duration - Duration in milliseconds
 */
function animateCounter(element, target, duration = 500) {
    const start = parseInt(element.textContent) || 0;
    const increment = (target - start) / (duration / 16);
    let current = start;

    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            element.textContent = target;
            clearInterval(timer);
        } else {
            element.textContent = Math.floor(current);
        }
    }, 16);
}

/**
 * Format a number with commas
 * @param {number} num - Number to format
 * @returns {string} Formatted number
 */
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/* ========== KEYBOARD SHORTCUTS ========== */

document.addEventListener('keydown', function (e) {
    // Ctrl/Cmd + K: Focus task input
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        const taskInput = document.querySelector('input[name="title"]');
        if (taskInput) taskInput.focus();
    }

    // Escape: Close any dropdowns or modals
    if (e.key === 'Escape') {
        console.log('Escape pressed');
    }
});

/* ========== SCROLL ANIMATIONS ========== */

function observeScrollAnimations() {
    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.animation = 'slideInUp 0.4s ease-out';
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });

        document.querySelectorAll('.quest-item').forEach(item => {
            observer.observe(item);
        });
    }
}

console.log('✓ Dashboard JavaScript loaded successfully');
