/**
 * Milestone Progress Tracker
 * Auto-saves milestone completion status to the backend
 */

// Toast notification system
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg z-50 transition-all duration-300 transform translate-x-0 ${
        type === 'success' ? 'bg-neon-green bg-opacity-20 border border-neon-green text-neon-green' : 
        type === 'error' ? 'bg-status-error bg-opacity-20 border border-status-error text-status-error' :
        'bg-neon-cyan bg-opacity-20 border border-neon-cyan text-neon-cyan'
    }`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    // Animate in
    setTimeout(() => toast.classList.add('opacity-100'), 10);
    
    // Remove after 3 seconds
    setTimeout(() => {
        toast.classList.add('opacity-0', 'translate-x-full');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Load saved progress on page load
async function loadProgress() {
    const pathIdElement = document.getElementById('path-id');
    if (!pathIdElement) {
        console.log('No path-id found, skipping progress load');
        return;
    }
    
    const pathId = pathIdElement.value;
    if (!pathId) {
        console.log('Path ID is empty');
        return;
    }
    
    try {
        const response = await fetch(`/api/progress/load/${pathId}`);
        const result = await response.json();
        
        if (result.success && result.data) {
            console.log(`Loaded ${result.data.length} progress records`);
            
            // Restore checkbox states
            result.data.forEach(item => {
                const checkbox = document.querySelector(
                    `.milestone-checkbox[data-milestone="${item.milestone_identifier}"]`
                );
                
                if (checkbox) {
                    if (item.status === 'completed') {
                        checkbox.checked = true;
                        // Add visual indicator
                        const card = checkbox.closest('.bg-white');
                        if (card) {
                            card.classList.add('border-neon-green');
                            card.style.borderWidth = '2px';
                        }
                    }
                }
            });
            
            // Update progress bar
            updateProgressBar();
        }
    } catch (error) {
        console.error('Failed to load progress:', error);
    }
}

// Save progress when checkbox changes
async function saveProgress(checkbox) {
    const pathId = document.getElementById('path-id').value;
    const milestoneIdentifier = checkbox.dataset.milestone;
    const status = checkbox.checked ? 'completed' : 'not_started';
    
    // Disable checkbox during save
    checkbox.disabled = true;
    
    try {
        const response = await fetch('/api/progress/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                path_id: pathId,
                milestone_identifier: milestoneIdentifier,
                status: status
            })
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            showToast('Progress saved ✓', 'success');
            
            // Visual feedback on the card
            const card = checkbox.closest('.bg-white');
            if (card) {
                if (status === 'completed') {
                    card.classList.add('border-neon-green');
                    card.style.borderWidth = '2px';
                } else {
                    card.classList.remove('border-neon-green');
                    card.style.borderWidth = '';
                }
            }
            
            // Update progress bar
            updateProgressBar();
        } else {
            throw new Error(result.message || 'Failed to save progress');
        }
    } catch (error) {
        console.error('Save failed:', error);
        showToast('Failed to save progress', 'error');
        
        // Revert checkbox state
        checkbox.checked = !checkbox.checked;
    } finally {
        checkbox.disabled = false;
    }
}

// Update progress bar based on completed milestones
function updateProgressBar() {
    const checkboxes = document.querySelectorAll('.milestone-checkbox');
    const total = checkboxes.length;
    
    if (total === 0) return;
    
    const completed = Array.from(checkboxes).filter(cb => cb.checked).length;
    const percentage = Math.round((completed / total) * 100);
    
    const progressBar = document.getElementById('progressBar');
    const progressText = progressBar?.parentElement?.querySelector('.text-sm.font-medium');
    
    if (progressBar) {
        progressBar.style.width = `${percentage}%`;
    }
    
    if (progressText) {
        progressText.textContent = `${percentage}%`;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Milestone tracker initialized');
    
    // Load existing progress
    loadProgress();
    
    // Attach event listeners to all milestone checkboxes
    const checkboxes = document.querySelectorAll('.milestone-checkbox');
    console.log(`Found ${checkboxes.length} milestone checkboxes`);
    
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function(e) {
            saveProgress(e.target);
        });
    });
});
