// DOM Elements
document.addEventListener('DOMContentLoaded', function() {
    // Device selection
    const deviceCards = document.querySelectorAll('.device-card');
    const startMigrationBtn = document.getElementById('startMigration');
    const progressFill = document.getElementById('progressFill');
    const progressPercent = document.getElementById('progressPercent');
    const speedValue = document.getElementById('speedValue');
    const timeLeft = document.getElementById('timeLeft');
    const filesCount = document.getElementById('filesCount');
    const fileInput = document.getElementById('file-input');
    const uploadArea = document.querySelector('.upload-area');

    // Device selection functionality
    deviceCards.forEach(card => {
        card.addEventListener('click', function() {
            const parent = this.closest('.device-options');
            parent.querySelectorAll('.device-card').forEach(c => c.classList.remove('active'));
            this.classList.add('active');
            
            // Update UI based on selection
            updateDeviceInfo();
        });
    });

    // File upload handling
    uploadArea.addEventListener('click', () => fileInput.click());
    
    fileInput.addEventListener('change', function(e) {
        const files = e.target.files;
        if (files.length > 0) {
            let totalSize = 0;
            for (let file of files) {
                totalSize += file.size;
            }
            
            const sizeInGB = (totalSize / (1024 * 1024 * 1024)).toFixed(2);
            uploadArea.innerHTML = `
                <i class="fas fa-check-circle" style="color: #4CAF50;"></i>
                <p>${files.length} file${files.length > 1 ? 's' : ''} selected</p>
                <span class="file-info">Total size: ${sizeInGB} GB</span>
            `;
            
            // Update storage check
            checkStorageCapacity(totalSize);
        }
    });

    // Drag and drop functionality
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#6C63FF';
        uploadArea.style.background = 'rgba(108, 99, 255, 0.1)';
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.borderColor = '#6C63FF';
        uploadArea.style.background = 'rgba(108, 99, 255, 0.05)';
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        fileInput.files = e.dataTransfer.files;
        fileInput.dispatchEvent(new Event('change'));
        uploadArea.style.borderColor = '#6C63FF';
        uploadArea.style.background = 'rgba(108, 99, 255, 0.05)';
    });

    // Start Migration Simulation
    startMigrationBtn.addEventListener('click', function() {
        if (!validateMigrationSetup()) {
            showNotification('Please configure source and destination first!', 'warning');
            return;
        }

        this.innerHTML = '<i class="fas fa-sync-alt fa-spin"></i> Migrating...';
        this.disabled = true;
        
        // Simulate migration progress
        simulateMigration();
    });

    // Update device information
    function updateDeviceInfo() {
        const sourceDevice = document.querySelector('.source-section .device-card.active');
        const destDevice = document.querySelector('.destination-section .device-card.active');
        
        // Update storage bar based on selection
        if (destDevice && destDevice.dataset.type === 'phone') {
            updateStorageBar(35);
        } else if (destDevice && destDevice.dataset.type === 'computer') {
            updateStorageBar(65);
        } else if (destDevice && destDevice.dataset.type === 'database') {
            updateStorageBar(42);
        }
    }

    function updateStorageBar(percent) {
        const storageFill = document.querySelector('.storage-fill');
        const storagePercent = document.querySelector('.storage-percent');
        
        storageFill.style.width = `${percent}%`;
        storagePercent.textContent = `${percent}% used`;
    }

    // Check storage capacity
    function checkStorageCapacity(fileSize) {
        const availableStorage = 350 * 1024 * 1024 * 1024; // 350GB in bytes
        const capacityCheck = document.querySelector('.capacity-check');
        
        if (fileSize < availableStorage) {
            capacityCheck.innerHTML = `
                <i class="fas fa-check-circle"></i>
                <span>Sufficient storage available ✓</span>
            `;
            capacityCheck.style.color = '#4CAF50';
            return true;
        } else {
            capacityCheck.innerHTML = `
                <i class="fas fa-exclamation-circle"></i>
                <span>Insufficient storage! Please free up space.</span>
            `;
            capacityCheck.style.color = '#F44336';
            return false;
        }
    }

    // Validate migration setup
    function validateMigrationSetup() {
        const sourceConnected = document.querySelector('.source-connection .btn-connect').classList.contains('connected');
        const destConnected = document.querySelector('.dest-connection .btn-connect').classList.contains('connected');
        const hasFiles = fileInput.files.length > 0;
        
        return sourceConnected && destConnected && hasFiles;
    }

    // Simulate migration progress
    function simulateMigration() {
        let progress = 0;
        let speed = Math.random() * 100 + 50; // Random speed between 50-150 MB/s
        let totalFiles = 5;
        let completedFiles = 0;
        
        const interval = setInterval(() => {
            progress += Math.random() * 5;
            speed += (Math.random() - 0.5) * 10; // Slight speed variation
            
            if (progress > 100) progress = 100;
            if (speed < 20) speed = 20;
            if (speed > 200) speed = 200;
            
            // Update progress bar
            progressFill.style.width = `${progress}%`;
            progressPercent.textContent = `${Math.round(progress)}%`;
            speedValue.textContent = `${Math.round(speed)} MB/s`;
            
            // Calculate time left
            const timeLeftSec = Math.round((100 - progress) * 0.5);
            const minutes = Math.floor(timeLeftSec / 60);
            const seconds = timeLeftSec % 60;
            timeLeft.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
            
            // Update files count
            if (progress >= 20 && completedFiles < 1) completedFiles = 1;
            if (progress >= 50 && completedFiles < 2) completedFiles = 2;
            if (progress >= 75 && completedFiles < 3) completedFiles = 3;
            if (progress >= 90 && completedFiles < 4) completedFiles = 4;
            if (progress >= 100 && completedFiles < 5) completedFiles = 5;
            
            filesCount.textContent = `${completedFiles}/${totalFiles}`;
            
            // Update file list
            updateFileList(completedFiles);
            
            // Complete migration
            if (progress >= 100) {
                clearInterval(interval);
                startMigrationBtn.innerHTML = '<i class="fas fa-check"></i> Migration Complete!';
                startMigrationBtn.style.background = 'linear-gradient(135deg, #4CAF50 0%, #3D8B40 100%)';
                
                showNotification('Migration completed successfully!', 'success');
                
                // Reset after 3 seconds
                setTimeout(() => {
                    startMigrationBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Start Smart Migration <span class="ai-badge">AI-Powered</span>';
                    startMigrationBtn.disabled = false;
                    startMigrationBtn.style.background = 'var(--gradient-primary)';
                }, 3000);
            }
        }, 200);
    }

    function updateFileList(completedFiles) {
        const fileItems = document.querySelectorAll('.file-item');
        fileItems.forEach((item, index) => {
            if (index < completedFiles) {
                item.classList.remove('in-progress', 'pending');
                item.classList.add('completed');
                item.querySelector('.mini-progress')?.remove();
                const checkIcon = document.createElement('i');
                checkIcon.className = 'fas fa-check success-icon';
                item.appendChild(checkIcon);
            } else if (index === completedFiles) {
                item.classList.remove('completed', 'pending');
                item.classList.add('in-progress');
            } else {
                item.classList.remove('completed', 'in-progress');
                item.classList.add('pending');
            }
        });
    }

    // Connect button functionality
    document.querySelectorAll('.btn-connect').forEach(btn => {
        btn.addEventListener('click', function() {
            const ipInput = this.parentElement.querySelector('input[type="text"]');
            
            if (ipInput.value.trim() === '') {
                showNotification('Please enter a valid IP address or URL', 'error');
                return;
            }
            
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Connecting...';
            
            // Simulate connection
            setTimeout(() => {
                this.innerHTML = '<i class="fas fa-plug"></i> Connected';
                this.classList.add('connected');
                this.style.background = '#4CAF50';
                
                showNotification('Successfully connected!', 'success');
            }, 1500);
        });
    });

    // Notification system
    function showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'warning' ? 'exclamation-triangle' : 'exclamation-circle'}"></i>
            <span>${message}</span>
            <button class="notification-close"><i class="fas fa-times"></i></button>
        `;
        
        // Add styles for notification
        const style = document.createElement('style');
        style.textContent = `
            .notification {
                position: fixed;
                top: 20px;
                right: 20px;
                background: white;
                padding: 1rem 1.5rem;
                border-radius: var(--radius-sm);
                box-shadow: var(--shadow-lg);
                display: flex;
                align-items: center;
                gap: 1rem;
                z-index: 10000;
                animation: slideIn 0.3s ease;
                border-left: 4px solid #6C63FF;
            }
            
            .notification.success { border-left-color: #4CAF50; }
            .notification.warning { border-left-color: #FF9800; }
            .notification.error { border-left-color: #F44336; }
            
            .notification i {
                font-size: 1.2rem;
            }
            
            .notification.success i { color: #4CAF50; }
            .notification.warning i { color: #FF9800; }
            .notification.error i { color: #F44336; }
            
            .notification-close {
                background: none;
                border: none;
                color: var(--gray);
                cursor: pointer;
                margin-left: auto;
            }
            
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
        `;
        
        document.head.appendChild(style);
        document.body.appendChild(notification);
        
        // Close button
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        });
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.animation = 'slideOut 0.3s ease';
                setTimeout(() => notification.remove(), 300);
            }
        }, 5000);
    }

    // Mobile menu toggle
    const menuToggle = document.querySelector('.menu-toggle');
    const navMenu = document.querySelector('.nav-menu');
    const navActions = document.querySelector('.nav-actions');
    
    if (menuToggle) {
        menuToggle.addEventListener('click', () => {
            const isVisible = navMenu.style.display === 'flex';
            navMenu.style.display = isVisible ? 'none' : 'flex';
            navActions.style.display = isVisible ? 'none' : 'flex';
            
            if (window.innerWidth <= 768) {
                if (!isVisible) {
                    navMenu.style.flexDirection = 'column';
                    navMenu.style.position = 'absolute';
                    navMenu.style.top = '100%';
                    navMenu.style.left = '0';
                    navMenu.style.right = '0';
                    navMenu.style.background = 'white';
                    navMenu.style.padding = '1rem';
                    navMenu.style.boxShadow = 'var(--shadow)';
                    
                    navActions.style.flexDirection = 'column';
                    navActions.style.position = 'absolute';
                    navActions.style.top = 'calc(100% + 200px)';
                    navActions.style.left = '0';
                    navActions.style.right = '0';
                    navActions.style.background = 'white';
                    navActions.style.padding = '1rem';
                    navActions.style.boxShadow = 'var(--shadow)';
                }
            }
        });
    }

    // Smooth scrolling for navigation links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 80,
                    behavior: 'smooth'
                });
            }
        });
    });

    // Initialize
    updateDeviceInfo();
});

// Add CSS for smooth transitions
const animationStyles = document.createElement('style');
animationStyles.textContent = `
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(animationStyles);
