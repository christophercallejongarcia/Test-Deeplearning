class ThemeToggle {
    constructor() {
        this.toggleButton = document.getElementById('theme-toggle');
        this.currentTheme = this.getStoredTheme() || this.getPreferredTheme();
        
        this.init();
    }

    init() {
        this.applyTheme(this.currentTheme);
        this.addEventListeners();
    }

    getStoredTheme() {
        return localStorage.getItem('theme');
    }

    getPreferredTheme() {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    setStoredTheme(theme) {
        localStorage.setItem('theme', theme);
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        this.updateAriaLabel(theme);
    }

    updateAriaLabel(theme) {
        const label = theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode';
        this.toggleButton.setAttribute('aria-label', label);
    }

    toggleTheme() {
        const newTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
        this.currentTheme = newTheme;
        this.applyTheme(newTheme);
        this.setStoredTheme(newTheme);
    }

    addEventListeners() {
        // Click event
        this.toggleButton.addEventListener('click', () => {
            this.toggleTheme();
        });

        // Keyboard accessibility
        this.toggleButton.addEventListener('keydown', (e) => {
            // Support Enter and Space keys
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.toggleTheme();
            }
        });

        // Listen for system theme changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            // Only update if user hasn't manually set a preference
            if (!this.getStoredTheme()) {
                const newTheme = e.matches ? 'dark' : 'light';
                this.currentTheme = newTheme;
                this.applyTheme(newTheme);
            }
        });

        // Handle focus for better accessibility
        this.toggleButton.addEventListener('focus', () => {
            this.toggleButton.style.transform = 'translateY(-1px)';
        });

        this.toggleButton.addEventListener('blur', () => {
            this.toggleButton.style.transform = '';
        });
    }
}

// Initialize the theme toggle when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ThemeToggle();
});

// Export for potential use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemeToggle;
}