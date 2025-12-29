/**
 * DART Insurance Duration Analysis Module
 * 보험사 듀레이션 분석 모듈
 */

const DartAnalysis = (function() {
    'use strict';

    // State
    let equityRateChart = null;
    let durationChart = null;
    let currentCompany = 'kyobo';
    let currentYearCount = 3;

    // API endpoints
    const API_BASE = '/api/v1/dart';

    /**
     * Initialize DART analysis module
     */
    function init() {
        console.log('[DART] Initializing DART analysis module');
        loadCompanies();
        setupEventListeners();
        // Auto-load default analysis on page load
        setTimeout(() => {
            handleAnalyze();
        }, 500);
    }

    /**
     * Setup event listeners
     */
    function setupEventListeners() {
        const analyzeBtn = document.getElementById('dartAnalyzeBtn');
        const companySelect = document.getElementById('dartCompanySelect');
        const yearSelect = document.getElementById('dartYearSelect');

        if (analyzeBtn) {
            analyzeBtn.addEventListener('click', handleAnalyze);
        }

        if (companySelect) {
            companySelect.addEventListener('change', (e) => {
                currentCompany = e.target.value;
            });
        }

        if (yearSelect) {
            yearSelect.addEventListener('change', (e) => {
                currentYearCount = parseInt(e.target.value);
            });
        }
    }

    /**
     * Load company list
     */
    async function loadCompanies() {
        try {
            const response = await fetch(`${API_BASE}/companies`);
            const result = await response.json();

            if (result.status === 'success' && result.data.companies) {
                renderCompanyOptions(result.data.companies);
            }
        } catch (error) {
            console.error('[DART] Error loading companies:', error);
        }
    }

    /**
     * Render company options in select dropdown
     */
    function renderCompanyOptions(companies) {
        const select = document.getElementById('dartCompanySelect');
        if (!select) return;

        select.innerHTML = companies.map(company =>
            `<option value="${company.id}" ${company.id === 'kyobo' ? 'selected' : ''}>${company.name}</option>`
        ).join('');

        currentCompany = 'kyobo';
    }

    /**
     * Handle analyze button click
     */
    async function handleAnalyze() {
        const loadingEl = document.getElementById('dartLoading');
        const resultsEl = document.getElementById('dartResults');
        const errorEl = document.getElementById('dartError');
        const analyzeBtn = document.getElementById('dartAnalyzeBtn');

        // Show loading state
        if (loadingEl) loadingEl.classList.add('active');
        if (errorEl) errorEl.style.display = 'none';
        if (analyzeBtn) analyzeBtn.disabled = true;

        try {
            const response = await fetch(`${API_BASE}/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    company_id: currentCompany,
                    year_count: currentYearCount
                })
            });

            const result = await response.json();

            if (result.status === 'success') {
                renderAnalysisResults(result.data);
            } else {
                throw new Error(result.error || 'Analysis failed');
            }

        } catch (error) {
            console.error('[DART] Analysis error:', error);
            if (errorEl) {
                errorEl.textContent = `분석 실패: ${error.message}`;
                errorEl.style.display = 'block';
            }
        } finally {
            if (loadingEl) loadingEl.classList.remove('active');
            if (analyzeBtn) analyzeBtn.disabled = false;
        }
    }

    /**
     * Render analysis results
     */
    function renderAnalysisResults(data) {
        console.log('[DART] Rendering results:', data);

        // Get latest quarter data
        const lastIdx = data.quarters.length - 1;
        const latestQuarter = data.quarters[lastIdx];
        const latestEquity = data.equity_level[lastIdx];
        const latestRate = data.kr10y_level[lastIdx];
        const equityQoQ = data.equity_qoq[lastIdx];
        const rateChange = data.kr10y_change[lastIdx];

        // Update summary cards
        const latestEquityLabelEl = document.getElementById('dartLatestEquityLabel');
        const latestRateLabelEl = document.getElementById('dartLatestRateLabel');
        const latestEquityEl = document.getElementById('dartLatestEquity');
        const latestRateEl = document.getElementById('dartLatestRate');
        const equityChangeEl = document.getElementById('dartEquityChange');
        const rateChangeEl = document.getElementById('dartRateChange');

        // Update labels with actual quarter
        if (latestEquityLabelEl) {
            latestEquityLabelEl.textContent = `${latestQuarter} 자본총계`;
        }
        if (latestRateLabelEl) {
            latestRateLabelEl.textContent = `${latestQuarter} KR 10Y`;
        }

        if (latestEquityEl) {
            latestEquityEl.textContent = latestEquity !== null
                ? `${latestEquity.toLocaleString()}억원`
                : '--';
        }

        if (latestRateEl) {
            latestRateEl.textContent = latestRate !== null
                ? `${latestRate.toFixed(2)}%`
                : '--';
        }

        if (equityChangeEl) {
            if (equityQoQ !== null && lastIdx > 0) {
                const prevEquity = data.equity_level[lastIdx - 1];
                const equityDiff = latestEquity - prevEquity;
                const sign = equityDiff >= 0 ? '+' : '';
                equityChangeEl.textContent = `${sign}${equityDiff.toLocaleString()}억원`;
                equityChangeEl.style.color = equityDiff >= 0 ? '#34A853' : '#EA4335';
            } else {
                equityChangeEl.textContent = '--';
                equityChangeEl.style.color = '';
            }
        }

        if (rateChangeEl) {
            if (rateChange !== null) {
                const bps = (rateChange * 100).toFixed(2);
                const sign = rateChange >= 0 ? '+' : '';
                rateChangeEl.textContent = `${sign}${bps}bp`;
                rateChangeEl.style.color = rateChange >= 0 ? '#EA4335' : '#4285F4';
            } else {
                rateChangeEl.textContent = '--';
                rateChangeEl.style.color = '';
            }
        }

        // Render charts
        renderEquityRateChart(data);
        renderDurationTimeSeriesChart(data);
    }

    /**
     * Render Chart 1: 자본총계 & 금리 추이 (Dual Axis)
     */
    function renderEquityRateChart(data) {
        const canvas = document.getElementById('dartEquityRateChart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');

        // Destroy existing chart
        if (equityRateChart) {
            equityRateChart.destroy();
        }

        // Create chart
        equityRateChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.quarters,
                datasets: [
                    {
                        label: '자본총계 (억원)',
                        data: data.equity_level,
                        borderColor: '#34A853',
                        backgroundColor: 'rgba(52, 168, 83, 0.1)',
                        borderWidth: 2,
                        tension: 0.4,
                        fill: true,
                        yAxisID: 'y-equity'
                    },
                    {
                        label: 'KR 10Y (%)',
                        data: data.kr10y_level,
                        borderColor: '#EA4335',
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        tension: 0.4,
                        fill: false,
                        yAxisID: 'y-rate'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: '분기'
                        },
                        grid: {
                            display: false
                        }
                    },
                    'y-equity': {
                        type: 'linear',
                        position: 'left',
                        title: {
                            display: true,
                            text: '자본총계 (억원)'
                        },
                        grid: {
                            color: '#E8EAED'
                        }
                    },
                    'y-rate': {
                        type: 'linear',
                        position: 'right',
                        title: {
                            display: true,
                            text: 'KR 10Y 금리 (%)'
                        },
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    /**
     * Render Chart 2: 민감도 분석 (시계열 Bar Chart)
     */
    function renderDurationTimeSeriesChart(data) {
        const canvas = document.getElementById('dartDurationChart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');

        // Destroy existing chart
        if (durationChart) {
            durationChart.destroy();
        }

        // Prepare bar colors based on positive/negative values (KR only)
        const krDurationColors = data.duration.kr10y.series.map(val =>
            val === null ? '#DADCE0' : (val >= 0 ? '#34A853' : '#EA4335')
        );

        // Create chart
        durationChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.quarters,
                datasets: [
                    {
                        label: 'KR 10Y 듀레이션',
                        data: data.duration.kr10y.series,
                        backgroundColor: krDurationColors,
                        borderWidth: 0
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed.y !== null) {
                                    label += context.parsed.y.toFixed(2);
                                }
                                return label;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: '분기'
                        },
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: '민감도'
                        },
                        grid: {
                            color: '#E8EAED'
                        },
                        ticks: {
                            callback: function(value) {
                                return value.toFixed(1);
                            }
                        }
                    }
                }
            }
        });
    }

    // Public API
    return {
        init: init
    };
})();

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', DartAnalysis.init);
} else {
    DartAnalysis.init();
}
