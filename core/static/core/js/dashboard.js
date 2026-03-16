/* ========================================
   LIFE QUEST - DASHBOARD JAVASCRIPT
   Toast Notifications & Interactivity
   ======================================== */

/* ========== DELETE MODAL STATE ========== */
// Stores the quest element and ID awaiting confirmation.
let currentQuestElement = null;
let currentQuestId = null;

document.addEventListener('DOMContentLoaded', function () {
    console.log('✓ Dashboard initialized');

    // Initialize Toast Notifications
    initializeToasts();

    // Initialize Event Listeners
    initializeEventListeners();

    // Initialize Bootstrap Tooltips
    initializeTooltips();

    // Initialize custom difficulty dropdown
    initDiffDropdown();

    // Initialize mobile hamburger menu
    initMobileMenu();
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
    // Add Task form (AJAX – no page reload)
    const taskForm = document.querySelector('form[data-action="add-task"]');
    if (taskForm) {
        taskForm.addEventListener('submit', handleAddTask);
    }

    // Single delegated listener on the quest board covers complete, undo,
    // and delete — including elements injected dynamically into the DOM.
    const questBoard = document.querySelector('.quest-board');
    if (questBoard) {
        questBoard.addEventListener('click', handleQuestAction);
    }

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

    // --- Delete Confirmation Modal Buttons ---
    const cancelBtn = document.getElementById('modal-cancel-btn');
    const confirmBtn = document.getElementById('modal-confirm-btn');
    const overlay = document.getElementById('delete-modal-overlay');

    if (cancelBtn) cancelBtn.addEventListener('click', hideDeleteModal);
    if (confirmBtn) confirmBtn.addEventListener('click', executeDeleteQuest);

    // Clicking the dark backdrop also dismisses the modal
    if (overlay) {
        overlay.addEventListener('click', function (e) {
            if (e.target === overlay) hideDeleteModal();
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

/* ========== QUEST ACTION DISPATCHER (EVENT DELEGATION) ========== */

/**
 * Single click handler delegated to .quest-board.
 * Dispatches to the correct AJAX handler based on data-action.
 */
function handleQuestAction(e) {
    const btn = e.target.closest('[data-action]');
    if (!btn) return;

    const action = btn.dataset.action;
    if (action === 'complete') {
        e.preventDefault();
        completeQuest(btn);
    } else if (action === 'delete') {
        e.preventDefault();
        deleteQuest(btn);
    } else if (action === 'undo') {
        e.preventDefault();
        undoQuest(btn);
    }
}

/* ========== ADD TASK (AJAX) ========== */

function handleAddTask(e) {
    e.preventDefault();
    const form = e.currentTarget;
    const btn = form.querySelector('button[type="submit"]');
    const titleInput = form.querySelector('input[name="title"]');
    const diffSelect = form.querySelector('#diff-value');

    btn.innerHTML = '⏳ Adding...';
    btn.disabled = true;

    fetch(form.action, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCsrfToken() },
        body: new FormData(form),
    })
        .then(res => { if (!res.ok) throw new Error(res.status); return res.json(); })
        .then(data => {
            if (data.status === 'success') {
                titleInput.value = '';
                diffSelect.value = '10';
                // Reset trigger button to Easy
                const trigger = document.getElementById('diff-trigger');
                if (trigger) {
                    trigger.querySelector('.diff-trigger-icon').textContent = '⚡';
                    trigger.querySelector('.diff-trigger-label').textContent = 'Easy';
                    trigger.querySelector('.diff-trigger-xp').textContent = '+10 XP';
                    trigger.className = 'diff-trigger active-easy';
                }
                // Reset selected state in panel
                document.querySelectorAll('.diff-item').forEach(i => i.classList.remove('selected'));
                const firstItem = document.querySelector('.diff-item[data-value="10"]');
                if (firstItem) firstItem.classList.add('selected');

                const activeList = document.getElementById('active-quest-list');
                if (activeList) {
                    const emptyState = document.getElementById('empty-state');
                    if (emptyState) emptyState.remove();
                    activeList.insertAdjacentHTML('beforeend', buildActiveQuestHTML(data.quest));
                }
                updateActiveCount(1);
                showToast('New Quest Added! ⚔️', 'success', 3000);
            } else {
                showToast(data.message || 'Failed to add quest.', 'error', 4000);
            }
        })
        .catch(err => {
            console.error('Add task error:', err);
            showToast('Something went wrong. Please try again.', 'error', 4000);
        })
        .finally(() => {
            btn.innerHTML = '<i class="fas fa-plus"></i> ADD';
            btn.disabled = false;
            titleInput.focus();
        });
}

/* ========== COMPLETE QUEST (AJAX) ========== */

function completeQuest(btn) {
    const taskId = btn.dataset.taskId;
    const questItem = document.getElementById(`quest-${taskId}`);

    btn.style.pointerEvents = 'none';
    btn.style.opacity = '0.4';

    fetch(getQuestUrl('complete', taskId), {
        method: 'POST',
        headers: { 'X-CSRFToken': getCsrfToken() },
    })
        .then(res => { if (!res.ok) throw new Error(res.status); return res.json(); })
        .then(data => {
            if (data.status === 'success') {
                if (questItem) {
                    questItem.classList.add('quest-completing');
                    setTimeout(() => {
                        questItem.remove();
                        updateActiveCount(-1);
                        checkEmptyState();

                        // Add the completed card to the completed list
                        const completedList = document.getElementById('completed-quest-list');
                        const completedSection = document.getElementById('completed-section');
                        if (completedList) {
                            completedList.insertAdjacentHTML('afterbegin', buildCompletedQuestHTML(data.quest));
                            // Keep only the 3 most recent visible cards to match server behaviour
                            const cards = completedList.querySelectorAll('.quest-item.completed');
                            if (cards.length > 3) cards[cards.length - 1].remove();
                        }
                        if (completedSection) completedSection.style.display = '';
                        updateCompletedCount(1);
                    }, 500);
                }
                updatePlayerStats(data);
                const msg = data.leveled_up
                    ? `LEVEL UP! You reached Level ${data.new_level}! ★`
                    : `Quest Complete! +${data.xp_gained} XP`;
                showToast(msg, 'success', 4000);
            }
        })
        .catch(err => {
            console.error('Complete quest error:', err);
            btn.style.pointerEvents = '';
            btn.style.opacity = '';
            showToast('Something went wrong. Please try again.', 'error', 4000);
        });
}

/* ========== DELETE QUEST (MODAL FLOW) ========== */

/**
 * Step 1 – intercept the trash-icon click.
 * Store state and open the confirmation modal instead of using window.confirm().
 */
function deleteQuest(btn) {
    currentQuestId = btn.dataset.taskId;
    currentQuestElement = document.getElementById(`quest-${currentQuestId}`);
    showDeleteModal();
}

/** Show the custom delete confirmation modal. */
function showDeleteModal() {
    const overlay = document.getElementById('delete-modal-overlay');
    if (overlay) overlay.classList.add('active');
}

/** Hide the modal and clear pending-delete state. */
function hideDeleteModal() {
    const overlay = document.getElementById('delete-modal-overlay');
    if (overlay) overlay.classList.remove('active');
    currentQuestElement = null;
    currentQuestId = null;
}

/**
 * Step 2 – called when the modal "Delete" button is clicked.
 * Hides the modal then fires the fetch() DELETE request.
 */
function executeDeleteQuest() {
    // Capture and clear state before async work
    const taskId = currentQuestId;
    const questItem = currentQuestElement;
    hideDeleteModal();

    if (!taskId) return;

    const wasActive = questItem && questItem.classList.contains('active');

    fetch(getQuestUrl('delete', taskId), {
        method: 'POST',
        headers: { 'X-CSRFToken': getCsrfToken() },
    })
        .then(res => { if (!res.ok) throw new Error(res.status); return res.json(); })
        .then(data => {
            if (data.status === 'success') {
                if (questItem) {
                    questItem.classList.add('quest-completing');
                    setTimeout(() => {
                        questItem.remove();
                        if (wasActive) {
                            updateActiveCount(-1);
                            checkEmptyState();
                        } else {
                            updateCompletedCount(-1);
                            checkCompletedSection();
                        }
                    }, 500);
                }
                showToast('Quest deleted.', 'info', 3000);
            }
        })
        .catch(err => {
            console.error('Delete quest error:', err);
            showToast('Something went wrong. Please try again.', 'error', 4000);
        });
}

/* ========== UNDO QUEST (AJAX) ========== */

function undoQuest(btn) {
    const taskId = btn.dataset.taskId;
    const questItem = document.getElementById(`quest-${taskId}`);

    btn.style.pointerEvents = 'none';
    btn.style.opacity = '0.4';

    fetch(getQuestUrl('undo', taskId), {
        method: 'POST',
        headers: { 'X-CSRFToken': getCsrfToken() },
    })
        .then(res => { if (!res.ok) throw new Error(res.status); return res.json(); })
        .then(data => {
            if (data.status === 'success') {
                if (questItem) {
                    questItem.remove();
                    updateCompletedCount(-1);
                    checkCompletedSection();
                }

                // If the server found a replacement task to fill the 3rd slot, append it
                if (data.next_completed) {
                    const completedList = document.getElementById('completed-quest-list');
                    const completedSection = document.getElementById('completed-section');
                    if (completedList) {
                        // Only add if not already in the DOM (e.g. rapid clicks)
                        if (!document.getElementById(`quest-${data.next_completed.id}`)) {
                            completedList.insertAdjacentHTML('beforeend', buildCompletedQuestHTML(data.next_completed));
                        }
                    }
                    if (completedSection) completedSection.style.display = '';
                }

                const activeList = document.getElementById('active-quest-list');
                if (activeList) {
                    const emptyState = document.getElementById('empty-state');
                    if (emptyState) emptyState.remove();
                    activeList.insertAdjacentHTML('afterbegin', buildActiveQuestHTML(data.quest));
                }
                updateActiveCount(1);
                updatePlayerStats(data);
                showToast(`Quest reverted! -${data.xp_lost} XP`, 'info', 3000);
            }
        })
        .catch(err => {
            console.error('Undo quest error:', err);
            btn.style.pointerEvents = '';
            btn.style.opacity = '';
            showToast('Something went wrong. Please try again.', 'error', 4000);
        });
}

/* ========== DOM HELPERS ========== */

/**
 * Resolve a named action URL by replacing the '0' placeholder with a real task ID.
 * window.QUEST_URLS is populated by an inline <script> in the template.
 */
function getQuestUrl(action, taskId) {
    return window.QUEST_URLS[action].replace('/0/', `/${taskId}/`);
}

/**
 * Build the HTML string for a new active quest card from a quest data object.
 * Uses escapeHtml to prevent XSS from user-supplied titles.
 */
function buildActiveQuestHTML(quest) {
    const { id, title, difficulty, created_at } = quest;
    const diffMap = { 100: ['epic', 'EPIC'], 50: ['hard', 'HARD'], 30: ['medium', 'MEDIUM'], 10: ['easy', 'EASY'] };
    const [cls, label] = diffMap[difficulty] || ['easy', 'EASY'];

    return `
    <div class="quest-item active" id="quest-${id}" style="animation:slideInUp 0.35s ease-out;">
        <a href="${getQuestUrl('complete', id)}"
           class="quest-checkbox"
           data-action="complete"
           data-task-id="${id}"
           data-task-title="${escapeHtml(title)}"
           title="Complete quest">
            <i class="fas fa-check"></i>
        </a>
        <div class="quest-info">
            <span class="quest-title">${escapeHtml(title)}</span>
            <div class="quest-meta">
                <span class="quest-badge ${cls}">${label}</span>
                <span class="quest-timestamp">
                    <i class="far fa-clock"></i> ${created_at}
                </span>
            </div>
        </div>
        <div class="quest-actions">
            <span class="quest-xp">+${difficulty} XP</span>
            <a href="${getQuestUrl('delete', id)}"
               class="btn-delete"
               data-action="delete"
               data-task-id="${id}"
               title="Delete quest">
                <i class="fas fa-trash"></i>
            </a>
        </div>
    </div>`;
}

/**
 * Build the HTML string for a completed quest card from a quest data object.
 */
function buildCompletedQuestHTML(quest) {
    const { id, title, difficulty, completed_at } = quest;
    const diffMap = { 100: ['epic', 'EPIC'], 50: ['hard', 'HARD'], 30: ['medium', 'MEDIUM'], 10: ['easy', 'EASY'] };
    const [cls, label] = diffMap[difficulty] || ['easy', 'EASY'];

    return `
    <div class="quest-item completed" id="quest-${id}" style="animation:slideInUp 0.35s ease-out;">
        <a href="${getQuestUrl('undo', id)}"
           class="quest-checkbox completed-check"
           data-action="undo"
           data-task-id="${id}"
           title="Undo task">
            <i class="fas fa-check"></i>
        </a>
        <div class="quest-info">
            <span class="quest-title">${escapeHtml(title)}</span>
            <div class="quest-meta">
                <span class="quest-badge ${cls}">${label}</span>
                <span class="quest-timestamp">
                    <i class="far fa-clock"></i> Completed: ${completed_at}
                </span>
            </div>
        </div>
        <div class="quest-actions">
            <span class="quest-xp">+${difficulty} XP</span>
            <a href="${getQuestUrl('delete', id)}"
               class="btn-delete"
               data-action="delete"
               data-task-id="${id}"
               title="Delete quest">
                <i class="fas fa-trash"></i>
            </a>
        </div>
    </div>`;
}

/** Safely escape a string for insertion into HTML content. */
function escapeHtml(str) {
    const d = document.createElement('div');
    d.appendChild(document.createTextNode(String(str)));
    return d.innerHTML;
}

/** Show the empty-state placeholder when the active list becomes empty. */
function checkEmptyState() {
    const activeList = document.getElementById('active-quest-list');
    if (activeList && activeList.children.length === 0) {
        activeList.innerHTML = `
        <div id="empty-state" class="empty-state">
            <i class="fas fa-scroll"></i>
            <p>No active quests. Add a new mission above!</p>
        </div>`;
    }
}

/** Hide the completed section when its list becomes empty. */
function checkCompletedSection() {
    const list = document.getElementById('completed-quest-list');
    const section = document.getElementById('completed-section');
    if (list && section && list.children.length === 0) {
        section.style.display = 'none';
    }
}

/** Update the Active Quests count badge in the sidebar nav. */
function updateActiveCount(delta) {
    const el = document.getElementById('nav-active-count');
    if (el) el.textContent = Math.max(0, (parseInt(el.textContent) || 0) + delta);
}

/** Update the Completed count badge in the sidebar nav and section title. */
function updateCompletedCount(delta) {
    ['nav-completed-count', 'completed-count'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.textContent = Math.max(0, (parseInt(el.textContent) || 0) + delta);
    });
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

/* ========== CSRF TOKEN HELPER ========== */

/**
 * Read the CSRF token from Django's csrftoken cookie, falling back to
 * the first hidden input[name=csrfmiddlewaretoken] in the page.
 */
function getCsrfToken() {
    const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    if (match) return decodeURIComponent(match[1]);
    const input = document.querySelector('[name=csrfmiddlewaretoken]');
    return input ? input.value : '';
}

/* ========== UPDATE PLAYER STATS IN SIDEBAR ========== */

/**
 * Reflect new EXP / level values returned by the server into the sidebar
 * without a page reload.
 * @param {Object} data - JSON response from complete_task view
 */
function updatePlayerStats(data) {
    const levelBadge = document.getElementById('level-badge');
    const expNext    = document.getElementById('exp-next');

    if (levelBadge) levelBadge.textContent = `Lv. ${data.new_level}`;
    if (expNext) {
        const remaining = data.next_level_exp - data.new_exp;
        expNext.textContent = `${remaining} EXP for next level`;
    }

    // Update every EXP text element (sidebar + mobile menu share the same class)
    document.querySelectorAll('.exp-values').forEach(el => {
        el.textContent = `${data.new_exp}/${data.next_level_exp}`;
    });

    // Update every EXP bar fill (sidebar + mobile menu share the same class)
    document.querySelectorAll('.exp-bar-fill').forEach(el => {
        el.style.width = `${data.exp_percentage}%`;
    });
}

/* ========== KEYBOARD SHORTCUTS ========== */

document.addEventListener('keydown', function (e) {
    // Ctrl/Cmd + K: Focus task input
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        const taskInput = document.querySelector('input[name="title"]');
        if (taskInput) taskInput.focus();
    }

    // Escape: Close the delete confirmation modal (if open)
    if (e.key === 'Escape') {
        hideDeleteModal();
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

/* ========== CUSTOM DIFFICULTY DROPDOWN ========== */

function initDiffDropdown() {
    const trigger  = document.getElementById('diff-trigger');
    const panel    = document.getElementById('diff-panel');
    const hiddenInput = document.getElementById('diff-value');
    if (!trigger || !panel || !hiddenInput) return;

    // Mark the default selected item (Easy)
    const defaultItem = panel.querySelector('.diff-item[data-value="10"]');
    if (defaultItem) {
        defaultItem.classList.add('selected');
        trigger.classList.add('active-easy');
    }

    // Toggle open / close
    trigger.addEventListener('click', function (e) {
        e.stopPropagation();
        const isOpen = panel.classList.toggle('open');
        trigger.classList.toggle('open', isOpen);
        trigger.setAttribute('aria-expanded', isOpen);
    });

    // Select an item
    panel.addEventListener('click', function (e) {
        const item = e.target.closest('.diff-item');
        if (!item) return;

        const value = item.dataset.value;
        const icon  = item.dataset.icon;
        const label = item.dataset.label;
        const xp    = item.dataset.xp;
        const color = item.dataset.color;

        // Update hidden input
        hiddenInput.value = value;

        // Update trigger appearance
        trigger.querySelector('.diff-trigger-icon').textContent  = icon;
        trigger.querySelector('.diff-trigger-label').textContent = label;
        trigger.querySelector('.diff-trigger-xp').textContent   = xp;
        trigger.className = `diff-trigger active-${color}`;

        // Mark selected row
        panel.querySelectorAll('.diff-item').forEach(i => i.classList.remove('selected'));
        item.classList.add('selected');

        // Close panel
        panel.classList.remove('open');
        trigger.setAttribute('aria-expanded', 'false');
    });

    // Click outside closes panel
    document.addEventListener('click', function () {
        panel.classList.remove('open');
        trigger.classList.remove('open');
        trigger.setAttribute('aria-expanded', 'false');
    });
}

/* ========== MOBILE MENU ========== */

function initMobileMenu() {
    const hamburger = document.getElementById('mobile-hamburger');
    const menu      = document.getElementById('mobile-menu');
    const overlay   = document.getElementById('mobile-menu-overlay');
    const closeBtn  = document.getElementById('mobile-menu-close');
    const mainContent = document.querySelector('.main-content');

    if (!hamburger || !menu || !overlay) return;

    function openMenu() {
        menu.classList.add('open');
        overlay.classList.add('open');
        // Prevent the main scroll area from scrolling while menu is open
        if (mainContent) mainContent.style.overflow = 'hidden';
    }

    function closeMenu() {
        menu.classList.remove('open');
        overlay.classList.remove('open');
        if (mainContent) mainContent.style.overflow = '';
    }

    hamburger.addEventListener('click', openMenu);

    // Overlay click = "click outside"
    overlay.addEventListener('click', closeMenu);

    // Explicit close button inside the panel
    if (closeBtn) closeBtn.addEventListener('click', closeMenu);

    // Escape key closes the menu (in addition to the delete-modal handler)
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') closeMenu();
    });
}
