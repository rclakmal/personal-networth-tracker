// Chart Management Module

// Create asset chart for individual account view
function createAssetChart(history, currency) {
    const canvas = document.getElementById('assetChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    if (AppState.assetChart) {
        AppState.assetChart.destroy();
    }
    
    const currentTheme = window.getCurrentTheme ? window.getCurrentTheme() : 'light';
    const chartColors = getChartColors(currentTheme);
    
    AppState.assetChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: history.map(point => new Date(point.date).toLocaleDateString()),
            datasets: [{
                label: 'Value',
                data: history.map(point => point.value),
                borderColor: chartColors.primary,
                backgroundColor: chartColors.primaryBg,
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 6,
                pointBackgroundColor: chartColors.primary,
                pointBorderColor: chartColors.bg,
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: chartColors.bg,
                    titleColor: chartColors.text,
                    bodyColor: chartColors.text,
                    borderColor: chartColors.border,
                    borderWidth: 1,
                    cornerRadius: 8,
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        title: function(tooltipItems) {
                            return new Date(tooltipItems[0].label).toLocaleDateString('en-US', {
                                weekday: 'short',
                                year: 'numeric',
                                month: 'short',
                                day: 'numeric'
                            });
                        },
                        label: function(context) {
                            return 'Value: ' + formatCurrency(context.parsed.y, currency);
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    ticks: {
                        callback: function(value) {
                            return formatCurrency(value, currency);
                        },
                        color: chartColors.text,
                        maxTicksLimit: 8
                    },
                    grid: {
                        color: chartColors.grid,
                        borderColor: chartColors.border,
                        lineWidth: 1
                    }
                },
                x: {
                    grid: {
                        color: chartColors.grid,
                        borderColor: chartColors.border,
                        lineWidth: 1
                    },
                    ticks: {
                        maxTicksLimit: 8,
                        color: chartColors.text
                    }
                }
            },
            elements: {
                point: {
                    radius: 0,
                    hoverRadius: 6,
                    hitRadius: 10
                },
                line: {
                    tension: 0.4,
                    borderCapStyle: 'round',
                    borderJoinStyle: 'round'
                }
            },
            animation: {
                duration: 750,
                easing: 'easeInOutQuart'
            }
        }
    });
}

// Load and display main net worth chart
function loadChart(period) {
    const chartContent = document.querySelector('.chart-content');
    chartContent.innerHTML = '<p class="text-center">Loading chart...</p>';
    
    fetch(`/api/networth/${period}?currency=${AppState.currentCurrency}`)
        .then(response => {
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return response.json();
        })
        .then(data => {
            chartContent.innerHTML = '<canvas id="networthChart" width="400" height="200"></canvas>';
            updateChart(data);
            updateGrowth(data);
        })
        .catch(error => {
            console.error('Error loading chart data:', error);
            chartContent.innerHTML = '<p class="text-muted text-center">Chart data unavailable</p>';
        });
}

// Update growth percentage widget
function updateGrowth(data) {
    const growthEl = document.getElementById('growth-percentage');
    if (!growthEl) return;
    
    const netWorthData = data.net_worth || [];
    if (netWorthData.length < 2) {
        growthEl.textContent = '0%';
        growthEl.className = 'metric-value';
        return;
    }
    
    const firstValue = netWorthData[0];
    const lastValue = netWorthData[netWorthData.length - 1];
    
    if (firstValue === 0) {
        growthEl.textContent = '0%';
        growthEl.className = 'metric-value';
        return;
    }
    
    const growth = ((lastValue - firstValue) / Math.abs(firstValue)) * 100;
    
    // Display rounded percentage
    const growthRounded = Math.round(growth);
    const growthText = (growth >= 0 ? '+' : '') + growthRounded + '%';
    
    // Store exact value in tooltip
    const growthExact = (growth >= 0 ? '+' : '') + growth.toFixed(2) + '%';
    
    growthEl.textContent = growthText;
    growthEl.title = growthExact;
    growthEl.className = 'metric-value ' + (growth >= 0 ? 'text-success' : 'text-danger');
}

// Update main net worth chart with new data
function updateChart(data) {
    const ctx = document.getElementById('networthChart').getContext('2d');
    
    if (AppState.chart) {
        AppState.chart.destroy();
    }
    
    const currentTheme = window.getCurrentTheme ? window.getCurrentTheme() : 'light';
    const chartColors = getChartColors(currentTheme);
    
    AppState.chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.dates.map(date => new Date(date).toLocaleDateString()),
            datasets: [{
                label: 'Net Worth',
                data: data.net_worth,
                borderColor: chartColors.primary,
                backgroundColor: chartColors.primaryBg,
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 6,
                pointBackgroundColor: chartColors.primary,
                pointBorderColor: chartColors.bg,
                pointBorderWidth: 2
            }]
        },
        options: getChartOptions(chartColors)
    });
}

// Get theme-aware chart colors
function getChartColors(theme) {
    const colors = {
        light: {
            primary: '#3b82f6',
            primaryBg: 'rgba(59, 130, 246, 0.1)',
            bg: '#ffffff',
            text: '#0f172a',
            grid: '#f1f5f9',
            border: '#e2e8f0'
        },
        dark: {
            primary: '#60a5fa',
            primaryBg: 'rgba(96, 165, 250, 0.2)',
            bg: '#0f172a',
            text: '#f8fafc',
            grid: '#374151',
            border: '#334155'
        },
        blue: {
            primary: '#0284c7',
            primaryBg: 'rgba(2, 132, 199, 0.1)',
            bg: '#f0f9ff',
            text: '#0c4a6e',
            grid: '#bae6fd',
            border: '#7dd3fc'
        },
        green: {
            primary: '#16a34a',
            primaryBg: 'rgba(22, 163, 74, 0.1)',
            bg: '#f0fdf4',
            text: '#14532d',
            grid: '#bbf7d0',
            border: '#86efac'
        }
    };
    return colors[theme] || colors.light;
}

// Get theme-aware chart options
function getChartOptions(colors) {
    return {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
            intersect: false,
            mode: 'index'
        },
        plugins: {
            legend: { display: false },
            tooltip: {
                backgroundColor: colors.bg,
                titleColor: colors.text,
                bodyColor: colors.text,
                borderColor: colors.border,
                borderWidth: 1,
                cornerRadius: 8,
                padding: 12,
                displayColors: false,
                callbacks: {
                    title: function(tooltipItems) {
                        return new Date(tooltipItems[0].label).toLocaleDateString('en-US', {
                            weekday: 'short',
                            year: 'numeric',
                            month: 'short',
                            day: 'numeric'
                        });
                    },
                    label: function(context) {
                        return 'Net Worth: ' + formatCurrency(context.parsed.y, AppState.currentCurrency);
                    }
                }
            }
        },
        scales: {
            y: {
                beginAtZero: false,
                ticks: {
                    callback: function(value) {
                        return formatCurrency(value, AppState.currentCurrency);
                    },
                    color: colors.text,
                    maxTicksLimit: 8
                },
                grid: {
                    color: colors.grid,
                    borderColor: colors.border,
                    lineWidth: 1
                }
            },
            x: {
                grid: {
                    color: colors.grid,
                    borderColor: colors.border,
                    lineWidth: 1
                },
                ticks: {
                    maxTicksLimit: 8,
                    color: colors.text
                }
            }
        },
        elements: {
            point: {
                radius: 0,
                hoverRadius: 6,
                hitRadius: 10
            },
            line: {
                tension: 0.4,
                borderCapStyle: 'round',
                borderJoinStyle: 'round'
            }
        },
        animation: {
            duration: 750,
            easing: 'easeInOutQuart'
        }
    };
}

// Update charts when theme changes
function updateChartsForTheme() {
    if (AppState.chart) {
        const currentTheme = window.getCurrentTheme ? window.getCurrentTheme() : 'light';
        const chartColors = getChartColors(currentTheme);
        
        AppState.chart.data.datasets[0].borderColor = chartColors.primary;
        AppState.chart.data.datasets[0].backgroundColor = chartColors.primaryBg;
        AppState.chart.data.datasets[0].pointBackgroundColor = chartColors.primary;
        AppState.chart.data.datasets[0].pointBorderColor = chartColors.bg;
        AppState.chart.options = getChartOptions(chartColors);
        AppState.chart.update();
    }
    
    if (AppState.assetChart) {
        const currentTheme = window.getCurrentTheme ? window.getCurrentTheme() : 'light';
        const chartColors = getChartColors(currentTheme);
        
        AppState.assetChart.data.datasets[0].borderColor = chartColors.primary;
        AppState.assetChart.data.datasets[0].backgroundColor = chartColors.primaryBg;
        AppState.assetChart.data.datasets[0].pointBackgroundColor = chartColors.primary;
        AppState.assetChart.data.datasets[0].pointBorderColor = chartColors.bg;
        AppState.assetChart.options.scales.y.ticks.color = chartColors.text;
        AppState.assetChart.options.scales.y.grid.color = chartColors.grid;
        AppState.assetChart.options.scales.y.grid.borderColor = chartColors.border;
        AppState.assetChart.options.scales.x.ticks.color = chartColors.text;
        AppState.assetChart.options.scales.x.grid.color = chartColors.grid;
        AppState.assetChart.options.scales.x.grid.borderColor = chartColors.border;
        AppState.assetChart.update();
    }
}

// Expose functions globally
window.createAssetChart = createAssetChart;
window.loadChart = loadChart;
window.updateGrowth = updateGrowth;
window.updateChart = updateChart;
window.getChartColors = getChartColors;
window.getChartOptions = getChartOptions;
window.updateChartsForTheme = updateChartsForTheme;
