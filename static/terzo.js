/* Terzo front end */

console.log("Begin...")

class PageSizeMonitor {
    constructor() {
        this.displayElement = document.getElementById('sizeDisplay');
        this.updateSizeDisplay();
        this.setupEventListeners();
        this.setupMutationObserver();
    }

    updateSizeDisplay() {
        // Document dimensions
        const documentWidth = Math.max(
            document.body.scrollWidth,
            document.body.offsetWidth,
            document.documentElement.clientWidth,
            document.documentElement.scrollWidth,
            document.documentElement.offsetWidth
        );

        const documentHeight = Math.max(
            document.body.scrollHeight,
            document.body.offsetHeight,
            document.documentElement.clientHeight,
            document.documentElement.scrollHeight,
            document.documentElement.offsetHeight
        );

        // Scroll position
        const scrollX = window.pageXOffset || document.documentElement.scrollLeft;
        const scrollY = window.pageYOffset || document.documentElement.scrollTop;

        // Update display
        this.displayElement.innerHTML = `
            <div>Width: ${documentWidth}px</div>
            <div>Height: ${documentHeight}px</div>
            <div>Y Scroll: ${scrollY.toFixed(0)}px</div>
        `;
    }

    setupEventListeners() {
        // Throttle function to limit update frequency yeah!
        let ticking = false;
        const throttleUpdate = () => {
            if (!ticking) {
                requestAnimationFrame(() => {
                    this.updateSizeDisplay();
                    ticking = false;
                });
                ticking = true;
            }
        };

        // Window resize event
        window.addEventListener('resize', throttleUpdate);

        // Scroll event
        window.addEventListener('scroll', throttleUpdate);

        // Orientation change (mobile)
        window.addEventListener('orientationchange', () => {
            // Delay slightly to allow orientation to complete
            setTimeout(throttleUpdate, 100);
        });

        // Zoom / scale changes
        window.addEventListener('wheel', (e) => {
            if (e.ctrlKey) {
                setTimeout(throttleUpdate, 100);
            }
        });

        // Focus events, in the case where the window size changes when switching apps
        window.addEventListener('focus', throttleUpdate);
    }

    setupMutationObserver() {
        // Watch for DOM changes that might affect document size
        const observer = new MutationObserver(() => {
            // Debounce to avoid excessive updates
            clearTimeout(this.mutationTimeout);
            this.mutationTimeout = setTimeout(() => {
                this.updateSizeDisplay();
            }, 100);
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['style', 'class']
        });
    }
}

// Initialize the monitor when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new PageSizeMonitor()
});

// Fallback initialization if DOMContentLoaded already fired
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new PageSizeMonitor();
    });
} else {
    new PageSizeMonitor();
}

console.log("End.")
