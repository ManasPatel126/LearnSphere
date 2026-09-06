/**
 * Server-Sent Events (SSE) Progress Handler
 * Handles real-time streaming updates for learning path generation
 */

let eventSource = null;
let progressModal = null;
let progressBar = null;
let progressMessage = null;
let cancelButton = null;

// Initialize SSE progress handler
function initSSEProgress() {
    // Create progress modal HTML
    const modalHTML = `
        <div id="progress-modal" class="fixed inset-0 bg-black bg-opacity-50 hidden items-center justify-center z-50" style="backdrop-filter: blur(4px);">
            <div class="glass-card p-8 max-w-md w-full mx-4 fade-in">
                <h3 class="text-2xl font-bold text-white mb-6 text-center">Generating Your Learning Path</h3>
                
                <!-- Progress Bar -->
                <div class="mb-6">
                    <div class="w-full bg-gray-700 bg-opacity-50 rounded-full h-4 overflow-hidden">
                        <div id="progress-bar" class="h-4 bg-gradient-to-r from-neon-cyan to-neon-purple rounded-full transition-all duration-500 ease-out" style="width: 0%"></div>
                    </div>
                    <div class="flex justify-between mt-2">
                        <span id="progress-percent" class="text-neon-cyan text-sm font-medium">0%</span>
                        <span class="text-secondary text-sm">Please wait...</span>
                    </div>
                </div>
                
                <!-- Progress Message -->
                <div class="mb-6">
                    <p id="progress-message" class="text-secondary text-center min-h-[24px]">Initializing...</p>
                </div>
                
                <!-- Animated Icon -->
                <div class="flex justify-center mb-6">
                    <div class="relative">
                        <div class="w-16 h-16 border-4 border-neon-cyan border-t-transparent rounded-full animate-spin"></div>
                        <div class="absolute inset-0 flex items-center justify-center">
                            <svg class="w-8 h-8 text-neon-cyan" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                            </svg>
                        </div>
                    </div>
                </div>
                
                <!-- Cancel Button -->
                <button id="cancel-generation" class="w-full px-4 py-2 border border-status-error text-status-error rounded-lg hover:bg-status-error hover:bg-opacity-10 transition">
                    Cancel Generation
                </button>
            </div>
        </div>
    `;
    
    // Add modal to body
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Get references
    progressModal = document.getElementById('progress-modal');
    progressBar = document.getElementById('progress-bar');
    progressMessage = document.getElementById('progress-message');
    cancelButton = document.getElementById('cancel-generation');
    
    // Cancel button handler
    cancelButton.addEventListener('click', cancelGeneration);
}

// Show progress modal
function showProgressModal() {
    if (progressModal) {
        progressModal.classList.remove('hidden');
        progressModal.classList.add('flex');
        resetProgress();
    }
}

// Hide progress modal
function hideProgressModal() {
    if (progressModal) {
        progressModal.classList.add('hidden');
        progressModal.classList.remove('flex');
    }
}

// Reset progress
function resetProgress() {
    if (progressBar) progressBar.style.width = '0%';
    if (progressMessage) progressMessage.textContent = 'Initializing...';
    document.getElementById('progress-percent').textContent = '0%';
}

// Update progress
function updateProgress(progress, message) {
    if (progressBar) {
        progressBar.style.width = `${progress}%`;
    }
    if (progressMessage) {
        progressMessage.textContent = message;
    }
    document.getElementById('progress-percent').textContent = `${progress}%`;
}

// Show error
function showError(errorMessage) {
    if (progressMessage) {
        progressMessage.innerHTML = `<span class="text-status-error">❌ ${errorMessage}</span>`;
    }
    if (progressBar) {
        progressBar.classList.remove('bg-gradient-to-r', 'from-neon-cyan', 'to-neon-purple');
        progressBar.classList.add('bg-status-error');
    }
    
    // Change cancel button to "Close"
    if (cancelButton) {
        cancelButton.textContent = 'Close';
        cancelButton.classList.remove('border-status-error', 'text-status-error');
        cancelButton.classList.add('border-neon-cyan', 'text-neon-cyan');
    }
}

// Cancel generation
function cancelGeneration() {
    if (eventSource) {
        eventSource.close();
        eventSource = null;
    }
    hideProgressModal();
}

// Start SSE streaming
function startSSEGeneration(formData) {
    // Show progress modal
    showProgressModal();
    
    // Close any existing connection
    if (eventSource) {
        eventSource.close();
    }
    
    // Create FormData for POST request
    const urlParams = new URLSearchParams(formData);
    
    // Create EventSource with POST data (using a workaround)
    // Note: EventSource only supports GET, so we'll use fetch with streaming
    fetch('/generate-stream', {
        method: 'POST',
        body: urlParams,
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        }
    }).then(response => {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        function readStream() {
            reader.read().then(({ done, value }) => {
                if (done) {
                    console.log('Stream complete');
                    return;
                }
                
                // Decode the chunk
                const chunk = decoder.decode(value, { stream: true });
                
                // Split by SSE message delimiter
                const messages = chunk.split('\n\n');
                
                messages.forEach(message => {
                    if (message.startsWith('data: ')) {
                        const data = message.substring(6);
                        try {
                            const parsed = JSON.parse(data);
                            handleSSEMessage(parsed);
                        } catch (e) {
                            console.error('Failed to parse SSE message:', data);
                        }
                    }
                });
                
                // Continue reading
                readStream();
            }).catch(error => {
                console.error('Stream error:', error);
                showError('Connection lost. Please try again.');
            });
        }
        
        readStream();
    }).catch(error => {
        console.error('Fetch error:', error);
        showError('Failed to start generation. Please try again.');
    });
}

// Handle SSE message
function handleSSEMessage(data) {
    console.log('SSE message:', data);
    
    // Handle error
    if (data.error) {
        showError(data.error);
        setTimeout(() => {
            hideProgressModal();
        }, 3000);
        return;
    }
    
    // Update progress
    if (data.progress !== undefined) {
        updateProgress(data.progress, data.message || '');
    }
    
    // Handle completion
    if (data.done) {
        // Add success animation
        if (progressBar) {
            progressBar.classList.add('animate-pulse');
        }
        
        // Redirect after short delay
        setTimeout(() => {
            if (data.redirect_url) {
                console.log('Redirecting to:', data.redirect_url);
                window.location.href = data.redirect_url;
            } else {
                console.error('No redirect URL provided');
                hideProgressModal();
            }
        }, 500);
    }
}

// Attach to form submission
document.addEventListener('DOMContentLoaded', function() {
    // Initialize SSE progress
    initSSEProgress();
    
    // Find the generation form
    const form = document.querySelector('form[action="/generate"]');
    
    if (form) {
        // Add checkbox for streaming mode
        const streamingCheckbox = document.createElement('div');
        streamingCheckbox.className = 'flex items-center gap-2 mt-4';
        streamingCheckbox.innerHTML = `
            <input type="checkbox" id="use-streaming" class="w-4 h-4 rounded border-neon-cyan text-neon-cyan focus:ring-neon-cyan" checked>
            <label for="use-streaming" class="text-sm text-secondary cursor-pointer">
                Enable real-time progress updates
            </label>
        `;
        
        // Insert before submit button
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.parentNode.insertBefore(streamingCheckbox, submitButton);
        }
        
        // Intercept form submission
        form.addEventListener('submit', function(e) {
            const useStreaming = document.getElementById('use-streaming')?.checked;
            
            if (useStreaming) {
                e.preventDefault();
                
                // Get form data
                const formData = new FormData(form);
                
                // Start SSE generation
                startSSEGeneration(formData);
            }
            // If not using streaming, let form submit normally
        });
    }
});
