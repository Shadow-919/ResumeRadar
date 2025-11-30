// ============================================
// DOM Element References (consolidated to avoid duplicate declarations)
// ============================================
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('resume-input');
const fileNameDisplay = document.getElementById('file-name-display');
const uploadForm = document.getElementById('upload-form');

// ============================================
// BUG FIX: Clear form ONLY when coming from result page
// This fixes the issue where job description persists when returning from result page
// BUT preserves the uploaded file when switching tabs/windows
// ============================================
window.addEventListener('DOMContentLoaded', function () {
    const jobDescField = document.getElementById('job-description');

    // Check if we're coming from the result page (via URL parameter or referrer)
    const urlParams = new URLSearchParams(window.location.search);
    const clearForm = urlParams.get('clear') === 'true';

    // Only clear if explicitly requested (from "New Analysis" button)
    if (clearForm) {
        // Clear job description field
        if (jobDescField) {
            jobDescField.value = '';
        }

        // Clear file input and display
        if (fileInput) {
            fileInput.value = '';
        }
        if (fileNameDisplay) {
            fileNameDisplay.innerHTML = '';
        }

        // Remove the clear parameter from URL to keep it clean
        window.history.replaceState({}, document.title, window.location.pathname);
    }
});

// ============================================
// BUG FIX: Detect browser Back/Forward navigation and clear form
// This prevents stale data from appearing when user navigates back
// ============================================
window.addEventListener('pageshow', function (event) {
    try {
        const jobDesc = document.getElementById('job-description');
        const input = document.getElementById('resume-input');
        const display = document.getElementById('file-name-display');

        // Detect navigation type using feature detection
        const navEntries = typeof performance.getEntriesByType === 'function' ? performance.getEntriesByType('navigation') : null;
        const navType = navEntries && navEntries[0] && navEntries[0].type ? navEntries[0].type : (performance.navigation && performance.navigation.type === 2 ? 'back_forward' : '');

        // Clear form if page was restored from cache or navigated via back/forward
        if (event.persisted || navType === 'back_forward') {
            if (jobDesc) jobDesc.value = '';
            if (input) {
                try { input.value = ''; } catch (e) { /* ignore */ }
                try { input.files = new DataTransfer().files; } catch (e) { /* ignore */ }
            }
            if (display) display.innerHTML = '';
        }
    } catch (err) {
        console.error('pageshow clear handler error', err);
    }
});

// NOTE: Removed visibilitychange handler to prevent clearing on tab switch

// Drag and Drop Functionality

// Prevent default drag behaviors
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, preventDefaults, false);
    document.body.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

// Highlight drop zone when item is dragged over it
['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, highlight, false);
});

['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, unhighlight, false);
});

function highlight(e) {
    dropZone.classList.add('dragover');
}

function unhighlight(e) {
    dropZone.classList.remove('dragover');
}

// Handle dropped files
dropZone.addEventListener('drop', handleDrop, false);

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;

    if (files.length > 0) {
        handleFiles(files);
    }
}

// Handle file selection via click - FIXED to prevent interference with interactive elements
dropZone.addEventListener('click', (e) => {
    // Ignore clicks on interactive controls (textarea, input, label, button, a)
    if (e.target.closest && e.target.closest('textarea, input, label, button, a')) {
        return;
    }
    // Only trigger file input if not clicking on the input itself
    if (e.target !== fileInput && fileInput) {
        fileInput.click();
    }
});

// ============================================
// BUG FIX: Improved file input change handler
// Ensures file display is ALWAYS updated immediately
// ============================================
fileInput.addEventListener('change', (e) => {
    const files = e.target.files;
    if (files.length > 0) {
        // Force immediate update with defensive checks
        setTimeout(() => {
            handleFiles(files);
        }, 0);
    } else {
        // Clear display if no file selected
        if (fileNameDisplay) {
            fileNameDisplay.innerHTML = '';
        }
    }
});

// ============================================
// BUG FIX: Enhanced handleFiles function
// Added defensive checks and immediate DOM updates
// ============================================
function handleFiles(files) {
    if (!files || files.length === 0) {
        console.warn('No files provided to handleFiles');
        return;
    }

    const file = files[0];

    // Validate file type
    const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    const allowedExtensions = ['.pdf', '.docx'];

    const fileName = file.name.toLowerCase();
    const isValidType = allowedTypes.includes(file.type) ||
        allowedExtensions.some(ext => fileName.endsWith(ext));

    if (!isValidType) {
        alert('Please upload a PDF or DOCX file only.');
        fileInput.value = ''; // Clear invalid file
        if (fileNameDisplay) {
            fileNameDisplay.innerHTML = '';
        }
        return;
    }

    // Update file input - defensive check
    try {
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        fileInput.files = dataTransfer.files;
    } catch (error) {
        console.error('Error updating file input:', error);
    }

    // ============================================
    // BUG FIX: Immediate and guaranteed display update
    // Using requestAnimationFrame to ensure DOM is ready
    // ============================================
    const updateDisplay = () => {
        if (!fileNameDisplay) {
            console.error('File name display element not found');
            return;
        }

        const displayHTML = `
            <div class="flex justify-center">
                <div class="file-uploaded-card rounded-xl px-4 py-3 inline-flex items-center gap-3">
                    <div class="flex items-center gap-2 text-green-400 font-medium">
                        <i class="fas fa-check-circle"></i>
                        <span>${file.name}</span>
                    </div>
                    <button type="button" onclick="removeFile(event)" class="remove-file-btn text-gray-400 hover:text-red-500 transition-colors">
                        <i class="fas fa-times text-xl"></i>
                    </button>
                </div>
            </div>
        `;
        fileNameDisplay.innerHTML = displayHTML;

        // Log for debugging
        console.log('File display updated:', file.name);
    };

    // Update immediately and also after next frame to ensure visibility
    updateDisplay();
    requestAnimationFrame(updateDisplay);
}

// Function to remove uploaded file
function removeFile(event) {
    if (event) {
        event.stopPropagation(); // Prevent triggering drop zone click
        event.preventDefault();
    }
    // Clear the file input robustly
    if (fileInput) {
        fileInput.value = ''; // Clear the file input
        // Extra safety for browsers that don't fully reset with value = ''
        try {
            fileInput.files = new DataTransfer().files;
        } catch (e) {
            // Ignore if DataTransfer not supported
        }
    }
    if (fileNameDisplay) {
        fileNameDisplay.innerHTML = ''; // Clear the display
    }
}


// CRITICAL FIX: ABSOLUTE validation that CANNOT be bypassed
uploadForm.addEventListener('submit', function (e) {
    // Get current file input state
    const files = fileInput.files;
    const jobDescription = document.getElementById('job-description').value.trim();

    // FIRST: Check if resume file is selected
    if (!files || files.length === 0) {
        // STOP everything
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();

        // Show alert
        alert('Resume not uploaded. Please upload it.');

        // Focus on drop zone to guide user
        dropZone.scrollIntoView({ behavior: 'smooth', block: 'center' });

        // Absolutely prevent submission
        return false;
    }

    // SECOND: Check if job description is filled
    if (!jobDescription) {
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();

        alert('Please enter a job description');
        document.getElementById('job-description').focus();

        return false;
    }

    // All validations passed - allow form submission
    return true;
}, true); // Use capture phase to ensure this runs first
