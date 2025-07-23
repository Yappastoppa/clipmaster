
// Security Management System
class SecurityManager {
    constructor() {
        this.rateLimiter = new Map();
        this.blockedIPs = new Set();
        this.securityLog = [];
        this.adminSessions = new Map();
        this.initSecurity();
    }

    initSecurity() {
        this.setupCSRFProtection();
        this.setupRateLimiting();
        this.setupBotDetection();
        this.setupDataEncryption();
        this.monitorSuspiciousActivity();
    }

    // CSRF Protection
    setupCSRFProtection() {
        this.csrfToken = this.generateSecureToken();
        document.addEventListener('DOMContentLoaded', () => {
            // Add CSRF token to all forms
            const forms = document.querySelectorAll('form');
            forms.forEach(form => {
                const csrfInput = document.createElement('input');
                csrfInput.type = 'hidden';
                csrfInput.name = 'csrf_token';
                csrfInput.value = this.csrfToken;
                form.appendChild(csrfInput);
            });
        });
    }

    // Rate Limiting
    setupRateLimiting() {
        const originalFetch = window.fetch;
        window.fetch = (...args) => {
            const clientIP = this.getClientIP();
            if (this.isRateLimited(clientIP)) {
                throw new Error('Rate limit exceeded');
            }
            return originalFetch.apply(window, args);
        };
    }

    isRateLimited(ip) {
        const now = Date.now();
        const requests = this.rateLimiter.get(ip) || [];
        const recentRequests = requests.filter(time => now - time < 60000); // 1 minute window
        
        if (recentRequests.length >= 100) { // Max 100 requests per minute
            this.logSecurityEvent('RATE_LIMIT_EXCEEDED', ip);
            return true;
        }
        
        recentRequests.push(now);
        this.rateLimiter.set(ip, recentRequests);
        return false;
    }

    // Bot Detection
    setupBotDetection() {
        let mouseMovements = 0;
        let keystrokes = 0;
        let scrollEvents = 0;

        document.addEventListener('mousemove', () => mouseMovements++);
        document.addEventListener('keydown', () => keystrokes++);
        document.addEventListener('scroll', () => scrollEvents++);

        setInterval(() => {
            if (mouseMovements === 0 && keystrokes === 0 && scrollEvents === 0) {
                this.logSecurityEvent('POTENTIAL_BOT_DETECTED', this.getClientIP());
            }
            mouseMovements = keystrokes = scrollEvents = 0;
        }, 30000);
    }

    // Data Encryption
    setupDataEncryption() {
        this.encryptionKey = this.generateEncryptionKey();
    }

    encryptData(data) {
        return btoa(JSON.stringify(data) + this.encryptionKey);
    }

    decryptData(encryptedData) {
        try {
            const decoded = atob(encryptedData);
            return JSON.parse(decoded.replace(this.encryptionKey, ''));
        } catch (error) {
            this.logSecurityEvent('DECRYPTION_FAILED', this.getClientIP());
            return null;
        }
    }

    // Security Monitoring
    monitorSuspiciousActivity() {
        // Monitor for SQL injection attempts
        const originalLocalStorage = localStorage.setItem;
        localStorage.setItem = (key, value) => {
            if (this.containsSQLInjection(value)) {
                this.logSecurityEvent('SQL_INJECTION_ATTEMPT', this.getClientIP());
                return;
            }
            originalLocalStorage.call(localStorage, key, value);
        };

        // Monitor for XSS attempts
        const originalInnerHTML = Element.prototype.innerHTML;
        Object.defineProperty(Element.prototype, 'innerHTML', {
            set: function(value) {
                if (this.containsXSS(value)) {
                    this.logSecurityEvent('XSS_ATTEMPT', this.getClientIP());
                    return;
                }
                originalInnerHTML.call(this, value);
            }
        });
    }

    containsSQLInjection(input) {
        const sqlPatterns = [
            /('|(\')|(\-\-)|(\;)|(\/\*))/i,
            /(union|select|insert|drop|delete|update|create|alter|exec)/i
        ];
        return sqlPatterns.some(pattern => pattern.test(input));
    }

    containsXSS(input) {
        const xssPatterns = [
            /<script[^>]*>.*?<\/script>/gi,
            /javascript:/gi,
            /on\w+\s*=/gi
        ];
        return xssPatterns.some(pattern => pattern.test(input));
    }

    // Admin Security
    validateAdminAccess(username, password, additionalToken) {
        const hashedPassword = this.hashPassword(password);
        const validCredentials = {
            'admin': this.hashPassword('autoparts2024!@#'),
            'superadmin': this.hashPassword('autopartsSUPER2024!@#$%')
        };

        if (validCredentials[username] !== hashedPassword) {
            this.logSecurityEvent('INVALID_ADMIN_LOGIN', this.getClientIP());
            return false;
        }

        if (!this.validateTwoFactor(additionalToken)) {
            this.logSecurityEvent('2FA_FAILED', this.getClientIP());
            return false;
        }

        const sessionId = this.generateSecureToken();
        this.adminSessions.set(sessionId, {
            username,
            loginTime: Date.now(),
            ip: this.getClientIP()
        });

        return sessionId;
    }

    validateTwoFactor(token) {
        // Simplified 2FA - in production, use TOTP
        const validToken = Math.floor(Date.now() / 30000).toString();
        return token === validToken;
    }

    // Utility Functions
    generateSecureToken() {
        const array = new Uint8Array(32);
        crypto.getRandomValues(array);
        return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
    }

    generateEncryptionKey() {
        return this.generateSecureToken().substring(0, 16);
    }

    hashPassword(password) {
        // Simple hash - in production, use bcrypt or similar
        return btoa(password + 'salt123').split('').reverse().join('');
    }

    getClientIP() {
        // In a real environment, get from server
        return 'client_' + Math.random().toString(36).substring(2, 15);
    }

    logSecurityEvent(event, ip, details = {}) {
        const logEntry = {
            timestamp: new Date().toISOString(),
            event,
            ip,
            details,
            userAgent: navigator.userAgent
        };
        
        this.securityLog.push(logEntry);
        console.warn('Security Event:', logEntry);
        
        // Send to admin if critical
        if (['SQL_INJECTION_ATTEMPT', 'XSS_ATTEMPT', 'RATE_LIMIT_EXCEEDED'].includes(event)) {
            this.notifyAdmin(logEntry);
        }
    }

    notifyAdmin(logEntry) {
        // In production, send email/SMS alert
        const notification = {
            type: 'SECURITY_ALERT',
            message: `Security event detected: ${logEntry.event}`,
            timestamp: logEntry.timestamp,
            ip: logEntry.ip
        };
        
        localStorage.setItem('adminNotifications', 
            JSON.stringify([...this.getAdminNotifications(), notification])
        );
    }

    getAdminNotifications() {
        return JSON.parse(localStorage.getItem('adminNotifications') || '[]');
    }

    getSecurityLog() {
        return this.securityLog;
    }
}

// Payment Security Manager
class PaymentSecurity {
    constructor() {
        this.setupPaymentSecurity();
    }

    setupPaymentSecurity() {
        this.validatePaymentData();
        this.setupPCICompliance();
        this.monitorTransactions();
    }

    validatePaymentData() {
        window.processPayment = (paymentData) => {
            if (!this.validateCreditCard(paymentData.cardNumber)) {
                throw new Error('Invalid credit card number');
            }
            
            if (!this.validateCVV(paymentData.cvv)) {
                throw new Error('Invalid CVV');
            }
            
            return this.securePaymentProcess(paymentData);
        };
    }

    validateCreditCard(cardNumber) {
        // Luhn algorithm
        const digits = cardNumber.replace(/\D/g, '');
        let sum = 0;
        let isEven = false;
        
        for (let i = digits.length - 1; i >= 0; i--) {
            let digit = parseInt(digits.charAt(i));
            
            if (isEven) {
                digit *= 2;
                if (digit > 9) digit -= 9;
            }
            
            sum += digit;
            isEven = !isEven;
        }
        
        return sum % 10 === 0;
    }

    validateCVV(cvv) {
        return /^\d{3,4}$/.test(cvv);
    }

    securePaymentProcess(paymentData) {
        // Encrypt payment data
        const encryptedData = this.encryptPaymentData(paymentData);
        
        // Log transaction for admin tracking
        const transactionId = 'TXN_' + Date.now();
        this.logTransaction(transactionId, encryptedData);
        
        return {
            transactionId,
            status: 'PENDING_VERIFICATION',
            message: 'Payment submitted for processing'
        };
    }

    encryptPaymentData(data) {
        // In production, use proper encryption
        return btoa(JSON.stringify({
            ...data,
            cardNumber: data.cardNumber.replace(/\d(?=\d{4})/g, '*'),
            cvv: '***'
        }));
    }

    logTransaction(transactionId, encryptedData) {
        const transactions = JSON.parse(localStorage.getItem('adminTransactions') || '[]');
        transactions.push({
            id: transactionId,
            timestamp: new Date().toISOString(),
            data: encryptedData,
            status: 'PENDING',
            amount: 0 // Will be updated by admin
        });
        localStorage.setItem('adminTransactions', JSON.stringify(transactions));
    }
}

// Initialize Security
const securityManager = new SecurityManager();
const paymentSecurity = new PaymentSecurity();

// Export for use in other files
window.SecurityManager = securityManager;
window.PaymentSecurity = paymentSecurity;
