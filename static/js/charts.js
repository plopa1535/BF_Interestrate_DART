/**
 * Interest Rate Charts Module
 * Implements line and bar charts using Chart.js
 */

const RateCharts = (function() {
    'use strict';

    // Chart instances
    let rateChart = null;
    let spreadChart = null;
    let correlationChart = null;

    // Color palette
    const COLORS = {
        usRate: {
            main: '#4285F4',
            light: 'rgba(66, 133, 244, 0.1)',
            border: 'rgba(66, 133, 244, 0.8)'
        },
        krRate: {
            main: '#EA4335',
            light: 'rgba(234, 67, 53, 0.1)',
            border: 'rgba(234, 67, 53, 0.8)'
        },
        spreadPositive: '#34A853',
        spreadNegative: '#EA4335',
        correlationHigh: '#34A853',
        correlationMid: '#FBBC04',
        correlationLow: '#EA4335',
        grid: '#E8EAED',
        text: '#5F6368'
    };

    // Chart.js defaults
    Chart.defaults.font.family = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
    Chart.defaults.font.size = 12;
    Chart.defaults.color = COLORS.text;

    /**
     * Initialize the main rate line chart
     */
    function initRateChart(data) {
        const ctx = document.getElementById('rateChart');
        if (!ctx) return;

        // Destroy existing chart
        if (rateChart) {
            rateChart.destroy();
        }

        const labels = data.map(d => d.date);
        const usRates = data.map(d => d.us_rate);
        const krRates = data.map(d => d.kr_rate);

        rateChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'US 10Y Treasury',
                        data: usRates,
                        borderColor: COLORS.usRate.main,
                        backgroundColor: COLORS.usRate.light,
                        borderWidth: 2.5,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 0,
                        pointHoverRadius: 6,
                        pointHoverBackgroundColor: COLORS.usRate.main,
                        pointHoverBorderColor: '#fff',
                        pointHoverBorderWidth: 2,
                        yAxisID: 'y'
                    },
                    {
                        label: 'KR 10Y Treasury',
                        data: krRates,
                        borderColor: COLORS.krRate.main,
                        backgroundColor: COLORS.krRate.light,
                        borderWidth: 2.5,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 0,
                        pointHoverRadius: 6,
                        pointHoverBackgroundColor: COLORS.krRate.main,
                        pointHoverBorderColor: '#fff',
                        pointHoverBorderWidth: 2,
                        yAxisID: 'y'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        align: 'end',
                        labels: {
                            usePointStyle: true,
                            pointStyle: 'circle',
                            padding: 20,
                            font: {
                                size: 12,
                                weight: '500'
                            }
                        }
                    },
                    tooltip: {
                        enabled: true,
                        backgroundColor: 'rgba(32, 33, 36, 0.95)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        cornerRadius: 8,
                        padding: 12,
                        displayColors: true,
                        boxPadding: 6,
                        callbacks: {
                            title: function(tooltipItems) {
                                const date = new Date(tooltipItems[0].label);
                                return date.toLocaleDateString('ko-KR', {
                                    year: 'numeric',
                                    month: 'long',
                                    day: 'numeric'
                                });
                            },
                            label: function(context) {
                                const label = context.dataset.label || '';
                                const value = context.parsed.y.toFixed(3);
                                return ` ${label}: ${value}%`;
                            },
                            afterBody: function(tooltipItems) {
                                const usRate = tooltipItems[0]?.parsed.y || 0;
                                const krRate = tooltipItems[1]?.parsed.y || 0;
                                const spread = ((krRate - usRate) * 100).toFixed(1);
                                return [`\n Spread: ${spread}bp`];
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'category',
                        grid: {
                            display: false
                        },
                        ticks: {
                            maxTicksLimit: 10,
                            callback: function(value, index) {
                                const date = new Date(this.getLabelForValue(value));
                                return date.toLocaleDateString('ko-KR', {
                                    month: 'short',
                                    day: 'numeric'
                                });
                            }
                        }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Interest Rate (%)',
                            font: { weight: '500' }
                        },
                        grid: {
                            color: COLORS.grid,
                            drawBorder: false
                        },
                        ticks: {
                            callback: value => value.toFixed(2) + '%'
                        }
                    }
                }
            }
        });

        // Hide loading indicator
        hideLoading('rateChartLoading');
    }

    /**
     * Initialize the spread bar chart
     */
    function initSpreadChart(data) {
        const ctx = document.getElementById('spreadChart');
        if (!ctx) return;

        // Destroy existing chart
        if (spreadChart) {
            spreadChart.destroy();
        }

        const labels = data.map(d => d.date);
        const spreads = data.map(d => d.spread);
        const backgroundColors = spreads.map(s => 
            s >= 0 ? COLORS.spreadPositive : COLORS.spreadNegative
        );

        spreadChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Spread (bp)',
                    data: spreads,
                    backgroundColor: backgroundColors,
                    borderColor: backgroundColors,
                    borderWidth: 0,
                    borderRadius: 2,
                    barPercentage: 0.8,
                    categoryPercentage: 0.9
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        enabled: true,
                        backgroundColor: 'rgba(32, 33, 36, 0.95)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        cornerRadius: 8,
                        padding: 12,
                        callbacks: {
                            title: function(tooltipItems) {
                                const date = new Date(tooltipItems[0].label);
                                return date.toLocaleDateString('ko-KR', {
                                    year: 'numeric',
                                    month: 'long',
                                    day: 'numeric'
                                });
                            },
                            label: function(context) {
                                const value = context.parsed.y.toFixed(1);
                                const sign = value >= 0 ? '+' : '';
                                return ` Spread: ${sign}${value}bp`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        grid: {
                            display: false
                        },
                        ticks: {
                            maxTicksLimit: 10,
                            callback: function(value, index) {
                                const date = new Date(this.getLabelForValue(value));
                                return date.toLocaleDateString('ko-KR', {
                                    month: 'short',
                                    day: 'numeric'
                                });
                            }
                        }
                    },
                    y: {
                        grid: {
                            color: COLORS.grid,
                            drawBorder: false
                        },
                        ticks: {
                            callback: value => {
                                const sign = value >= 0 ? '+' : '';
                                return sign + value + 'bp';
                            }
                        }
                    }
                }
            }
        });

        // Hide loading indicator
        hideLoading('spreadChartLoading');
    }

    /**
     * Initialize the correlation bar chart
     */
    function initCorrelationChart(data) {
        const ctx = document.getElementById('correlationChart');
        if (!ctx) return;

        // Destroy existing chart
        if (correlationChart) {
            correlationChart.destroy();
        }

        const labels = data.map(d => d.period_label);
        const correlations = data.map(d => d.correlation);

        // Color based on correlation value
        const backgroundColors = correlations.map(c => {
            if (c >= 0.7) return COLORS.correlationHigh;
            if (c >= 0.3) return COLORS.correlationMid;
            return COLORS.correlationLow;
        });

        correlationChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: '상관계수',
                    data: correlations,
                    backgroundColor: backgroundColors,
                    borderColor: backgroundColors,
                    borderWidth: 0,
                    borderRadius: 4,
                    barPercentage: 0.7,
                    categoryPercentage: 0.8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        enabled: true,
                        backgroundColor: 'rgba(32, 33, 36, 0.95)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        cornerRadius: 8,
                        padding: 12,
                        callbacks: {
                            title: function(tooltipItems) {
                                const idx = tooltipItems[0].dataIndex;
                                const item = data[idx];
                                return `${item.period_start} ~ ${item.period_end}`;
                            },
                            label: function(context) {
                                const value = context.parsed.y.toFixed(3);
                                let interpretation = '';
                                if (value >= 0.7) interpretation = ' (강한 양의 상관)';
                                else if (value >= 0.3) interpretation = ' (약한 양의 상관)';
                                else if (value >= -0.3) interpretation = ' (상관관계 없음)';
                                else if (value >= -0.7) interpretation = ' (약한 음의 상관)';
                                else interpretation = ' (강한 음의 상관)';
                                return ` 상관계수: ${value}${interpretation}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        grid: {
                            display: false
                        },
                        ticks: {
                            font: {
                                size: 11
                            }
                        }
                    },
                    y: {
                        min: -1,
                        max: 1,
                        grid: {
                            color: COLORS.grid,
                            drawBorder: false
                        },
                        ticks: {
                            stepSize: 0.5,
                            callback: value => value.toFixed(1)
                        }
                    }
                }
            }
        });

        // Hide loading indicator
        hideLoading('correlationChartLoading');
    }

    /**
     * Load correlation data and render chart
     */
    async function loadCorrelationChart() {
        showLoading('correlationChartLoading');

        try {
            const response = await fetch('/api/v1/rates/correlation?days=180&window=30');
            const result = await response.json();

            if (result.status === 'success' && result.data && result.data.correlations) {
                initCorrelationChart(result.data.correlations);

                // Update overall correlation value
                const overallEl = document.getElementById('overallCorrelation');
                if (overallEl && result.data.overall_correlation !== undefined) {
                    const corr = result.data.overall_correlation;
                    overallEl.textContent = corr.toFixed(3);

                    // Color based on value
                    if (corr >= 0.7) overallEl.style.color = COLORS.correlationHigh;
                    else if (corr >= 0.3) overallEl.style.color = COLORS.correlationMid;
                    else overallEl.style.color = COLORS.correlationLow;
                }
            } else {
                console.error('Failed to load correlation data:', result.error);
            }
        } catch (error) {
            console.error('Error fetching correlation data:', error);
        }
    }

    /**
     * Hide loading indicator
     */
    function hideLoading(elementId) {
        const loading = document.getElementById(elementId);
        if (loading) {
            loading.classList.add('hidden');
        }
    }

    /**
     * Show loading indicator
     */
    function showLoading(elementId) {
        const loading = document.getElementById(elementId);
        if (loading) {
            loading.classList.remove('hidden');
        }
    }

    /**
     * Update latest rate values in the summary cards
     */
    function updateRateSummary(data) {
        if (!data || data.length === 0) return;

        const latest = data[data.length - 1];
        
        // Update US rate
        const usRateEl = document.getElementById('usRateValue');
        if (usRateEl) {
            usRateEl.textContent = latest.us_rate.toFixed(3) + '%';
        }

        // Update KR rate
        const krRateEl = document.getElementById('krRateValue');
        if (krRateEl) {
            krRateEl.textContent = latest.kr_rate.toFixed(3) + '%';
        }

        // Update spread
        const spreadEl = document.getElementById('spreadValue');
        if (spreadEl) {
            const spread = latest.spread;
            const sign = spread >= 0 ? '+' : '';
            spreadEl.textContent = sign + spread.toFixed(1) + 'bp';
            spreadEl.style.color = spread >= 0 ? COLORS.spreadPositive : COLORS.spreadNegative;
        }
    }

    /**
     * Fetch and render all charts
     */
    async function loadCharts() {
        showLoading('rateChartLoading');
        showLoading('spreadChartLoading');

        try {
            const response = await fetch('/api/v1/rates?days=180');
            const result = await response.json();

            if (result.status === 'success' && result.data && result.data.rates) {
                const rates = result.data.rates;
                
                initRateChart(rates);
                initSpreadChart(rates);
                updateRateSummary(rates);

                // Load correlation chart
                loadCorrelationChart();

                // Update last update time
                const updateEl = document.getElementById('lastUpdate');
                if (updateEl) {
                    const now = new Date();
                    updateEl.textContent = `Last updated: ${now.toLocaleString('ko-KR')}`;
                }
            } else {
                console.error('Failed to load rate data:', result.error);
                showChartError('Failed to load chart data');
            }
        } catch (error) {
            console.error('Error fetching rate data:', error);
            showChartError('Network error loading charts');
        }
    }

    /**
     * Show error message in chart area
     */
    function showChartError(message) {
        hideLoading('rateChartLoading');
        hideLoading('spreadChartLoading');

        const rateLoading = document.getElementById('rateChartLoading');
        if (rateLoading) {
            rateLoading.innerHTML = `
                <div style="color: var(--google-red); text-align: center;">
                    <p>${message}</p>
                    <button onclick="RateCharts.loadCharts()" style="
                        margin-top: 10px;
                        padding: 8px 16px;
                        background: var(--google-blue);
                        color: white;
                        border: none;
                        border-radius: 4px;
                        cursor: pointer;
                    ">Retry</button>
                </div>
            `;
            rateLoading.classList.remove('hidden');
        }
    }

    // Public API
    return {
        init: loadCharts,
        loadCharts: loadCharts,
        loadCorrelationChart: loadCorrelationChart,
        refresh: loadCharts
    };
})();

// Initialize charts when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    RateCharts.init();
});
