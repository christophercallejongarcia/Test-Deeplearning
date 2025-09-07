// API base URL - use relative path to work from any host
const API_URL = '/api';

// Global state
let currentSessionId = null;

// DOM elements
let chatMessages, chatInput, sendButton, totalCourses, courseCards, newChatButton, showAllOutlinesBtn;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Get DOM elements after page loads
    chatMessages = document.getElementById('chatMessages');
    chatInput = document.getElementById('chatInput');
    sendButton = document.getElementById('sendButton');
    totalCourses = document.getElementById('totalCourses');
    courseCards = document.getElementById('courseCards');
    newChatButton = document.getElementById('newChatButton');
    showAllOutlinesBtn = document.getElementById('showAllOutlinesBtn');
    
    setupEventListeners();
    createNewSession();
    loadCourseStats();
    
    // Initialize theme toggle
    new ThemeToggle();
});

// Event Listeners
function setupEventListeners() {
    // Chat functionality
    sendButton.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
    
    // New Chat button
    newChatButton.addEventListener('click', startNewChat);
    
    // Show All Outlines button
    if (showAllOutlinesBtn) {
        showAllOutlinesBtn.addEventListener('click', showAllCourseOutlines);
    }
    
    // Suggested questions
    document.querySelectorAll('.suggested-item').forEach(button => {
        button.addEventListener('click', (e) => {
            const question = e.target.getAttribute('data-question');
            chatInput.value = question;
            sendMessage();
        });
    });
}


// Chat Functions
async function sendMessage() {
    const query = chatInput.value.trim();
    if (!query) return;

    // Disable input
    chatInput.value = '';
    chatInput.disabled = true;
    sendButton.disabled = true;

    // Add user message
    addMessage(query, 'user');

    // Add loading message - create a unique container for it
    const loadingMessage = createLoadingMessage();
    chatMessages.appendChild(loadingMessage);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
        const response = await fetch(`${API_URL}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                session_id: currentSessionId
            })
        });

        if (!response.ok) throw new Error('Query failed');

        const data = await response.json();
        
        // Update session ID if new
        if (!currentSessionId) {
            currentSessionId = data.session_id;
        }

        // Replace loading message with response
        loadingMessage.remove();
        addMessage(data.answer, 'assistant', data.sources);

    } catch (error) {
        // Replace loading message with error
        loadingMessage.remove();
        addMessage(`Error: ${error.message}`, 'assistant');
    } finally {
        chatInput.disabled = false;
        sendButton.disabled = false;
        chatInput.focus();
    }
}

function createLoadingMessage() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="loading">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    return messageDiv;
}

function addMessage(content, type, sources = null, isWelcome = false) {
    const messageId = Date.now();
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}${isWelcome ? ' welcome-message' : ''}`;
    messageDiv.id = `message-${messageId}`;
    
    // Convert markdown to HTML for assistant messages
    let displayContent = type === 'assistant' ? marked.parse(content) : escapeHtml(content);
    
    // Make all links open in new tab for assistant messages
    if (type === 'assistant') {
        displayContent = makeLinksOpenInNewTab(displayContent);
    }
    
    let html = `<div class="message-content">${displayContent}</div>`;
    
    if (sources && sources.length > 0) {
        // Handle both old string format and new structured format for backward compatibility
        const sourcesHtml = sources.map(source => {
            let sourceItem;
            if (typeof source === 'string') {
                // Old format - just return as text
                sourceItem = source;
            } else if (source.link) {
                // New format with link - create clickable link
                sourceItem = `<a href="${source.link}" target="_blank" rel="noopener noreferrer" class="source-link">${source.display}</a>`;
            } else {
                // New format without link - just return display text
                sourceItem = source.display;
            }
            return `<div class="source-item">${sourceItem}</div>`;
        }).join('');
        
        html += `
            <details class="sources-collapsible">
                <summary class="sources-header">Sources</summary>
                <div class="sources-content">${sourcesHtml}</div>
            </details>
        `;
    }
    
    messageDiv.innerHTML = html;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageId;
}

// Helper function to escape HTML for user messages
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Helper function to make all links open in new tab
function makeLinksOpenInNewTab(html) {
    // Replace all <a> tags to add target="_blank" and rel="noopener noreferrer"
    return html.replace(/<a\s+href="([^"]*)"(?![^>]*target=)/gi, '<a href="$1" target="_blank" rel="noopener noreferrer"');
}

// Removed removeMessage function - no longer needed since we handle loading differently

async function createNewSession() {
    currentSessionId = null;
    chatMessages.innerHTML = '';
    addMessage('Welcome to the Course Materials Assistant! I can help you with questions about courses, lessons and specific content. What would you like to know?', 'assistant', null, true);
}

// Function to handle New Chat button click
function startNewChat() {
    // Clear current session
    currentSessionId = null;
    
    // Clear chat messages
    chatMessages.innerHTML = '';
    
    // Clear input field
    chatInput.value = '';
    
    // Re-enable input if it was disabled
    chatInput.disabled = false;
    sendButton.disabled = false;
    
    // Add welcome message
    addMessage('Welcome to the Course Materials Assistant! I can help you with questions about courses, lessons and specific content. What would you like to know?', 'assistant', null, true);
    
    // Focus on input
    chatInput.focus();
}

// Load course statistics
async function loadCourseStats() {
    try {
        console.log('Loading detailed course stats...');
        const response = await fetch(`${API_URL}/courses/detailed`);
        if (!response.ok) throw new Error('Failed to load course stats');
        
        const data = await response.json();
        console.log('Detailed course data received:', data);
        
        // Update stats in UI
        if (totalCourses) {
            totalCourses.textContent = data.total_courses;
        }
        
        // Update course cards
        if (courseCards) {
            if (data.courses && data.courses.length > 0) {
                courseCards.innerHTML = data.courses
                    .map(course => createCourseCard(course))
                    .join('');
                
                // Add event listeners to outline buttons
                setupCourseCardListeners();
            } else {
                courseCards.innerHTML = '<span class="no-courses">No courses available</span>';
            }
        }
        
    } catch (error) {
        console.error('Error loading course stats:', error);
        // Set default values on error
        if (totalCourses) {
            totalCourses.textContent = '0';
        }
        if (courseCards) {
            courseCards.innerHTML = '<span class="error">Failed to load courses</span>';
        }
    }
}

// Create a course card HTML
function createCourseCard(course) {
    const truncatedTitle = course.title.length > 40 ? 
        course.title.substring(0, 40) + '...' : course.title;
    
    return `
        <div class="course-card" data-course-title="${course.title}">
            <div class="course-card-title" title="${course.title}">${truncatedTitle}</div>
            <div class="course-card-info">
                <span class="course-card-lessons">${course.lesson_count} lessons</span>
                <button class="course-card-outline-btn" data-course-title="${course.title}">
                    Outline
                </button>
            </div>
        </div>
    `;
}

// Setup event listeners for course cards
function setupCourseCardListeners() {
    // Outline buttons
    document.querySelectorAll('.course-card-outline-btn').forEach(button => {
        button.addEventListener('click', (e) => {
            e.stopPropagation();
            const courseTitle = button.getAttribute('data-course-title');
            askForCourseOutline(courseTitle);
        });
    });
    
    // Course card clicks (also trigger outline)
    document.querySelectorAll('.course-card').forEach(card => {
        card.addEventListener('click', (e) => {
            if (!e.target.classList.contains('course-card-outline-btn')) {
                const courseTitle = card.getAttribute('data-course-title');
                askForCourseOutline(courseTitle);
            }
        });
    });
}

// Ask for course outline
function askForCourseOutline(courseTitle) {
    const question = `What is the complete outline of the "${courseTitle}" course?`;
    chatInput.value = question;
    sendMessage();
}

// Show all course outlines
function showAllCourseOutlines() {
    const question = "Show me the complete outlines for all available courses with their titles, course links, and lesson lists.";
    chatInput.value = question;
    sendMessage();
}

// Enhanced Theme Management System
class EnhancedThemeSystem {
    constructor() {
        this.toggleButton = document.getElementById('theme-toggle');
        this.dropdownTrigger = document.getElementById('theme-dropdown-trigger');
        this.dropdown = document.getElementById('theme-dropdown');
        this.dropdownMenu = document.getElementById('theme-dropdown-menu');
        this.currentTheme = this.getStoredTheme() || this.getPreferredTheme();
        this.autoThemeEnabled = this.getStoredTheme() === 'auto' || !this.getStoredTheme();
        
        this.themes = {
            light: { name: 'Light', icon: '☀️' },
            dark: { name: 'Dark', icon: '🌙' },
            auto: { name: 'Auto', icon: '🖥️' },
            'high-contrast': { name: 'High Contrast', icon: '🔲' }
        };
        
        this.init();
    }

    init() {
        this.applyTheme(this.currentTheme);
        this.updateDropdownUI();
        this.addEventListeners();
        this.setupSystemThemeWatcher();
    }

    getStoredTheme() {
        return localStorage.getItem('theme');
    }

    getPreferredTheme() {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    getEffectiveTheme() {
        if (this.currentTheme === 'auto') {
            return this.getPreferredTheme();
        }
        return this.currentTheme;
    }

    setStoredTheme(theme) {
        localStorage.setItem('theme', theme);
        this.autoThemeEnabled = theme === 'auto';
    }

    applyTheme(theme) {
        const effectiveTheme = theme === 'auto' ? this.getPreferredTheme() : theme;
        document.documentElement.setAttribute('data-theme', effectiveTheme);
        this.updateAriaLabel(effectiveTheme);
        this.updateToggleButton(effectiveTheme);
        
        // Announce theme change for screen readers
        this.announceThemeChange(this.themes[theme]?.name || theme);
    }

    updateAriaLabel(theme) {
        const nextTheme = theme === 'dark' ? 'light' : 'dark';
        const label = `Switch to ${nextTheme} mode`;
        if (this.toggleButton) {
            this.toggleButton.setAttribute('aria-label', label);
        }
    }

    updateToggleButton(theme) {
        // Update toggle button visual state based on effective theme
        // This is handled by CSS based on data-theme attribute
    }

    updateDropdownUI() {
        const options = this.dropdownMenu?.querySelectorAll('.theme-option');
        options?.forEach(option => {
            const themeValue = option.dataset.theme;
            option.classList.toggle('active', themeValue === this.currentTheme);
        });
    }

    announceThemeChange(themeName) {
        // Create temporary element for screen reader announcement
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'sr-only';
        announcement.textContent = `Theme changed to ${themeName}`;
        
        document.body.appendChild(announcement);
        setTimeout(() => document.body.removeChild(announcement), 1000);
    }

    toggleTheme() {
        const themes = ['light', 'dark'];
        const currentIndex = themes.indexOf(this.getEffectiveTheme());
        const nextIndex = (currentIndex + 1) % themes.length;
        const newTheme = themes[nextIndex];
        
        this.setTheme(newTheme);
    }

    setTheme(theme) {
        if (!this.themes[theme]) return;
        
        this.currentTheme = theme;
        this.applyTheme(theme);
        this.setStoredTheme(theme);
        this.updateDropdownUI();
        
        // Trigger custom event
        window.dispatchEvent(new CustomEvent('themeChanged', {
            detail: { theme, effectiveTheme: this.getEffectiveTheme() }
        }));
    }

    openDropdown() {
        this.dropdown?.classList.add('open');
        this.dropdownTrigger?.setAttribute('aria-expanded', 'true');
        
        // Focus first option
        const firstOption = this.dropdownMenu?.querySelector('.theme-option');
        firstOption?.focus();
    }

    closeDropdown() {
        this.dropdown?.classList.remove('open');
        this.dropdownTrigger?.setAttribute('aria-expanded', 'false');
    }

    setupSystemThemeWatcher() {
        // Watch for system theme changes
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        mediaQuery.addEventListener('change', (e) => {
            if (this.currentTheme === 'auto') {
                this.applyTheme('auto');
            }
        });

        // Watch for high contrast preference
        const highContrastQuery = window.matchMedia('(prefers-contrast: high)');
        if (highContrastQuery.matches && !this.getStoredTheme()) {
            this.setTheme('high-contrast');
        }
    }

    addEventListeners() {
        // Toggle button
        if (this.toggleButton) {
            this.toggleButton.addEventListener('click', () => {
                this.toggleTheme();
            });

            this.toggleButton.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.toggleTheme();
                }
            });
        }

        // Dropdown trigger
        if (this.dropdownTrigger) {
            this.dropdownTrigger.addEventListener('click', (e) => {
                e.stopPropagation();
                if (this.dropdown?.classList.contains('open')) {
                    this.closeDropdown();
                } else {
                    this.openDropdown();
                }
            });

            this.dropdownTrigger.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.openDropdown();
                } else if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    this.openDropdown();
                }
            });
        }

        // Theme options
        const options = this.dropdownMenu?.querySelectorAll('.theme-option');
        options?.forEach((option, index) => {
            option.setAttribute('tabindex', '0');
            option.setAttribute('role', 'menuitem');
            
            option.addEventListener('click', () => {
                const theme = option.dataset.theme;
                this.setTheme(theme);
                this.closeDropdown();
                this.dropdownTrigger?.focus();
            });

            option.addEventListener('keydown', (e) => {
                switch (e.key) {
                    case 'Enter':
                    case ' ':
                        e.preventDefault();
                        option.click();
                        break;
                    case 'ArrowUp':
                        e.preventDefault();
                        const prevOption = option.previousElementSibling || 
                                         this.dropdownMenu?.lastElementChild;
                        prevOption?.focus();
                        break;
                    case 'ArrowDown':
                        e.preventDefault();
                        const nextOption = option.nextElementSibling || 
                                         this.dropdownMenu?.firstElementChild;
                        nextOption?.focus();
                        break;
                    case 'Escape':
                        this.closeDropdown();
                        this.dropdownTrigger?.focus();
                        break;
                }
            });
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.dropdown?.contains(e.target)) {
                this.closeDropdown();
            }
        });

        // Keyboard navigation for dropdown
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.dropdown?.classList.contains('open')) {
                this.closeDropdown();
                this.dropdownTrigger?.focus();
            }
        });

        // Handle focus events for better accessibility
        if (this.toggleButton) {
            this.toggleButton.addEventListener('focus', () => {
                this.toggleButton.style.transform = 'translateY(-1px)';
            });

            this.toggleButton.addEventListener('blur', () => {
                this.toggleButton.style.transform = '';
            });
        }
    }
}

// Legacy ThemeToggle class for backward compatibility
class ThemeToggle extends EnhancedThemeSystem {
    constructor() {
        super();
    }
}