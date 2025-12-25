/**
 * Main JavaScript file for GymSphere
 * Handles onboarding navigation, progress charts, and product carousel
 */

// Onboarding navigation helpers
function goToNextStep(currentStep, nextStep) {
    window.location.href = nextStep;
}

function goBack(previousStep) {
    window.location.href = previousStep;
}

// Product carousel functionality
function initProductCarousel() {
    const carousel = document.getElementById('productCarousel');
    if (!carousel) return;

    let scrollPosition = 0;
    const scrollAmount = 300;

    // Auto-scroll if needed
    const scrollInterval = setInterval(() => {
        if (carousel.scrollLeft >= carousel.scrollWidth - carousel.clientWidth) {
            scrollPosition = 0;
        } else {
            scrollPosition += scrollAmount;
        }
        carousel.scrollTo({ left: scrollPosition, behavior: 'smooth' });
    }, 3000);
}

// Chart.js progress chart initialization
function initProgressChart() {
    const canvas = document.getElementById('progressChart');
    if (!canvas) return;

    fetch('/api/user_progress')
        .then(response => response.json())
        .then(data => {
            if (!data || data.length === 0) {
                canvas.parentElement.innerHTML = '<p class="text-gray-400">No progress data yet. Start logging your weight!</p>';
                return;
            }

            const ctx = canvas.getContext('2d');
            const labels = data.map(d => new Date(d.logged_at).toLocaleDateString()).reverse();
            const weights = data.map(d => d.weight).reverse();

            if (typeof Chart !== 'undefined') {
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'Weight (kg)',
                            data: weights,
                            borderColor: '#22d3ee',
                            backgroundColor: 'rgba(34, 211, 238, 0.1)',
                            tension: 0.4,
                            fill: true
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                labels: { color: '#e9e9ff' }
                            }
                        },
                        scales: {
                            y: {
                                ticks: { color: '#e9e9ff' },
                                grid: { color: 'rgba(255, 255, 255, 0.1)' }
                            },
                            x: {
                                ticks: { color: '#e9e9ff' },
                                grid: { color: 'rgba(255, 255, 255, 0.1)' }
                            }
                        }
                    }
                });
            }
        })
        .catch(error => {
            console.error('Error loading progress data:', error);
            canvas.parentElement.innerHTML = '<p class="text-gray-400">Error loading progress data.</p>';
        });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function () {
    initProductCarousel();
    initProgressChart();

    if (document.getElementById('createPlanBtn')) {
        initPlanFeatures();
    }

    // Mobile Menu Toggle
    const mobileBtn = document.getElementById('mobileMenuBtn');
    const mobileMenu = document.getElementById('mobileMenu');
    if (mobileBtn && mobileMenu) {
        mobileBtn.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
            mobileMenu.classList.toggle('flex');
        });
    }
});

function initPlanFeatures() {
    const createBtn = document.getElementById('createPlanBtn');

    fetchTodayPlan();
    fetchPlanStats();
    fetchPlanCalendar();

    if (createBtn) {
        createBtn.addEventListener('click', () => {
            if (confirm("Generate new 30-day plan?")) {
                generatePlan();
            }
        });
    }

    document.getElementById('markWorkoutBtn')?.addEventListener('click', () => handleCheckIn('exercise'));
    document.getElementById('markDietBtn')?.addEventListener('click', () => handleCheckIn('diet'));
}

async function generatePlan() {
    const loadingEl = document.getElementById('planLoading');
    loadingEl.classList.remove('hidden');

    try {
        const res = await fetch('/api/plan/generate', {
            method: 'POST',
            body: JSON.stringify({ start_date: new Date().toISOString().split('T')[0] })
        });
        if (res.ok) {
            alert("Plan created!");
            location.reload();
        } else {
            alert("Error creating plan.");
        }
    } catch (e) {
        console.error(e);
        alert("Server error.");
    } finally {
        loadingEl.classList.add('hidden');
    }
}

async function fetchTodayPlan() {
    const container = document.getElementById('planContainer');
    const createBtn = document.getElementById('createPlanBtn');
    const dateEl = document.getElementById('todayDate');

    try {
        const res = await fetch('/api/plan/today');
        const data = await res.json();

        if (data.status === 'no_plan') {
            createBtn.classList.remove('hidden');
            container.classList.add('hidden');
            return;
        }

        createBtn.classList.remove('hidden');
        createBtn.textContent = "Regenerate Plan";
        container.classList.remove('hidden');

        if (data.status === 'no_entry_for_today') {
            document.getElementById('todayWorkoutList').innerHTML = '<div>Plan ended.</div>';
            return;
        }

        const entry = data.entry;
        window.currentEntryId = entry.id;
        dateEl.textContent = new Date(entry.date).toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric' });

        const workoutList = document.getElementById('todayWorkoutList');
        const workoutBtn = document.getElementById('markWorkoutBtn');

        if (!entry.is_exercise_day) {
            workoutList.innerHTML = '<div class="text-blue-300">Rest Day</div>';
            workoutBtn.style.display = 'none';
        } else {
            workoutBtn.style.display = 'inline-block';
            if (entry.is_exercise_completed) {
                workoutBtn.textContent = "Done";
                workoutBtn.disabled = true;
                workoutBtn.classList.add('bg-green-600', 'opacity-50', 'cursor-not-allowed');
            } else {
                workoutBtn.textContent = "Mark Done";
                workoutBtn.disabled = false;
                workoutBtn.classList.remove('bg-green-600', 'opacity-50', 'cursor-not-allowed');
            }

            let html = '';
            (entry.exercise_payload || []).forEach(ex => {
                html += `<div class="text-white text-sm">• ${ex.name}</div>`;
            });
            workoutList.innerHTML = html;
        }

        const dietList = document.getElementById('todayDietList');
        const dietBtn = document.getElementById('markDietBtn');

        if (entry.is_diet_completed) {
            dietBtn.textContent = "Done";
            dietBtn.disabled = true;
            dietBtn.classList.add('bg-green-600', 'opacity-50', 'cursor-not-allowed');
        } else {
            dietBtn.textContent = "Mark Done";
            dietBtn.disabled = false;
            dietBtn.classList.remove('bg-green-600', 'opacity-50', 'cursor-not-allowed');
        }

        const diet = entry.diet_payload || {};
        const meals = diet.meals || {};

        dietList.innerHTML = `
            <div class="text-xs text-emerald-300 mb-1">~${diet.calories} kcal</div>
            <div class="space-y-1">
                <div class="text-xs"><span class="text-gray-400">Brekkie:</span> <span class="text-white">${meals.breakfast || '-'}</span></div>
                <div class="text-xs"><span class="text-gray-400">Lunch:</span> <span class="text-white">${meals.lunch || '-'}</span></div>
                <div class="text-xs"><span class="text-gray-400">Dinner:</span> <span class="text-white">${meals.dinner || '-'}</span></div>
            </div>
        `;

    } catch (e) { console.error(e); }
}

async function fetchPlanStats() {
    try {
        const res = await fetch('/api/plan/stats');
        const data = await res.json();
        document.getElementById('currentStreak').textContent = data.current_streak;
        document.getElementById('longestStreak').textContent = data.longest_streak;
    } catch (e) { }
}

async function fetchPlanCalendar() {
    const grid = document.getElementById('calendarGrid');
    if (!grid) return;

    // Clear old days
    while (grid.children.length > 7) grid.removeChild(grid.lastChild);

    try {
        const res = await fetch('/api/plan/calendar');
        const entries = await res.json();

        entries.forEach(e => {
            const d = document.createElement('div');
            d.className = 'p-1 rounded text-xs flex items-center justify-center aspect-square';
            d.textContent = new Date(e.date).getDate();

            if (e.status === 'completed') d.classList.add('bg-green-500/30', 'text-green-200');
            else if (e.status === 'missed') d.classList.add('bg-red-500/20', 'text-red-300');
            else if (e.status === 'today') d.classList.add('border', 'border-indigo-400', 'bg-indigo-500/10');
            else d.classList.add('text-gray-500');

            grid.appendChild(d);
        });
    } catch (e) { }
}

async function handleCheckIn(type) {
    if (!window.currentEntryId) return;
    try {
        const res = await fetch('/api/plan/checkin', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ entry_id: window.currentEntryId, type: type })
        });
        if (res.ok) {
            fetchTodayPlan();
            fetchPlanStats();
            fetchPlanCalendar();
        }
    } catch (e) { console.error(e); }
}


// --- Notification Center Logic ---

function initNotifications() {
    const btn = document.getElementById('notifBtn');
    const panel = document.getElementById('notificationPanel');
    const closeBtn = document.getElementById('closeNotifs');
    const markAllBtn = document.getElementById('markAllReadBtn');

    if (btn && panel) {
        btn.addEventListener('click', () => {
            panel.classList.remove('translate-x-full');
            // Fetch when opened
            fetchNotifications();
        });
    }

    if (closeBtn && panel) {
        closeBtn.addEventListener('click', () => {
            panel.classList.add('translate-x-full');
        });
    }

    if (markAllBtn) {
        markAllBtn.addEventListener('click', markAllNotificationsRead);
    }

    // Initial fetch for badge
    fetchNotifications();

    // Poll every 5 minutes
    setInterval(fetchNotifications, 300000);
}

async function fetchNotifications() {
    try {
        const res = await fetch('/api/notifications');
        const notifs = await res.json();

        renderNotifications(notifs);
        updateBadge(notifs);
    } catch (e) { console.error("Error fetching notifications", e); }
}

function renderNotifications(notifs) {
    const list = document.getElementById('notificationList');
    if (!list) return;

    if (notifs.length === 0) {
        list.innerHTML = '<div class="text-center text-gray-500 py-10 text-sm">No new notifications</div>';
        return;
    }

    let html = '';
    notifs.forEach(n => {
        const bgClass = n.is_read ? 'opacity-50' : 'bg-white/5 border border-white/10';
        const icon = n.type === 'plan' ? '📅' : (n.type === 'streak_alert' ? '🔥' : '🔔');

        html += `
        <div class="p-3 rounded-xl ${bgClass} transition hover:bg-white/10 relative group">
            <div class="flex justify-between items-start mb-1">
                <span class="text-sm font-semibold text-cyan-200">${icon} ${n.title}</span>
                <span class="text-[10px] text-gray-500">${n.created_at}</span>
            </div>
            <p class="text-xs text-gray-300 leading-relaxed">${n.message}</p>
            ${!n.is_read ? `
            <button onclick="markNotificationRead(${n.id})" class="absolute top-2 right-2 text-xs text-cyan-500 opacity-0 group-hover:opacity-100 transition">
                Mark read
            </button>` : ''}
        </div>
        `;
    });
    list.innerHTML = html;
}

function updateBadge(notifs) {
    const badge = document.getElementById('notifBadge');
    const countDisplay = document.getElementById('unreadCountDisplay');

    const unread = notifs.filter(n => !n.is_read).length;

    if (badge) {
        if (unread > 0) {
            badge.classList.remove('hidden');
        } else {
            badge.classList.add('hidden');
        }
    }

    if (countDisplay) {
        countDisplay.textContent = `${unread} unread`;
    }
}

async function markNotificationRead(id) {
    try {
        await fetch('/api/notifications/read', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: id })
        });
        fetchNotifications();
    } catch (e) { }
}

async function markAllNotificationsRead() {
    try {
        await fetch('/api/notifications/read', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({}) // Empty for all
        });
        fetchNotifications();
    } catch (e) { }
}

// --- Shopping Logic ---

async function initShoppingCarousel() {
    const container = document.getElementById('shoppingCarousel');
    if (!container) return;

    try {
        const res = await fetch('/api/shop/recommend');
        const items = await res.json();

        if (items.length === 0) {
            container.innerHTML = '<div class="text-gray-500 text-sm">No recommendations yet.</div>';
            return;
        }

        let html = '';
        items.forEach(item => {
            html += `
            <div class="flex-none w-40 glass rounded-xl p-3 flex flex-col items-center text-center gap-2 group relative overflow-hidden">
                <div class="w-full aspect-square rounded-lg bg-black/50 overflow-hidden mb-1">
                    <img src="${item.image_url}" alt="${item.name}" class="w-full h-full object-cover transition duration-300 group-hover:scale-110">
                </div>
                <div class="text-xs font-semibold truncate w-full">${item.name}</div>
                <div class="text-[10px] text-cyan-300">$${item.price}</div>
                <a href="${item.affiliate_url}" target="_blank" class="absolute inset-0 bg-black/60 flex items-center justify-center opacity-0 group-hover:opacity-100 transition duration-300 backdrop-blur-sm">
                    <span class="text-xs font-bold text-white bg-cyan-500 px-3 py-1 rounded-full">View Deal</span>
                </a>
            </div>
            `;
        });
        container.innerHTML = html;

    } catch (e) { console.error(e); }
}


// Initialize everything
document.addEventListener('DOMContentLoaded', () => {
    // Mobile menu loaded in base
    initPlanFeatures();
    initNotifications();
    initShoppingCarousel();
});


