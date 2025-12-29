/**
 * Interest Rate Monitor - Main Application Module
 * Handles AI analysis and news feed functionality
 */

const App = (function() {
    'use strict';

    // Configuration
    const CONFIG = {
        analysisRefreshInterval: 6 * 60 * 60 * 1000, // 6 hours
        newsRefreshInterval: 30 * 60 * 1000, // 30 minutes
        retryDelay: 3000
    };

    // State
    let analysisTimer = null;
    let newsTimer = null;

    /**
     * Initialize the application
     */
    function init() {
        loadAnalysis();
        loadNews();
        loadForecast();
        setupEventListeners();
        startAutoRefresh();
        initChat();
    }

    /**
     * Setup event listeners
     */
    function setupEventListeners() {
        // Refresh analysis button
        const refreshBtn = document.getElementById('refreshAnalysis');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', async function() {
                this.classList.add('loading');
                try {
                    // Clear cache first to get fresh analysis
                    await fetch('/api/v1/cache/clear', { method: 'POST' });
                    // Then load new analysis
                    await loadAnalysis();
                } catch (error) {
                    console.error('Error refreshing analysis:', error);
                } finally {
                    this.classList.remove('loading');
                }
            });
        }
    }

    /**
     * Start auto-refresh timers
     */
    function startAutoRefresh() {
        // Analysis refresh
        analysisTimer = setInterval(loadAnalysis, CONFIG.analysisRefreshInterval);
        
        // News refresh
        newsTimer = setInterval(loadNews, CONFIG.newsRefreshInterval);
    }

    /* =====================
       AI Analysis Module
       ===================== */

    /**
     * Load AI analysis
     */
    async function loadAnalysis() {
        const contentEl = document.getElementById('analysisContent');
        const timeEl = document.getElementById('analysisTime');

        // Show loading state
        if (contentEl) {
            contentEl.innerHTML = `
                <div class="analysis-skeleton">
                    <div class="skeleton-line"></div>
                    <div class="skeleton-line short"></div>
                </div>
            `;
        }

        try {
            const response = await fetch('/api/v1/analysis');
            const result = await response.json();

            if (result.status === 'success' && result.data) {
                // Display analysis
                if (contentEl) {
                    contentEl.textContent = result.data.analysis;
                    contentEl.classList.remove('error');
                }

                // Display generation time
                if (timeEl) {
                    const genTime = new Date(result.data.generated_at);
                    timeEl.textContent = `Generated: ${formatRelativeTime(genTime)}`;
                }
            } else {
                showAnalysisError(contentEl, result.error || 'Failed to load analysis');
            }
        } catch (error) {
            console.error('Error loading analysis:', error);
            showAnalysisError(contentEl, 'Network error');
        }
    }

    /**
     * Show analysis error
     */
    function showAnalysisError(element, message) {
        if (element) {
            element.textContent = '현재 AI 분석을 불러올 수 없습니다. 잠시 후 다시 시도해 주세요.';
            element.classList.add('error');
        }
    }

    /* =====================
       News Feed Module
       ===================== */

    /**
     * Load news feed
     */
    async function loadNews() {
        const usListEl = document.getElementById('usNewsList');
        const krListEl = document.getElementById('krNewsList');

        // Show loading state
        showNewsSkeleton(usListEl);
        showNewsSkeleton(krListEl);

        try {
            const response = await fetch('/api/v1/news?country=all&limit=5');
            const result = await response.json();

            if (result.status === 'success' && result.data) {
                renderNewsColumn(usListEl, result.data.us);
                renderNewsColumn(krListEl, result.data.kr);
            } else {
                showNewsError(usListEl, result.error);
                showNewsError(krListEl, result.error);
            }
        } catch (error) {
            console.error('Error loading news:', error);
            showNewsError(usListEl, 'Network error');
            showNewsError(krListEl, 'Network error');
        }
    }

    /**
     * Show news skeleton loading
     */
    function showNewsSkeleton(element) {
        if (!element) return;
        
        element.innerHTML = `
            <div class="news-skeleton">
                <div class="skeleton-card"></div>
                <div class="skeleton-card"></div>
                <div class="skeleton-card"></div>
            </div>
        `;
    }

    /**
     * Render news column
     */
    function renderNewsColumn(element, newsItems) {
        if (!element) return;

        if (!newsItems || newsItems.length === 0) {
            element.innerHTML = `
                <div class="news-empty">
                    <p>최신 뉴스가 없습니다.</p>
                </div>
            `;
            return;
        }

        const html = newsItems.map(item => createNewsCard(item)).join('');
        element.innerHTML = html;
    }

    /**
     * Create news card HTML
     */
    function createNewsCard(item) {
        const title = escapeHtml(item.title || 'No title');
        const source = escapeHtml(item.source || 'Unknown');
        const snippet = escapeHtml(item.snippet || '');
        const relativeTime = item.relative_time || '';
        const url = item.url || '#';

        return `
            <a href="${url}" class="news-card" target="_blank" rel="noopener noreferrer">
                <h4 class="news-title">${title}</h4>
                <div class="news-meta">
                    <span class="news-source">${source}</span>
                    <span class="news-time">${relativeTime}</span>
                </div>
                ${snippet ? `<p class="news-snippet">${snippet}</p>` : ''}
            </a>
        `;
    }

    /**
     * Show news error
     */
    function showNewsError(element, message) {
        if (!element) return;
        
        element.innerHTML = `
            <div class="news-empty">
                <p>뉴스를 불러올 수 없습니다.</p>
                <button onclick="App.loadNews()" style="
                    margin-top: 10px;
                    padding: 8px 16px;
                    background: var(--google-blue);
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                ">다시 시도</button>
            </div>
        `;
    }

    /* =====================
       Forecast Module
       ===================== */

    // Forecast chart instance
    let forecastChart = null;

    /**
     * Load forecast data
     */
    async function loadForecast() {
        const loadingEl = document.getElementById('forecastChartLoading');
        const sourceEl = document.getElementById('forecastSource');
        const updatedEl = document.getElementById('forecastUpdated');
        const tableBody = document.getElementById('forecastTableBody');

        try {
            const response = await fetch('/api/v1/forecast');
            const result = await response.json();

            if (result.status === 'success' && result.data) {
                const data = result.data;

                // Update meta info
                if (sourceEl) {
                    sourceEl.textContent = `출처: ${data.source || '--'}`;
                }
                if (updatedEl) {
                    updatedEl.textContent = `업데이트: ${data.updated_at || '--'}`;
                }

                // Render chart
                renderForecastChart(data.forecasts);

                // Render table
                renderForecastTable(tableBody, data.forecasts);

                // Hide loading
                if (loadingEl) {
                    loadingEl.classList.add('hidden');
                }
            }
        } catch (error) {
            console.error('Error loading forecast:', error);
            if (loadingEl) {
                loadingEl.innerHTML = '<span>전망 데이터를 불러올 수 없습니다.</span>';
            }
        }
    }

    /**
     * Render forecast chart
     */
    function renderForecastChart(forecasts) {
        const ctx = document.getElementById('forecastChart');
        if (!ctx || !forecasts) return;

        if (forecastChart) {
            forecastChart.destroy();
        }

        const labels = forecasts.map(f => {
            const date = new Date(f.month + '-01');
            return date.toLocaleDateString('ko-KR', { year: '2-digit', month: 'short' });
        });
        const usRates = forecasts.map(f => f.us_rate);
        const krRates = forecasts.map(f => f.kr_rate);

        forecastChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'US 10Y (전망)',
                        data: usRates,
                        borderColor: '#4285F4',
                        backgroundColor: 'rgba(66, 133, 244, 0.1)',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        fill: false,
                        tension: 0.3,
                        pointRadius: 4,
                        pointBackgroundColor: '#4285F4'
                    },
                    {
                        label: 'KR 10Y (전망)',
                        data: krRates,
                        borderColor: '#EA4335',
                        backgroundColor: 'rgba(234, 67, 53, 0.1)',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        fill: false,
                        tension: 0.3,
                        pointRadius: 4,
                        pointBackgroundColor: '#EA4335'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        align: 'end'
                    },
                    tooltip: {
                        backgroundColor: 'rgba(32, 33, 36, 0.95)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        callbacks: {
                            label: function(context) {
                                return ` ${context.dataset.label}: ${context.parsed.y.toFixed(2)}%`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        title: {
                            display: true,
                            text: 'Interest Rate (%)'
                        },
                        ticks: {
                            callback: value => value.toFixed(2) + '%'
                        }
                    }
                }
            }
        });
    }

    /**
     * Render forecast table
     */
    function renderForecastTable(tableBody, forecasts) {
        if (!tableBody || !forecasts) return;

        const html = forecasts.map(f => {
            const spread = ((f.kr_rate - f.us_rate) * 100).toFixed(0);
            const spreadClass = spread >= 0 ? 'spread-positive' : 'spread-negative';
            const spreadSign = spread >= 0 ? '+' : '';

            return `
                <tr>
                    <td>${f.month}</td>
                    <td class="us-value">${f.us_rate.toFixed(2)}%</td>
                    <td class="kr-value">${f.kr_rate.toFixed(2)}%</td>
                    <td class="spread-value ${spreadClass}">${spreadSign}${spread}bp</td>
                </tr>
            `;
        }).join('');

        tableBody.innerHTML = html;
    }

    /* =====================
       Utility Functions
       ===================== */

    /**
     * Format relative time
     */
    function formatRelativeTime(date) {
        const now = new Date();
        const diff = now - date;
        
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);

        if (days > 0) {
            return `${days}일 전`;
        } else if (hours > 0) {
            return `${hours}시간 전`;
        } else if (minutes > 0) {
            return `${minutes}분 전`;
        } else {
            return '방금 전';
        }
    }

    /**
     * Escape HTML special characters
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Cleanup timers
     */
    function destroy() {
        if (analysisTimer) {
            clearInterval(analysisTimer);
        }
        if (newsTimer) {
            clearInterval(newsTimer);
        }
    }

    /* =====================
       Chat Module
       ===================== */

    /**
     * Initialize chat widget
     */
    function initChat() {
        const chatWidget = document.getElementById('chatWidget');
        const chatToggle = document.getElementById('chatToggle');
        const chatInput = document.getElementById('chatInput');
        const chatSend = document.getElementById('chatSend');

        if (!chatWidget || !chatToggle) return;

        // Toggle chat window
        chatToggle.addEventListener('click', function() {
            chatWidget.classList.toggle('open');
            if (chatWidget.classList.contains('open')) {
                chatInput.focus();
            }
        });

        // Send message on button click
        if (chatSend) {
            chatSend.addEventListener('click', sendChatMessage);
        }

        // Send message on Enter key
        if (chatInput) {
            chatInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendChatMessage();
                }
            });
        }
    }

    /**
     * Send chat message
     */
    async function sendChatMessage() {
        const chatInput = document.getElementById('chatInput');
        const chatMessages = document.getElementById('chatMessages');
        const chatSend = document.getElementById('chatSend');

        if (!chatInput || !chatMessages) return;

        const message = chatInput.value.trim();
        if (!message) return;

        // Disable input while processing
        chatInput.disabled = true;
        chatSend.disabled = true;

        // Add user message to chat
        addChatMessage(message, 'user');
        chatInput.value = '';

        // Add loading indicator
        const loadingEl = addChatMessage('', 'bot', true);

        try {
            const response = await fetch('/api/v1/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: message })
            });

            const result = await response.json();

            // Remove loading indicator
            if (loadingEl) {
                loadingEl.remove();
            }

            if (result.status === 'success' && result.data) {
                addChatMessage(result.data.response, 'bot');
            } else {
                addChatMessage(result.error || '응답을 받을 수 없습니다.', 'bot');
            }
        } catch (error) {
            console.error('Chat error:', error);
            if (loadingEl) {
                loadingEl.remove();
            }
            addChatMessage('네트워크 오류가 발생했습니다.', 'bot');
        } finally {
            // Re-enable input
            chatInput.disabled = false;
            chatSend.disabled = false;
            chatInput.focus();
        }
    }

    /**
     * Add message to chat
     */
    function addChatMessage(content, sender, isLoading = false) {
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return null;

        const messageEl = document.createElement('div');
        messageEl.className = `chat-message ${sender}${isLoading ? ' loading' : ''}`;

        const contentEl = document.createElement('div');
        contentEl.className = 'message-content';
        contentEl.textContent = content;

        messageEl.appendChild(contentEl);
        chatMessages.appendChild(messageEl);

        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;

        return messageEl;
    }

    // Public API
    return {
        init: init,
        loadAnalysis: loadAnalysis,
        loadNews: loadNews,
        loadForecast: loadForecast,
        initChat: initChat,
        destroy: destroy
    };
})();

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    App.init();
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    App.destroy();
});
