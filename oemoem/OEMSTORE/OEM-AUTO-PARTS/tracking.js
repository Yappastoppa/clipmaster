
// Advanced User Tracking System
class UserTracker {
    constructor() {
        this.sessionId = this.generateSessionId();
        this.userId = localStorage.getItem('userId') || this.generateUserId();
        this.trackingData = JSON.parse(localStorage.getItem('trackingData') || '[]');
        this.initTracking();
    }

    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substring(2, 15);
    }

    generateUserId() {
        const userId = 'user_' + Date.now() + '_' + Math.random().toString(36).substring(2, 15);
        localStorage.setItem('userId', userId);
        return userId;
    }

    initTracking() {
        this.trackPageView();
        this.trackUserInteractions();
        this.trackDeviceInfo();
        this.trackLocationData();
        this.setupRealTimeTracking();
    }

    trackPageView() {
        const pageData = {
            type: 'PAGE_VIEW',
            userId: this.userId,
            sessionId: this.sessionId,
            timestamp: new Date().toISOString(),
            page: window.location.pathname,
            title: document.title,
            referrer: document.referrer,
            userAgent: navigator.userAgent
        };
        this.saveTrackingData(pageData);
    }

    trackUserInteractions() {
        // Track clicks
        document.addEventListener('click', (e) => {
            this.saveTrackingData({
                type: 'CLICK',
                userId: this.userId,
                sessionId: this.sessionId,
                timestamp: new Date().toISOString(),
                element: e.target.tagName,
                className: e.target.className,
                id: e.target.id,
                text: e.target.textContent?.substring(0, 100),
                coordinates: { x: e.clientX, y: e.clientY }
            });
        });

        // Track form submissions
        document.addEventListener('submit', (e) => {
            this.saveTrackingData({
                type: 'FORM_SUBMIT',
                userId: this.userId,
                sessionId: this.sessionId,
                timestamp: new Date().toISOString(),
                formId: e.target.id,
                formAction: e.target.action
            });
        });

        // Track search queries
        const searchInputs = document.querySelectorAll('input[type="search"], #search-bar');
        searchInputs.forEach(input => {
            input.addEventListener('input', (e) => {
                this.saveTrackingData({
                    type: 'SEARCH_QUERY',
                    userId: this.userId,
                    sessionId: this.sessionId,
                    timestamp: new Date().toISOString(),
                    query: e.target.value,
                    queryLength: e.target.value.length
                });
            });
        });
    }

    trackDeviceInfo() {
        const deviceData = {
            type: 'DEVICE_INFO',
            userId: this.userId,
            sessionId: this.sessionId,
            timestamp: new Date().toISOString(),
            screen: {
                width: screen.width,
                height: screen.height,
                colorDepth: screen.colorDepth
            },
            viewport: {
                width: window.innerWidth,
                height: window.innerHeight
            },
            platform: navigator.platform,
            language: navigator.language,
            cookieEnabled: navigator.cookieEnabled,
            onlineStatus: navigator.onLine
        };
        this.saveTrackingData(deviceData);
    }

    trackLocationData() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    this.saveTrackingData({
                        type: 'LOCATION_DATA',
                        userId: this.userId,
                        sessionId: this.sessionId,
                        timestamp: new Date().toISOString(),
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude,
                        accuracy: position.coords.accuracy
                    });
                },
                (error) => {
                    this.saveTrackingData({
                        type: 'LOCATION_ERROR',
                        userId: this.userId,
                        sessionId: this.sessionId,
                        timestamp: new Date().toISOString(),
                        error: error.message
                    });
                }
            );
        }
    }

    setupRealTimeTracking() {
        // Track time spent on page
        let startTime = Date.now();
        window.addEventListener('beforeunload', () => {
            const timeSpent = Date.now() - startTime;
            this.saveTrackingData({
                type: 'TIME_SPENT',
                userId: this.userId,
                sessionId: this.sessionId,
                timestamp: new Date().toISOString(),
                timeSpent: timeSpent,
                page: window.location.pathname
            });
        });

        // Track scroll behavior
        let scrollData = [];
        window.addEventListener('scroll', () => {
            scrollData.push({
                timestamp: Date.now(),
                scrollY: window.scrollY,
                scrollPercent: Math.round((window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100)
            });

            // Save scroll data periodically
            if (scrollData.length >= 10) {
                this.saveTrackingData({
                    type: 'SCROLL_BEHAVIOR',
                    userId: this.userId,
                    sessionId: this.sessionId,
                    timestamp: new Date().toISOString(),
                    scrollData: scrollData
                });
                scrollData = [];
            }
        });

        // Track mouse movements (sampled)
        let mouseData = [];
        document.addEventListener('mousemove', (e) => {
            if (Math.random() < 0.01) { // Sample 1% of movements
                mouseData.push({
                    timestamp: Date.now(),
                    x: e.clientX,
                    y: e.clientY
                });

                if (mouseData.length >= 20) {
                    this.saveTrackingData({
                        type: 'MOUSE_MOVEMENT',
                        userId: this.userId,
                        sessionId: this.sessionId,
                        timestamp: new Date().toISOString(),
                        movements: mouseData
                    });
                    mouseData = [];
                }
            }
        });
    }

    // E-commerce specific tracking
    trackPurchaseIntent(productId, productName, price) {
        this.saveTrackingData({
            type: 'PURCHASE_INTENT',
            userId: this.userId,
            sessionId: this.sessionId,
            timestamp: new Date().toISOString(),
            productId: productId,
            productName: productName,
            price: price,
            stage: 'VIEW_PRODUCT'
        });
    }

    trackAddToCart(productId, productName, price, quantity) {
        this.saveTrackingData({
            type: 'ADD_TO_CART',
            userId: this.userId,
            sessionId: this.sessionId,
            timestamp: new Date().toISOString(),
            productId: productId,
            productName: productName,
            price: price,
            quantity: quantity
        });
    }

    trackCheckoutStep(step, data = {}) {
        this.saveTrackingData({
            type: 'CHECKOUT_STEP',
            userId: this.userId,
            sessionId: this.sessionId,
            timestamp: new Date().toISOString(),
            step: step,
            data: data
        });
    }

    trackPurchase(transactionId, total, items) {
        this.saveTrackingData({
            type: 'PURCHASE_COMPLETE',
            userId: this.userId,
            sessionId: this.sessionId,
            timestamp: new Date().toISOString(),
            transactionId: transactionId,
            total: total,
            items: items
        });
    }

    saveTrackingData(data) {
        this.trackingData.push(data);
        localStorage.setItem('trackingData', JSON.stringify(this.trackingData));
        
        // Keep only last 1000 entries to prevent storage overflow
        if (this.trackingData.length > 1000) {
            this.trackingData = this.trackingData.slice(-1000);
            localStorage.setItem('trackingData', JSON.stringify(this.trackingData));
        }

        // Send to admin dashboard in real-time for critical events
        if (['PURCHASE_COMPLETE', 'ADD_TO_CART', 'FORM_SUBMIT'].includes(data.type)) {
            this.notifyAdmin(data);
        }
    }

    notifyAdmin(data) {
        const adminNotifications = JSON.parse(localStorage.getItem('adminUserActivity') || '[]');
        adminNotifications.push({
            ...data,
            priority: 'HIGH'
        });
        localStorage.setItem('adminUserActivity', JSON.stringify(adminNotifications));
    }

    getUserAnalytics() {
        return {
            userId: this.userId,
            sessionId: this.sessionId,
            totalEvents: this.trackingData.length,
            sessionStart: this.trackingData[0]?.timestamp,
            lastActivity: this.trackingData[this.trackingData.length - 1]?.timestamp,
            eventTypes: this.getEventTypeCounts(),
            deviceInfo: this.trackingData.find(d => d.type === 'DEVICE_INFO'),
            locationData: this.trackingData.find(d => d.type === 'LOCATION_DATA')
        };
    }

    getEventTypeCounts() {
        const counts = {};
        this.trackingData.forEach(event => {
            counts[event.type] = (counts[event.type] || 0) + 1;
        });
        return counts;
    }

    exportTrackingData() {
        return {
            analytics: this.getUserAnalytics(),
            rawData: this.trackingData
        };
    }
}

// Initialize tracking
const userTracker = new UserTracker();

// Export for global access
window.UserTracker = userTracker;

// Enhanced tracking for specific actions
window.trackProductView = (productId, productName, price) => {
    userTracker.trackPurchaseIntent(productId, productName, price);
};

window.trackAddToCart = (productId, productName, price, quantity) => {
    userTracker.trackAddToCart(productId, productName, price, quantity);
};

window.trackCheckoutStep = (step, data) => {
    userTracker.trackCheckoutStep(step, data);
};

window.trackPurchase = (transactionId, total, items) => {
    userTracker.trackPurchase(transactionId, total, items);
};
