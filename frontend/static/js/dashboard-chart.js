/* ============================================================
   Ruta: Frontend/static/js/dashboard-chart.js
   Gráfico de estado emocional - última semana
   Espera puntos_semana en formato JSON: [{label:'Lun', valor: 7}, ...]
   ============================================================ */
(function () {
    const canvas = document.getElementById('canvasEmocionalSemana');
    if (!canvas || typeof Chart === 'undefined') return;

    let puntos;
    try {
        puntos = JSON.parse(canvas.dataset.puntos);
    } catch (err) {
        console.error('puntos_semana no es JSON válido', err);
        return;
    }

    new Chart(canvas, {
        type: 'line',
        data: {
            labels: puntos.map(p => p.label),
            datasets: [{
                label: 'Estado emocional',
                data: puntos.map(p => p.valor),
                borderColor: '#2A8E8E',
                backgroundColor: 'rgba(42, 142, 142, 0.15)',
                fill: true,
                tension: 0.35,
                pointRadius: 5,
                pointBackgroundColor: '#2A8E8E'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { min: 0, max: 10, ticks: { stepSize: 2 } }
            },
            plugins: { legend: { display: false } }
        }
    });
})();
