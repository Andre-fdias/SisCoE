// static/js/global-system.js
// Sistema Global Automático - SisCoE

class GlobalSpinner {
    constructor() {
        this.spinnerContainer = null;
        this.isShowing = false;
        this.init();
    }

    init() {
        this.createSpinnerStructure();
        this.setupGlobalHandlers();
        console.log('✅ Spinner global inicializado');
    }

    createSpinnerStructure() {
        if (document.getElementById('global-spinner-container')) return;

        const spinnerHTML = `
            <div id="global-spinner-container" class="global-spinner">
                <div class="spinner-scene">
                    <!-- Caminhão de Bombeiros -->
                    <div class="fire-truck">
                        <div class="truck-body">
                            <div class="cabin">
                                <div class="window"></div>
                                <div class="siren">
                                    <div class="siren-light red"></div>
                                    <div class="siren-light blue"></div>
                                </div>
                            </div>
                            <div class="body">
                                <div class="ladder"></div>
                                <div class="water-hose">
                                    <div class="water-nozzle"></div>
                                </div>
                            </div>
                        </div>
                        <div class="wheels">
                            <div class="wheel front"></div>
                            <div class="wheel back"></div>
                        </div>
                    </div>

                    <!-- Prédio em Chamas -->
                    <div class="burning-building">
                        <div class="building">
                            <div class="floor floor-1">
                                <div class="window window-left on-fire"></div>
                                <div class="window window-right"></div>
                            </div>
                            <div class="floor floor-2">
                                <div class="window window-left"></div>
                                <div class="window window-right on-fire"></div>
                            </div>
                            <div class="floor floor-3">
                                <div class="window window-left on-fire"></div>
                                <div class="window window-right"></div>
                            </div>
                            <div class="roof"></div>
                        </div>
                        <div class="flames">
                            <div class="flame flame-1"></div>
                            <div class="flame flame-2"></div>
                            <div class="flame flame-3"></div>
                        </div>
                        <div class="smoke">
                            <div class="smoke-particle smoke-1"></div>
                            <div class="smoke-particle smoke-2"></div>
                            <div class="smoke-particle smoke-3"></div>
                        </div>
                    </div>

                    <!-- Jato de Água -->
                    <div class="water-stream">
                        <div class="water-particle water-1"></div>
                        <div class="water-particle water-2"></div>
                        <div class="water-particle water-3"></div>
                        <div class="water-particle water-4"></div>
                        <div class="water-particle water-5"></div>
                    </div>

                    <!-- Texto de Carregamento -->
                    <div class="loading-text">
                        <div class="loading-dots">
                            <span>CARREGANDO SISCOE</span>
                            <span class="dot dot-1">.</span>
                            <span class="dot dot-2">.</span>
                            <span class="dot dot-3">.</span>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', spinnerHTML);
        this.spinnerContainer = document.getElementById('global-spinner-container');
    }

    setupGlobalHandlers() {
        this.setupAjaxInterceptors();
        this.setupNavigationHandlers();
        this.setupFormHandlers();
        
        window.addEventListener('load', () => {
            setTimeout(() => this.hide(), 1000);
        });

        setTimeout(() => this.hide(), 15000);
        window.addEventListener('error', () => {
            setTimeout(() => this.hide(), 2000);
        });
    }

    setupAjaxInterceptors() {
        const originalFetch = window.fetch;
        const self = this;

        window.fetch = function(...args) {
            if (!args[0]?.includes('keep_alive') && !args[0]?.includes('health')) {
                self.show();
            }
            
            return originalFetch.apply(this, args)
                .then(response => {
                    setTimeout(() => self.hide(), 300);
                    return response;
                })
                .catch(error => {
                    setTimeout(() => self.hide(), 300);
                    throw error;
                });
        };

        const originalXHROpen = XMLHttpRequest.prototype.open;
        const originalXHRSend = XMLHttpRequest.prototype.send;

        XMLHttpRequest.prototype.open = function(...args) {
            this._url = args[1];
            return originalXHROpen.apply(this, args);
        };

        XMLHttpRequest.prototype.send = function(...args) {
            if (!this._url?.includes('keep_alive') && !this._url?.includes('health')) {
                self.show();
            }
            
            this.addEventListener('loadend', function() {
                if (!this._url?.includes('keep_alive') && !this._url?.includes('health')) {
                    setTimeout(() => self.hide(), 300);
                }
            });

            return originalXHRSend.apply(this, args);
        };
    }

    setupNavigationHandlers() {
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a');
            if (link && link.href && !link.href.includes('#') && link.target !== '_blank') {
                const href = link.getAttribute('href');
                if (href && !href.startsWith('javascript:') && !href.startsWith('#')) {
                    setTimeout(() => this.show(), 100);
                }
            }
        });

        window.addEventListener('beforeunload', () => {
            this.show();
        });
    }

    setupFormHandlers() {
        document.addEventListener('submit', (e) => {
            if (!e.target.action?.includes('keep_alive')) {
                setTimeout(() => this.show(), 100);
            }
        });
    }

    show() {
        if (this.spinnerContainer && !this.isShowing) {
            this.isShowing = true;
            this.spinnerContainer.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        }
    }

    hide() {
        if (this.spinnerContainer && this.isShowing) {
            this.isShowing = false;
            this.spinnerContainer.style.display = 'none';
            document.body.style.overflow = '';
        }
    }
}

class GlobalSessionManager {
    constructor() {
        this.config = {
            IDLE_TIMEOUT: 1800, // 30 minutos
            WARNING_TIME: 300,  // 5 minutos
            LOGOUT_URL: '/accounts/logout/',
            KEEP_ALIVE_URL: '/accounts/keep-alive/',
            IS_AUTHENTICATED: this.checkAuthentication()
        };
        
        this.timers = { warning: null, logout: null, countdown: null };
        this.isWarningShown = false;
        this.lastActivity = Date.now();
        this.isInitialized = false;
        this.isEnabled = true;
        this.activityHandler = null;
    }

    checkAuthentication() {
        // Verifica de múltiplas formas se o usuário está autenticado
        return document.body.classList.contains('user-authenticated') ||
               document.querySelector('meta[name="user-authenticated"]')?.content === 'true' ||
               document.querySelector('[data-user-authenticated="true"]') !== null;
    }

    init() {
        if (!this.config.IS_AUTHENTICATED || this.isInitialized) {
            return;
        }
        
        try {
            this.createModalStructure();
            this.setupActivityMonitoring();
            this.startTimers();
            this.isInitialized = true;
            
            console.log('✅ Sistema global de timeout inicializado');
        } catch (error) {
            console.error('❌ Erro ao inicializar sistema de timeout:', error);
            this.disable();
        }
    }

    createModalStructure() {
        if (document.getElementById('globalSessionExpiryModal')) return;

        const modalHTML = `
            <div id="globalSessionExpiryModal" class="global-session-modal">
                <div class="global-session-modal-content">
                    <div class="global-session-header">
                        <div class="global-session-icon">⏰</div>
                        <h3 class="global-session-title">Sessão Prestes a Expirar</h3>
                    </div>
                    
                    <div class="global-session-body">
                        <p class="global-session-message">
                            Sua sessão expirará em <span id="globalSessionCountdown" class="global-session-countdown">300</span> segundos devido à inatividade.
                        </p>
                        <div class="global-session-progress">
                            <div id="globalSessionProgressBar" class="global-session-progress-bar" style="width: 100%"></div>
                        </div>
                        <p class="global-session-warning">
                            Para manter sua sessão ativa, clique em "Continuar".
                        </p>
                    </div>
                    
                    <div class="global-session-footer">
                        <button id="globalSessionContinueBtn" class="global-session-btn global-session-btn-continue">
                            <i class="fas fa-sync-alt mr-2"></i> Continuar
                        </button>
                        <button id="globalSessionLogoutBtn" class="global-session-btn global-session-btn-logout">
                            <i class="fas fa-sign-out-alt mr-2"></i> Sair Agora
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        const container = document.getElementById('global-modals-container') || document.body;
        container.insertAdjacentHTML('beforeend', modalHTML);
        this.setupModalEvents();
    }

    setupModalEvents() {
        const continueBtn = document.getElementById('globalSessionContinueBtn');
        const logoutBtn = document.getElementById('globalSessionLogoutBtn');
        const modal = document.getElementById('globalSessionExpiryModal');

        if (continueBtn) {
            continueBtn.addEventListener('click', () => this.handleContinue());
        }
        
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => this.handleLogout());
        }

        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) this.handleContinue();
            });
        }

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isWarningShown) {
                this.handleContinue();
            }
        });
    }

    setupActivityMonitoring() {
        this.cleanupActivityMonitoring();
        
        const activityEvents = [
            'mousedown', 'mousemove', 'keypress', 'keydown', 'scroll', 
            'touchstart', 'click', 'input', 'focus', 'blur', 'wheel',
            'touchmove', 'touchend', 'touchcancel', 'change', 'submit'
        ];

        const debouncedRecordActivity = this.debounce(() => {
            this.recordActivity();
        }, 1000);

        activityEvents.forEach(event => {
            document.addEventListener(event, debouncedRecordActivity, { passive: true });
        });

        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) this.recordActivity();
        });

        window.addEventListener('focus', () => this.recordActivity());
        this.activityHandler = debouncedRecordActivity;
    }

    cleanupActivityMonitoring() {
        if (this.activityHandler) {
            const activityEvents = [
                'mousedown', 'mousemove', 'keypress', 'keydown', 'scroll', 
                'touchstart', 'click', 'input', 'focus', 'blur', 'wheel',
                'touchmove', 'touchend', 'touchcancel', 'change', 'submit'
            ];
            
            activityEvents.forEach(event => {
                document.removeEventListener(event, this.activityHandler);
            });
        }
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    recordActivity() {
        if (!this.isEnabled || !this.config.IS_AUTHENTICATED) return;
        
        const now = Date.now();
        const timeSinceLastActivity = now - this.lastActivity;
        
        if (timeSinceLastActivity > 1000) {
            this.lastActivity = now;
            this.resetTimers();
        }
    }

    startTimers() {
        if (!this.isEnabled) return;
        
        this.clearAllTimers();
        
        const warningTime = (this.config.IDLE_TIMEOUT - this.config.WARNING_TIME) * 1000;
        
        this.timers.warning = setTimeout(() => {
            this.showWarning();
        }, warningTime);

        this.timers.logout = setTimeout(() => {
            this.handleTimeout();
        }, this.config.IDLE_TIMEOUT * 1000);
    }

    clearAllTimers() {
        Object.values(this.timers).forEach(timer => {
            if (timer) clearTimeout(timer);
        });
        this.timers = { warning: null, logout: null, countdown: null };
    }

    resetTimers() {
        if (!this.isEnabled) return;
        
        if (this.isWarningShown) {
            this.hideWarning();
        }
        this.startTimers();
    }

    showWarning() {
        if (!this.isEnabled || this.isWarningShown || !this.config.IS_AUTHENTICATED) return;
        
        this.isWarningShown = true;
        const modal = document.getElementById('globalSessionExpiryModal');
        if (modal) {
            modal.style.display = 'flex';
            this.startCountdown();
        }
    }

    hideWarning() {
        this.isWarningShown = false;
        const modal = document.getElementById('globalSessionExpiryModal');
        if (modal) {
            modal.style.display = 'none';
        }
        if (this.timers.countdown) {
            clearInterval(this.timers.countdown);
            this.timers.countdown = null;
        }
    }

    startCountdown() {
        let timeLeft = this.config.WARNING_TIME;
        this.updateCountdownDisplay(timeLeft);
        
        this.timers.countdown = setInterval(() => {
            timeLeft--;
            this.updateCountdownDisplay(timeLeft);
            
            if (timeLeft <= 0) {
                this.handleTimeout();
            }
        }, 1000);
    }

    updateCountdownDisplay(timeLeft) {
        const countdownElement = document.getElementById('globalSessionCountdown');
        const progressBar = document.getElementById('globalSessionProgressBar');
        
        if (countdownElement) countdownElement.textContent = timeLeft;
        
        if (progressBar) {
            const progressPercentage = (timeLeft / this.config.WARNING_TIME) * 100;
            progressBar.style.width = `${progressPercentage}%`;
            
            if (timeLeft <= 10) {
                progressBar.style.background = 'linear-gradient(90deg, #e74c3c, #c0392b)';
            } else if (timeLeft <= 30) {
                progressBar.style.background = 'linear-gradient(90deg, #f39c12, #e67e22)';
            } else {
                progressBar.style.background = 'linear-gradient(90deg, #e74c3c, #f39c12)';
            }
        }
    }

    async handleContinue() {
        try {
            if (window.globalSpinner) window.globalSpinner.show();
            await this.keepSessionAlive();
            this.hideWarning();
            this.showTemporaryMessage('✅ Sessão mantida com sucesso!', '#27ae60');
            this.lastActivity = Date.now();
            this.resetTimers();
        } catch (error) {
            console.error('❌ Erro ao manter sessão:', error);
            this.showTemporaryMessage('❌ Erro ao manter sessão', '#e74c3c');
            this.hideWarning();
            this.resetTimers();
        } finally {
            if (window.globalSpinner) window.globalSpinner.hide();
        }
    }

    handleLogout() {
        this.showTemporaryMessage('🚪 Saindo do sistema...', '#3498db', true)
            .then(() => {
                window.location.href = this.config.LOGOUT_URL;
            });
    }

    handleTimeout() {
        this.clearAllTimers();
        this.showTemporaryMessage('⏰ Sessão expirada por inatividade', '#e74c3c', true)
            .then(() => {
                window.location.href = this.config.LOGOUT_URL + '?timeout=true';
            });
    }

    async keepSessionAlive() {
        if (!this.config.KEEP_ALIVE_URL) return Promise.resolve();

        try {
            const csrfToken = this.getCSRFToken();
            if (!csrfToken) throw new Error('Token CSRF não encontrado');

            const response = await fetch(this.config.KEEP_ALIVE_URL, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrfToken, 'Content-Type': 'application/json' },
                credentials: 'same-origin',
                body: JSON.stringify({ action: 'keep_alive', timestamp: new Date().toISOString() })
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            return await response.json();
        } catch (error) {
            console.warn('⚠️ Não foi possível contactar o servidor:', error.message);
            return Promise.resolve();
        }
    }

    showTemporaryMessage(text, color, fullWidth = false) {
        return new Promise(resolve => {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'global-toast';
            messageDiv.style.cssText = `
                ${fullWidth ? 
                    'top: 0; left: 0; width: 100%; text-align: center; padding: 20px;' : 
                    'top: 20px; right: 20px; max-width: 300px; padding: 15px; border-radius: 8px;'
                }
                background: ${color};
                color: white;
                font-weight: 600;
                z-index: 100001;
            `;
            messageDiv.textContent = text;
            
            document.body.appendChild(messageDiv);
            
            setTimeout(() => {
                if (messageDiv.parentNode) messageDiv.remove();
                resolve();
            }, fullWidth ? 2000 : 3000);
        });
    }

    getCSRFToken() {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfToken) return csrfToken.value;
        
        const csrfCookie = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
        if (csrfCookie) return csrfCookie.split('=')[1];
        
        return '';
    }

    disable() {
        this.isEnabled = false;
        this.clearAllTimers();
        this.cleanupActivityMonitoring();
        this.hideWarning();
    }

    destroy() {
        this.disable();
        this.isInitialized = false;
    }
}

// Sistema de Toast Global
class GlobalToastSystem {
    constructor() {
        this.container = null;
        this.init();
    }

    init() {
        this.createContainer();
    }

    createContainer() {
        if (document.getElementById('global-toast-container')) return;

        this.container = document.createElement('div');
        this.container.id = 'global-toast-container';
        this.container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            max-width: 400px;
        `;
        document.body.appendChild(this.container);
    }

    show(message, type = 'info', duration = 5000) {
        const colors = {
            success: '#27ae60',
            error: '#e74c3c',
            warning: '#f39c12',
            info: '#3498db'
        };

        const toast = document.createElement('div');
        toast.style.cssText = `
            background: ${colors[type] || colors.info};
            color: white;
            padding: 15px 20px;
            margin-bottom: 10px;
            border-radius: 8px;
            font-weight: 600;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            animation: slideInRight 0.3s ease-out;
            cursor: pointer;
        `;
        toast.textContent = message;

        toast.addEventListener('click', () => {
            toast.style.animation = 'slideInRight 0.3s ease-out reverse';
            setTimeout(() => toast.remove(), 300);
        });

        this.container.appendChild(toast);

        setTimeout(() => {
            if (toast.parentNode) {
                toast.style.animation = 'slideInRight 0.3s ease-out reverse';
                setTimeout(() => toast.remove(), 300);
            }
        }, duration);
    }
}

// Inicialização Automática do Sistema Global
function initializeGlobalSystem() {
    // Aguarda o DOM estar completamente pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initSystems);
    } else {
        initSystems();
    }

    function initSystems() {
        // Inicializa Toast System primeiro
        window.globalToast = new GlobalToastSystem();
        
        // Inicializa Spinner System
        window.globalSpinner = new GlobalSpinner();
        
        // Inicializa Session Manager com delay
        setTimeout(() => {
            window.globalSessionManager = new GlobalSessionManager();
            window.globalSessionManager.init();
        }, 1000);

        console.log('🚀 SisCoE - Sistema Global Automático Carregado');
        
        // Garante que o spinner seja escondido
        window.addEventListener('load', () => {
            setTimeout(() => window.globalSpinner.hide(), 1000);
        });

        // Fallback para garantir que o spinner seja escondido
        setTimeout(() => window.globalSpinner.hide(), 10000);
    }
}

// API Global para uso em todo o sistema
window.App = {
    showSpinner: function() {
        if (window.globalSpinner) window.globalSpinner.show();
    },
    hideSpinner: function() {
        if (window.globalSpinner) window.globalSpinner.hide();
    },
    showToast: function(message, type = 'info') {
        if (window.globalToast) window.globalToast.show(message, type);
    },
    showAlert: function(message, type = 'INFO', title = '') {
        // Implementação simplificada do modal de alerta
        const alertDiv = document.createElement('div');
        alertDiv.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            z-index: 10000;
            max-width: 400px;
            text-align: center;
        `;
        alertDiv.innerHTML = `
            <h3 style="margin-bottom: 15px; color: #2c3e50;">${title || type}</h3>
            <p style="margin-bottom: 20px; color: #555;">${message}</p>
            <button onclick="this.parentElement.remove()" style="
                padding: 10px 20px;
                background: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                cursor: pointer;
            ">OK</button>
        `;
        document.body.appendChild(alertDiv);
    }
};

// Inicia o sistema automaticamente
initializeGlobalSystem();