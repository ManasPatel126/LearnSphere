// Initialize theme immediately to prevent flash
(function() {
    const storedTheme = localStorage.getItem('theme');
    const root = document.documentElement;
    
    if (storedTheme === 'light') {
        root.classList.remove('dark');
    } else {
        // Default to dark theme
        root.classList.add('dark');
    }
})();

document.addEventListener('DOMContentLoaded', function () {
    // Ensure Tailwind uses class strategy
    if (window.tailwind && window.tailwind.config) {
        window.tailwind.config.darkMode = 'class';
    }

    const themeToggleDesktop = document.getElementById('theme-toggle');
    const themeToggleMobile = document.getElementById('theme-toggle-mobile');
    const root = document.documentElement;

    // Helpers to swap icon visibility
    function showDarkIcons() {
        document.querySelectorAll('#theme-toggle-light-icon, #theme-toggle-mobile-light-icon').forEach(el => {
            if (el) el.classList.add('hidden');
        });
        document.querySelectorAll('#theme-toggle-dark-icon, #theme-toggle-mobile-dark-icon').forEach(el => {
            if (el) el.classList.remove('hidden');
        });
    }
    
    function showLightIcons() {
        document.querySelectorAll('#theme-toggle-dark-icon, #theme-toggle-mobile-dark-icon').forEach(el => {
            if (el) el.classList.add('hidden');
        });
        document.querySelectorAll('#theme-toggle-light-icon, #theme-toggle-mobile-light-icon').forEach(el => {
            if (el) el.classList.remove('hidden');
        });
    }

    // Set initial theme and icons
    const storedTheme = localStorage.getItem('theme');
    const isDark = storedTheme !== 'light'; // Default to dark
    
    if (isDark) {
        root.classList.add('dark');
        showDarkIcons();
    } else {
        root.classList.remove('dark');
        showLightIcons();
    }

    function toggleTheme() {
        root.classList.toggle('dark');
        const isDark = root.classList.contains('dark');
        
        if (isDark) {
            localStorage.setItem('theme', 'dark');
            showDarkIcons();
            console.log('Switched to dark mode');
        } else {
            localStorage.setItem('theme', 'light');
            showLightIcons();
            console.log('Switched to light mode');
        }
    }

    if (themeToggleDesktop) {
        themeToggleDesktop.addEventListener('click', function(e) {
            e.preventDefault();
            toggleTheme();
        });
    }
    
    if (themeToggleMobile) {
        themeToggleMobile.addEventListener('click', function(e) {
            e.preventDefault();
            toggleTheme();
        });
    }
    
    console.log('Theme system initialized. Current theme:', root.classList.contains('dark') ? 'dark' : 'light');
});
