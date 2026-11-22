/* INKLINE Analytics & Dashboard Visualizations */

function initViewsChart(canvasId, labels, data) {
  const ctx = document.getElementById(canvasId);
  if (!ctx || !window.Chart) return;

  new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Daily Story Views',
        data: data,
        borderColor: '#800020',
        backgroundColor: 'rgba(128, 0, 32, 0.08)',
        fill: true,
        tension: 0.35,
        pointBackgroundColor: '#800020',
        pointRadius: 4,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: { precision: 0 }
        }
      }
    }
  });
}

function initCategoryDistributionChart(canvasId, labels, data) {
  const ctx = document.getElementById(canvasId);
  if (!ctx || !window.Chart) return;

  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: data,
        backgroundColor: [
          '#800020', '#D97706', '#2563EB', '#059669', '#7C3AED', '#DB2777'
        ],
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom' }
      }
    }
  });
}

function initStatusBreakdownChart(canvasId, labels, data) {
  const ctx = document.getElementById(canvasId);
  if (!ctx || !window.Chart) return;

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Count',
        data: data,
        backgroundColor: ['#16A34A', '#D97706', '#6B7280', '#DC2626'],
        borderRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        y: { beginAtZero: true, ticks: { precision: 0 } }
      }
    }
  });
}
