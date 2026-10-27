document.addEventListener('DOMContentLoaded', function () {
    // Sidebar toggle for mobile
    const sidebar = document.getElementById('sidebar');
    const toggle = document.getElementById('sidebarToggle');
    const closeBtn = document.getElementById('sidebarClose');

    if (toggle && sidebar) {
        toggle.addEventListener('click', () => sidebar.classList.add('show'));
    }
    if (closeBtn && sidebar) {
        closeBtn.addEventListener('click', () => sidebar.classList.remove('show'));
    }

    // Auto-dismiss alerts after 5s
    document.querySelectorAll('.alert-dismissible').forEach(alert => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) bsAlert.close();
        }, 5000);
    });

    // Confirm dangerous actions
    document.querySelectorAll('[data-confirm]').forEach(el => {
        el.addEventListener('click', function (e) {
            if (!confirm(this.dataset.confirm || 'Are you sure?')) {
                e.preventDefault();
            }
        });
    });
});

// Helper to create charts
function createChart(canvasId, type, labels, data, colors) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    return new Chart(ctx, {
        type: type,
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors || [
                    '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'
                ],
                borderWidth: 0,
                borderRadius: type === 'bar' ? 6 : 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: type === 'doughnut' || type === 'pie' ? 'bottom' : 'top',
                    labels: { usePointStyle: true, padding: 16, font: { size: 12 } }
                }
            },
            scales: type === 'bar' || type === 'line' ? {
                y: { beginAtZero: true, grid: { color: '#f1f5f9' } },
                x: { grid: { display: false } }
            } : {}
        }
    });
}
