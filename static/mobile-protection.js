/**
 * Mobile-Only Protection System
 * Active in production, disabled in Replit development
 */

// Check if running in Replit - disable protection for development
if (window.location.hostname.includes('replit.dev') || 
    window.location.hostname.includes('replit.app') || 
    window.location.hostname.includes('repl.co')) {
    // Skip protection in Replit environment
    console.log('Mobile protection disabled in Replit environment');
} else {
    // Execute protection in production
    (function() {
        'use strict';
    
    // Comprehensive mobile detection
    function isMobileDevice() {
        // Check user agent for mobile indicators
        const userAgent = navigator.userAgent.toLowerCase();
        const mobileKeywords = [
            'mobile', 'android', 'iphone', 'ipad', 'ipod', 'blackberry', 
            'windows phone', 'opera mini', 'silk', 'kindle'
        ];
        
        const hasMobileKeyword = mobileKeywords.some(keyword => 
            userAgent.includes(keyword)
        );
        
        // Check screen size (mobile typically < 768px width)
        const hasSmallScreen = window.screen.width <= 768 || window.innerWidth <= 768;
        
        // Check for touch capability
        const hasTouchScreen = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
        
        // Check orientation support (mobile feature)
        const hasOrientationSupport = typeof window.orientation !== 'undefined';
        
        // Combined mobile detection
        return hasMobileKeyword || (hasSmallScreen && hasTouchScreen) || hasOrientationSupport;
    }
    
    // Additional desktop detection patterns
    function isDesktopCloner() {
        const userAgent = navigator.userAgent.toLowerCase();
        
        // Common desktop browsers without mobile indicators
        const desktopBrowsers = [
            'chrome', 'firefox', 'safari', 'edge', 'opera'
        ];
        
        const mobileExclusions = [
            'mobile', 'android', 'iphone', 'ipad'
        ];
        
        const hasDesktopBrowser = desktopBrowsers.some(browser => 
            userAgent.includes(browser)
        );
        
        const lacksMobileIndicators = !mobileExclusions.some(mobile => 
            userAgent.includes(mobile)
        );
        
        // Large screen size typical of desktop
        const hasLargeScreen = window.screen.width > 1024 && window.screen.height > 768;
        
        return hasDesktopBrowser && lacksMobileIndicators && hasLargeScreen;
    }
    
    // Check for common scraping tools
    function isScrapingTool() {
        const userAgent = navigator.userAgent.toLowerCase();
        const scrapingTools = [
            'wget', 'curl', 'httrack', 'webzip', 'teleport', 
            'offline explorer', 'web copier', 'sitesuck',
            'python', 'java', 'go-http-client', 'node'
        ];
        
        return scrapingTools.some(tool => userAgent.includes(tool));
    }
    
    // Execute protection immediately
    function executeProtection() {
        if (!isMobileDevice() || isDesktopCloner() || isScrapingTool()) {
            // Clear all content immediately
            document.documentElement.innerHTML = '';
            document.body.innerHTML = '';
            
            // Clear page title and meta data
            document.title = '';
            
            // Remove all stylesheets
            const stylesheets = document.querySelectorAll('link[rel="stylesheet"], style');
            stylesheets.forEach(sheet => sheet.remove());
            
            // Block any further script execution
            window.stop && window.stop();
            
            // Redirect to about:blank after a brief delay
            setTimeout(() => {
                window.location.href = 'about:blank';
            }, 100);
            
            // Return false to stop any further processing
            return false;
        }
        return true;
    }
    
    // Execute protection immediately when script loads
    if (!executeProtection()) {
        return;
    }
    
    // Monitor for window resize (desktop users might resize to mimic mobile)
    let resizeTimeout;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            if (!isMobileDevice() || isDesktopCloner()) {
                executeProtection();
            }
        }, 100);
    });
    
    // Monitor for developer tools opening (common for cloners)
    let devToolsOpen = false;
    const devToolsChecker = setInterval(() => {
        if (window.outerHeight - window.innerHeight > 200 || 
            window.outerWidth - window.innerWidth > 200) {
            if (!devToolsOpen) {
                devToolsOpen = true;
                executeProtection();
            }
        } else {
            devToolsOpen = false;
        }
    }, 1000);
    
    // Block right-click context menu (prevent inspect element)
    document.addEventListener('contextmenu', function(e) {
        if (!isMobileDevice()) {
            e.preventDefault();
            executeProtection();
            return false;
        }
    });
    
    // Block common developer shortcuts
    document.addEventListener('keydown', function(e) {
        // Block F12, Ctrl+Shift+I, Ctrl+Shift+C, Ctrl+U
        if (e.key === 'F12' || 
            (e.ctrlKey && e.shiftKey && (e.key === 'I' || e.key === 'C')) ||
            (e.ctrlKey && e.key === 'u')) {
            e.preventDefault();
            executeProtection();
            return false;
        }
    });
    
    // Additional protection against iframe embedding
    if (window.top !== window.self) {
        executeProtection();
    }
    
    })(); // Close production protection block
}