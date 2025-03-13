// static/js/main.js

// Connect to WebSocket
let socket;
let clickData = {
    totalClicks: 0,
    casinos: {},
    history: [],
    lastClicked: null
};

let continuousMode = false;
let webSocketWorking = false;
function connectWebSocket() {
    // Check if socket already exists and is connected
    try {
        // Check if socket already exists and is connected
        if (socket && socket.connected) {
            return;
        }

        // Create socket connection with the correct path
        socket = io.connect(window.location.origin, {
            path: '/socket.io',
            reconnectionAttempts: 3,
            timeout: 5000
        });

        // Socket event handlers
        socket.on('connect', function () {
            console.log('Connected to WebSocket');
            webSocketWorking = true;
            socket.emit('request_status');
        });

        socket.on('connect_error', function (error) {
            console.error('WebSocket connection error:', error);
            webSocketWorking = false;
            startPolling();
        });

        // Rest of your socket event handlers...
    } catch (e) {
        console.error('Error setting up WebSocket:', e);
        webSocketWorking = false;
        startPolling();
    }

    socket.on('status_update', function (data) {
        console.log('Status update received:', data);

        // Update continuous mode
        continuousMode = data.continuous || false;
        updateContinuousModeUI();

        // Update status badge
        const statusBadge = document.getElementById('status-badge');
        const automationStatus = document.getElementById('automation-status');

        if (data.running) {
            if (statusBadge) {
                statusBadge.textContent = 'Running';
                statusBadge.className = 'badge bg-success';
            }

            if (automationStatus) {
                automationStatus.textContent = 'Automation is running' +
                    (continuousMode ? ' (Continuous Mode)' : '');
                automationStatus.className = 'alert alert-success';
            }

            // Enable stop button, disable start button
            const startButton = document.getElementById('start-button');
            const stopButton = document.getElementById('stop-button');
            if (startButton) startButton.disabled = true;
            if (stopButton) stopButton.disabled = false;
        } else {
            if (statusBadge) {
                statusBadge.textContent = 'Stopped';
                statusBadge.className = 'badge bg-danger';
            }

            if (automationStatus) {
                automationStatus.textContent = 'Automation is stopped';
                automationStatus.className = 'alert alert-info';
            }

            // Enable start button, disable stop button
            const startButton = document.getElementById('start-button');
            const stopButton = document.getElementById('stop-button');
            if (startButton) startButton.disabled = false;
            if (stopButton) stopButton.disabled = true;
        }

        // Update stats if provided
        if (data.stats) {
            console.log('Updating stats from WebSocket:', data.stats);
            updateDashboard(data.stats);
        }
    });

    socket.on('automation_error', function (data) {
        console.error('Automation error:', data.message);
        const automationStatus = document.getElementById('automation-status');
        if (automationStatus) {
            automationStatus.textContent = 'Error: ' + data.message;
            automationStatus.className = 'alert alert-danger';
        }

        showNotification('error', 'Automation error: ' + data.message);

        // Enable start button, disable stop button
        const startButton = document.getElementById('start-button');
        const stopButton = document.getElementById('stop-button');
        if (startButton) startButton.disabled = false;
        if (stopButton) stopButton.disabled = true;
    });
}

function startPolling() {
    if (!window.pollingInterval) {
        console.log('Starting polling for updates...');
        window.pollingInterval = setInterval(function () {
            loadStatsFromServer();
            checkAutomationStatus();
        }, 3000);
    }
}
// Update continuous mode UI
function updateContinuousModeUI() {
    const continuousModeCheckbox = document.getElementById('continuous-mode');
    if (continuousModeCheckbox) {
        continuousModeCheckbox.checked = continuousMode;
    }

    const continuousModeLabel = document.getElementById('continuous-mode-label');
    if (continuousModeLabel) {
        continuousModeLabel.textContent = continuousMode ?
            'Continuous Mode (ON)' : 'Continuous Mode (OFF)';
    }
}
// Update dashboard with current statistics
function updateDashboard(data) {
    console.log('Updating dashboard with data:', data);

    if (!data) {
        console.error('No data provided to updateDashboard');
        return;
    }

    // Extract data from the stats.json format
    const clicks = data.clicks || {};
    const history = data.history || [];
    const totalClicks = data.totalClicks || Object.values(clicks).reduce((sum, val) => sum + val, 0) || 0;

    console.log('Processed data:', {
        clicks,
        history: history.length > 0 ? history[0] : 'No history',
        totalClicks
    });

    // Update total clicks
    const totalClicksElement = document.getElementById('total-clicks');
    if (totalClicksElement) {
        totalClicksElement.textContent = totalClicks;
        console.log('Updated total clicks:', totalClicks);
    }

    // Update unique casinos count
    const uniqueCasinosElement = document.getElementById('unique-casinos');
    if (uniqueCasinosElement) {
        const uniqueCasinos = Object.keys(clicks).length;
        uniqueCasinosElement.textContent = uniqueCasinos;
        console.log('Updated unique casinos:', uniqueCasinos);
    }

    // Update most clicked casino
    const mostClickedNameElement = document.getElementById('most-clicked-name');
    const mostClickedCountElement = document.getElementById('most-clicked-count');

    if (mostClickedNameElement && mostClickedCountElement) {
        let mostClickedName = 'None';
        let mostClickedCount = 0;

        for (const casino in clicks) {
            if (clicks[casino] > mostClickedCount) {
                mostClickedCount = clicks[casino];
                mostClickedName = casino;
            }
        }

        mostClickedNameElement.textContent = mostClickedName;
        mostClickedCountElement.textContent = mostClickedCount + ' clicks';
        console.log('Updated most clicked:', mostClickedName, mostClickedCount);
    }

    // Update last clicked
    const lastClickedElement = document.getElementById('last-clicked');
    const lastClickedTimeElement = document.getElementById('last-clicked-time');

    if (lastClickedElement && lastClickedTimeElement) {
        if (history && history.length > 0) {
            const lastClick = history[history.length - 1];
            lastClickedElement.textContent = lastClick.casino || 'Unknown';
            lastClickedTimeElement.textContent = lastClick.timestamp || 'Unknown';
            console.log('Updated last clicked:', lastClick);
        } else {
            lastClickedElement.textContent = 'None';
            lastClickedTimeElement.textContent = 'N/A';
            console.log('No last clicked data available');
        }
    }

    // Update history table
    updateHistoryTable(history);
    updateHistorySection(data);
    // Update charts
    updateCharts(clicks, history);
}



// Process stats data and update the history section
function updateHistorySection(data) {
    const clicksData = data.clicks;
    const historyData = data.history;
    const screenshotData = data.Screenshot || {}; // Get screenshot data
    const summaryTableBody = document.getElementById('casino-summary-table');

    // Clear existing table content
    summaryTableBody.innerHTML = '';

    // Create a map to organize history by casino
    const casinoHistoryMap = {};
    const casinoLastTimestamp = {};
    const casinoAffiliate = {};
    // Process history data to group by casino
    historyData.forEach(entry => {
        const casinoName = entry.casino;
        const affiliate = entry.affiliate;
        // Initialize array if this is the first entry for this casino
        if (!casinoHistoryMap[casinoName]) {
            casinoHistoryMap[casinoName] = [];
        }

        // Add this entry to the casino's history
        casinoHistoryMap[casinoName].push(entry);

        // Update the last timestamp (assuming history is chronological)
        casinoLastTimestamp[casinoName] = entry.timestamp;

        // Update the affiliate
        casinoAffiliate[casinoName] = affiliate;
    });

    // Create table rows for each casino
    Object.keys(clicksData).forEach(casinoName => {
        const clickCount = clicksData[casinoName];
        const lastTimestamp = casinoLastTimestamp[casinoName] || 'N/A';
        const affiliate = casinoAffiliate[casinoName] || 'N/A';

        // Format the timestamp for display
        let formattedTimestamp = 'N/A';
        if (lastTimestamp !== 'N/A') {
            const [datePart, timePart] = lastTimestamp.split(' ');
            formattedTimestamp = `${datePart} at ${timePart}`;
        }

        // Create the table row
        const row = document.createElement('tr');
        row.className = 'hoverable-row';
        row.innerHTML = `
            <td>${casinoName}</td>
            <td>${clickCount}</td>
            <td>${affiliate}</td>
            <td>${formattedTimestamp}</td>
        `;

        // **THIS IS THE IMPORTANT PART - adding the data to the row**
        $(row).data('screenshot', screenshotData[casinoName] || ''); // Store the screenshot path here

        // Add hover events to show/hide detailed history
        row.addEventListener('mouseenter', (event) => {
            showHistoryTooltip(casinoName, casinoHistoryMap[casinoName] || [], event);
        });

        row.addEventListener('mouseleave', () => {
            hideHistoryTooltip();
        });

        // Add mousemove event to follow cursor
        row.addEventListener('mousemove', (event) => {
            updateTooltipPosition(event);
        });

        summaryTableBody.appendChild(row);
    });
}

// Add this code after your existing updateHistorySection function
$(document).ready(function () {
    // Event delegation for dynamically added rows (unchanged)
    $('#casino-summary-table').on('click', 'tr', function () {
        const casino = $(this).find('td:first').text();
        const timestamp = $(this).find('td:last').text();
        const screenshot = $(this).data('screenshot');
        openImagePreviewModal(casino, timestamp, screenshot);

        // Add click event listener to each row
        $(this).off('click').on('click', function (event) {
            const screenshot = $(this).data('screenshot');
            handleRowClick(event, screenshot);
        });
    });
});

function openImagePreviewModal(casino, timestamp, screenshot) {

    // Create modal if it doesn't exist
    if (!$('#imagePreviewModal').length) {
        const modalHTML = `
            <div class="modal fade" id="imagePreviewModal" tabindex="-1" aria-labelledby="imagePreviewModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="imagePreviewModalLabel">Casino Screenshot Preview</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body text-center">
                            <div id="modal-screenshot-container">
                                <img id="modalImage" src="" alt="Casino Screenshot" class="img-fluid">
                            </div>
                            <div class="mt-3">
                                <h6 id="modalCasinoName" class="mb-2"></h6>
                                <p id="modalTimestamp" class="text-muted"></p>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        $('body').append(modalHTML);

        // Add zoom and 3D tilt effect to the modal image
        const $modalImage = $('#modalImage');
        const $modalScreenshotContainer = $('#modal-screenshot-container');

        $modalImage.hover(
            function () {
                // Zoom effect on hover
                $(this).css('transform', 'scale(1.1)');
                $(this).css('transition', 'transform 0.3s ease');
                $modalScreenshotContainer.css('transition', 'transform 0.3s ease'); // Add transition to container
            },
            function () {
                // Zoom out
                $(this).css('transform', 'scale(1)');
                $modalScreenshotContainer.css('transform', 'perspective(1000px) rotateY(0deg) rotateX(0deg)'); // Reset 3D effect
            }
        );
        // 3D tilt effect
        $modalScreenshotContainer.mousemove(function (event) {
            const containerWidth = $(this).width();
            const containerHeight = $(this).height();
            const offsetX = event.offsetX;
            const offsetY = event.offsetY;

            // Calculate rotation angles based on mouse position
            const rotateY = (offsetX - containerWidth / 2) / containerWidth * 20; // Adjust sensitivity (20 deg max)
            const rotateX = -(offsetY - containerHeight / 2) / containerHeight * 20; // Adjust sensitivity (20 deg max)

            // Apply the 3D rotation
            $(this).css('transform', `perspective(1000px) rotateY(${rotateY}deg) rotateX(${rotateX}deg)`);
        });
    }
    const modal = new bootstrap.Modal(document.getElementById('imagePreviewModal'));
    // Update modal content
    $('#modalCasinoName').text(casino);
    $('#modalTimestamp').text(timestamp);
    const $modalImage = $('#modalImage');

    if (screenshot) {
        $modalImage.attr('src', screenshot).show();
        // Add zoom and 3D tilt effect AFTER the image is loaded
        $modalImage.on('load', function () {
            addZoomAndTiltEffects($modalImage);
        });
    } else {
        $modalImage.hide();
    }
    modal.show();
}

function addZoomAndTiltEffects($image) {
    const $container = $image.parent();
    let zoomLevel = 1;
    const zoomStep = 0.1; // Zoom increment/decrement

    // Zoom using arrow keys
    $(document).on('keydown', function (e) {
        if (e.key === 'ArrowUp' || e.key === 'ArrowRight') { // zoom in
            zoomLevel += zoomStep;
        } else if (e.key === 'ArrowDown' || e.key === 'ArrowLeft') { //zoom out
            zoomLevel -= zoomStep;
        }
        zoomLevel = Math.max(1, Math.min(zoomLevel, 3)); // Limit zoom
        $image.css('transform', `scale(${zoomLevel})`);
    });

    $container.mousemove(function (e) {
        const containerWidth = $(this).width();
        const containerHeight = $(this).height();
        const offsetX = e.offsetX;
        const offsetY = e.offsetY;

        const rotateY = (offsetX - containerWidth / 2) / containerWidth * 20;
        const rotateX = -(offsetY - containerHeight / 2) / containerHeight * 20;

        $(this).css('transform', `perspective(1000px) rotateY(${rotateY}deg) rotateX(${rotateX}deg)`);
    });

    $container.mouseleave(function () {
        $(this).css('transform', 'none');
    });

    $image.on('mouseenter', function () {
        $(this).css('cursor', 'zoom-in');
    });
    $image.on('mouseleave', function () {
        $(this).css('cursor', 'default');
    });
}



// Show detailed history tooltip
function showHistoryTooltip(casinoName, historyEntries, event) {
    const tooltip = document.getElementById('history-tooltip');
    const tooltipTitle = document.getElementById('history-tooltip-title');
    const detailTable = document.getElementById('history-detail-table');
    const screenshotContainer = document.getElementById('history-screenshot-container'); // Get the container

    // Set the tooltip title
    tooltipTitle.textContent = `${casinoName} History (${historyEntries.length} clicks)`;

    // Clear existing table content
    detailTable.innerHTML = '';

    // Clear existing screenshot
    screenshotContainer.innerHTML = ''; // Clear previous screenshot

    // Sort entries by timestamp (newest first)
    const sortedEntries = [...historyEntries].sort((a, b) => {
        return new Date(b.timestamp) - new Date(a.timestamp);
    });

    // Add entries to the table
    sortedEntries.forEach((entry, index) => {
        const [datePart, timePart] = entry.timestamp.split(' ');

        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${index + 1}</td>
            <td>${datePart}</td>
            <td>${timePart}</td>
        `;

        detailTable.appendChild(row);
    });

    // Load and display the screenshot
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            const screenshotPath = data.Screenshot && data.Screenshot[casinoName];
            if (screenshotPath) {
                const img = document.createElement('img');
                img.src = screenshotPath;
                img.alt = `Screenshot of ${casinoName}`;

                // Add hover effect to the image
                img.addEventListener('mouseenter', function () {
                    this.style.transform = 'scale(1.1)';
                    this.style.transition = 'transform 0.3s ease';
                });
                img.addEventListener('mouseleave', function () {
                    this.style.transform = 'scale(1)';
                });
                screenshotContainer.appendChild(img);
            } else {
                screenshotContainer.textContent = 'No screenshot available';
            }
        })
        .catch(error => {
            console.error('Error loading screenshot:', error);
            screenshotContainer.textContent = 'Failed to load screenshot';
        });

    // Position and show the tooltip
    updateTooltipPosition(event);
    tooltip.style.display = 'block';
}

// Update tooltip position based on mouse position
function updateTooltipPosition(event) {
    const tooltip = document.getElementById('history-tooltip');

    // Get viewport dimensions
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    // Get tooltip dimensions
    const tooltipWidth = tooltip.offsetWidth;
    const tooltipHeight = tooltip.offsetHeight;

    // Calculate position (offset from cursor)
    let left = event.pageX + 15;
    let top = event.pageY + 15;

    // Adjust if tooltip would go off-screen
    if (left + tooltipWidth > viewportWidth - 20) {
        left = event.pageX - tooltipWidth - 15;
    }

    if (top + tooltipHeight > viewportHeight + window.scrollY - 20) {
        top = event.pageY - tooltipHeight - 15;
    }

    // Set position
    tooltip.style.left = `${left}px`;
    tooltip.style.top = `${top}px`;
}

// Hide the history tooltip
function hideHistoryTooltip() {
    const tooltip = document.getElementById('history-tooltip');
    tooltip.style.display = 'none';
}

// Close popup when clicking outside
function closePopupOnClickOutside(event) {
    const popup = document.getElementById('history-detail-popup');

    if (!popup.contains(event.target) &&
        !event.target.closest('.clickable-row')) {
        hideHistoryPopup();
    }
}
// Load stats from server
function loadStatsFromServer() {
    console.log('Loading stats from server...');
    fetch('/api/stats')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Stats loaded from server:', data);
            updateDashboard(data);
        })
        .catch(error => {
            console.error('Error loading stats from server:', error);
            showNotification('error', 'Failed to load statistics');
        });
}

document.addEventListener('DOMContentLoaded', function () {
    // Connect to WebSocket
    connectWebSocket();
    // Always load initial data
    loadStatsFromServer();
    checkAutomationStatus();
    // Sidebar toggle functionality
    let sidebar = document.querySelector(".sidebar");
    let sidebarBtn = document.querySelector(".sidebarBtn");

    if (sidebar && sidebarBtn) {
        sidebarBtn.onclick = function () {
            sidebar.classList.toggle("active");
            if (sidebar.classList.contains("active")) {
                sidebarBtn.classList.replace("bx-menu", "bx-menu-alt-right");
            } else {
                sidebarBtn.classList.replace("bx-menu-alt-right", "bx-menu");
            }
        }
    }

    // Section navigation
    function showSection(sectionName) {
        // Hide all sections
        const sections = document.querySelectorAll('.section-content');
        sections.forEach(section => {
            section.classList.add('hidden');
        });

        // Show the requested section
        const targetSection = document.getElementById(sectionName + '-section');
        if (targetSection) {
            targetSection.classList.remove('hidden');
        }

        // Update active state in navigation
        const navLinks = document.querySelectorAll('.nav-links li');
        navLinks.forEach(link => {
            link.classList.remove('active');
        });

        // Find the link that corresponds to this section and make it active
        const activeLink = document.querySelector(`.nav-links li a[id="${sectionName}Link"]`);
        if (activeLink) {
            activeLink.parentElement.classList.add('active');
        }

        // Update the dashboard title
        const dashboardTitle = document.querySelector('.dashboard');
        if (dashboardTitle) {
            dashboardTitle.textContent = sectionName.charAt(0).toUpperCase() + sectionName.slice(1);
        }
    }

    // Set up navigation links
    const dashboardLink = document.querySelector('.nav-links li:first-child a');
    if (dashboardLink) {
        dashboardLink.addEventListener('click', function (e) {
            e.preventDefault();
            showSection('dashboard');
        });
    }

    const controlLink = document.getElementById('controlLink');
    if (controlLink) {
        controlLink.addEventListener('click', function (e) {
            e.preventDefault();
            showSection('control');
        });
    }

    const historyLink = document.getElementById('historyLink');
    if (historyLink) {
        historyLink.addEventListener('click', function (e) {
            e.preventDefault();
            showSection('history');
        });
    }

    const settingsLink = document.getElementById('settingsLink');
    if (settingsLink) {
        settingsLink.addEventListener('click', function (e) {
            e.preventDefault();
            showSection('settings');
        });
    }
    // Update continuous mode UI
});

// Update history table
function updateHistoryTable(history) {
    const historyTableBody = document.getElementById('history-table-body');
    if (!historyTableBody) {
        console.error('History table body element not found');
        return;
    }

    // Clear existing rows
    historyTableBody.innerHTML = '';

    // Check if history exists and has entries
    if (!history || !Array.isArray(history) || history.length === 0) {
        console.log('No history data available');

        // Add a row indicating no data
        const emptyRow = document.createElement('tr');
        emptyRow.innerHTML = `
            <td colspan="3" class="text-center">No history data available</td>
        `;
        historyTableBody.appendChild(emptyRow);
        return;
    }

    console.log('Updating history table with data:', history);

    // Display the most recent clicks first (up to 50)
    const recentHistory = [...history].reverse().slice(0, 50);

    recentHistory.forEach((click, index) => {
        const row = document.createElement('tr');

        // Make sure we handle missing data gracefully
        const casino = click.casino || 'Unknown';
        const timestamp = click.timestamp || 'Unknown';

        row.innerHTML = `
            <td>${index + 1}</td>
            <td>${casino}</td>
            <td>${timestamp}</td>
        `;
        historyTableBody.appendChild(row);
    });

    console.log('Updated history table with', recentHistory.length, 'entries');
}

// Update charts
function updateCharts(clicks, history) {
    // Distribution chart
    updateDistributionChart(clicks);

    // History chart
    updateHistoryChart(history);
}

// Debounce function to prevent too frequent updates
function debounce(func, wait) {
    let timeout;
    return function (...args) {
        const context = this;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), wait);
    };
}

// Global chart instances
let distributionChart = null;
let historyChart = null;

// Update charts with debouncing
const debouncedUpdateCharts = debounce(function (clicks, history) {
    updateDistributionChart(clicks);
    updateHistoryChart(history);
}, 500); // Only update charts every 500ms at most
// Update distribution chart
function updateDistributionChart(clicks) {
    const ctx = document.getElementById('clickDistributionChart');
    if (!ctx) return;

    // Prepare data for chart
    const labels = Object.keys(clicks);
    const chartData = Object.values(clicks);
    const backgroundColors = generateColors(labels.length);

    // Check if chart already exists
    if (distributionChart) {
        // Update existing chart
        distributionChart.data.labels = labels;
        distributionChart.data.datasets[0].data = chartData;
        distributionChart.data.datasets[0].backgroundColor = backgroundColors;
        distributionChart.update('none'); // Use 'none' animation for smoother updates
    } else {
        // Create new chart only if it doesn't exist
        distributionChart = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: chartData,
                    backgroundColor: backgroundColors,
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 500 // Shorter animation
                },
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            boxWidth: 15,
                            font: {
                                size: 10
                            }
                        }
                    }
                }
            }
        });
    }
}

// Update history chart (clicks over time)
function updateHistoryChart(history) {
    const ctx = document.getElementById('clickHistoryChart');
    if (!ctx) return;

    // Group clicks by hour for the last 24 hours
    const now = new Date();
    const hourlyData = Array(24).fill(0);
    const hourLabels = Array(24).fill().map((_, i) => {
        const hour = (now.getHours() - 23 + i + 24) % 24;
        return `${hour}:00`;
    });

    // Count clicks per hour
    history.forEach(click => {
        try {
            const clickTime = new Date(click.timestamp);
            const hoursDiff = Math.floor((now - clickTime) / (1000 * 60 * 60));

            if (hoursDiff < 24) {
                const index = 23 - hoursDiff;
                hourlyData[index]++;
            }
        } catch (e) {
            console.error('Error parsing timestamp:', click.timestamp, e);
        }
    });

    // Check if chart already exists
    if (historyChart) {
        // Update existing chart
        historyChart.data.labels = hourLabels;
        historyChart.data.datasets[0].data = hourlyData;
        historyChart.update('none'); // Use 'none' animation for smoother updates
    } else {
        // Create new chart only if it doesn't exist
        historyChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: hourLabels,
                datasets: [{
                    label: 'Clicks',
                    data: hourlyData,
                    borderColor: 'rgba(75, 192, 192, 1)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    borderWidth: 2,
                    tension: 0.1,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 500 // Shorter animation
                },
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    },
                    x: {
                        ticks: {
                            maxRotation: 0,
                            autoSkip: true,
                            maxTicksLimit: 12
                        }
                    }
                }
            }
        });
    }
}

// Update charts
function updateCharts(clicks, history) {
    debouncedUpdateCharts(clicks, history);
}
// Generate random colors for chart
function generateColors(count) {
    const colors = [];
    for (let i = 0; i < count; i++) {
        const hue = (i * 137) % 360; // Use golden angle for good distribution
        colors.push(`hsla(${hue}, 70%, 60%, 0.8)`);
    }
    return colors;
}

// Set up continuous mode toggle
const continuousModeCheckbox = document.getElementById('continuous-mode');
if (continuousModeCheckbox) {
    continuousModeCheckbox.addEventListener('change', function () {
        continuousMode = this.checked;
        updateContinuousModeUI();

        fetch('/api/toggle_continuous', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ continuous: continuousMode })
        })
            .then(response => response.json())
            .then(data => {
                showNotification('info', `Continuous mode ${continuousMode ? 'enabled' : 'disabled'}`);
            })
            .catch(error => {
                console.error('Error toggling continuous mode:', error);
            });
    });
}

// Automation control
const startButton = document.getElementById('start-button');
const stopButton = document.getElementById('stop-button');

if (startButton && stopButton) {
    startButton.addEventListener('click', function () {
        // Disable button to prevent multiple clicks
        startButton.disabled = true;
        startButton.textContent = 'Starting...';

        fetch('/api/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ continuous: continuousMode })
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Server responded with status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'started' || data.status === 'already_running') {
                    const statusBadge = document.getElementById('status-badge');
                    const automationStatus = document.getElementById('automation-status');

                    if (statusBadge) {
                        statusBadge.textContent = 'Running';
                        statusBadge.className = 'badge bg-success';
                    }

                    if (automationStatus) {
                        automationStatus.textContent = 'Automation is running' +
                            (data.continuous ? ' (Continuous Mode)' : '');
                        automationStatus.className = 'alert alert-success';
                    }

                    showNotification('success', 'Automation started successfully');

                    // Enable stop button
                    stopButton.disabled = false;
                } else {
                    const automationStatus = document.getElementById('automation-status');
                    if (automationStatus) {
                        automationStatus.textContent = 'Failed to start: ' + data.message;
                        automationStatus.className = 'alert alert-danger';
                    }

                    showNotification('error', 'Failed to start automation: ' + data.message);

                    // Re-enable start button
                    startButton.disabled = false;
                }
            })
            .catch(error => {
                console.error('Error starting automation:', error);

                const automationStatus = document.getElementById('automation-status');
                if (automationStatus) {
                    automationStatus.textContent = 'Error: ' + error.message;
                    automationStatus.className = 'alert alert-danger';
                }

                showNotification('error', 'Error starting automation: ' + error.message);

                // Re-enable start button
                startButton.disabled = false;
            })
            .finally(() => {
                // Reset button text
                startButton.textContent = 'Start Automation';
            });
    });

    stopButton.addEventListener('click', function () {
        // Disable button to prevent multiple clicks
        stopButton.disabled = true;
        stopButton.textContent = 'Stopping...';

        fetch('/api/stop', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Server responded with status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'stopping' || data.status === 'stopped') {
                    const statusBadge = document.getElementById('status-badge');
                    const automationStatus = document.getElementById('automation-status');

                    if (statusBadge) {
                        statusBadge.textContent = 'Stopped';
                        statusBadge.className = 'badge bg-danger';
                    }

                    if (automationStatus) {
                        automationStatus.textContent = 'Automation is stopping...';
                        automationStatus.className = 'alert alert-info';
                    }

                    showNotification('success', 'Automation is stopping...');

                    // Enable start button
                    startButton.disabled = false;
                } else {
                    const automationStatus = document.getElementById('automation-status');
                    if (automationStatus) {
                        automationStatus.textContent = 'Failed to stop: ' + data.message;
                        automationStatus.className = 'alert alert-danger';
                    }

                    showNotification('error', 'Failed to stop automation: ' + data.message);

                    // Re-enable stop button
                    stopButton.disabled = false;
                }
            })
            .catch(error => {
                console.error('Error stopping automation:', error);

                const automationStatus = document.getElementById('automation-status');
                if (automationStatus) {
                    automationStatus.textContent = 'Error: ' + error.message;
                    automationStatus.className = 'alert alert-danger';
                }

                showNotification('error', 'Error stopping automation: ' + error.message);

                // Re-enable stop button
                stopButton.disabled = false;
            })
            .finally(() => {
                // Reset button text
                stopButton.textContent = 'Stop Automation';
            });
    });
}

// Reset statistics button
const resetButton = document.getElementById('reset-stats-button');
if (resetButton) {
    resetButton.addEventListener('click', function () {
        if (confirm('Are you sure you want to reset all statistics?')) {
            fetch('/api/reset', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        showNotification('success', 'Statistics reset successfully');
                        // Request updated stats via WebSocket
                        if (socket && socket.connected) {
                            socket.emit('request_status');
                        } else {
                            loadStatsFromServer();
                        }
                    } else {
                        showNotification('error', data.message || 'Failed to reset statistics');
                    }
                })
                .catch(error => {
                    console.error('Error resetting stats:', error);
                    showNotification('error', 'Failed to reset statistics');
                });
        }
    });
}

// Function to show notifications
function showNotification(type, message) {
    let notificationArea = document.getElementById('notificationArea');
    if (!notificationArea) {
        // Create notification area if it doesn't exist
        notificationArea = document.createElement('div');
        notificationArea.id = 'notificationArea';
        notificationArea.style.position = 'fixed';
        notificationArea.style.top = '20px';
        notificationArea.style.right = '20px';
        notificationArea.style.zIndex = '1000';
        document.body.appendChild(notificationArea);
    }

    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'info'}`;
    notification.style.marginBottom = '10px';
    notification.textContent = message;

    notificationArea.appendChild(notification);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transition = 'opacity 0.5s';
        setTimeout(() => {
            notification.remove();
        }, 500);
    }, 5000);
}

// Check automation status on page load
function checkAutomationStatus() {
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            const statusBadge = document.getElementById('status-badge');
            const automationStatus = document.getElementById('automation-status');

            // Update continuous mode
            continuousMode = data.continuous || false;
            updateContinuousModeUI();

            if (data.running) {
                if (statusBadge) {
                    statusBadge.textContent = 'Running';
                    statusBadge.className = 'badge bg-success';
                }

                if (automationStatus) {
                    automationStatus.textContent = 'Automation is running' +
                        (continuousMode ? ' (Continuous Mode)' : '');
                    automationStatus.className = 'alert alert-success';
                }

                // Enable stop button, disable start button
                const startButton = document.getElementById('start-button');
                const stopButton = document.getElementById('stop-button');
                if (startButton) startButton.disabled = true;
                if (stopButton) stopButton.disabled = false;
            } else {
                if (statusBadge) {
                    statusBadge.textContent = 'Stopped';
                    statusBadge.className = 'badge bg-danger';
                }

                if (automationStatus) {
                    automationStatus.textContent = 'Automation is stopped';
                    automationStatus.className = 'alert alert-info';
                }

                // Enable start button, disable stop button
                const startButton = document.getElementById('start-button');
                const stopButton = document.getElementById('stop-button');
                if (startButton) startButton.disabled = false;
                if (stopButton) stopButton.disabled = true;
            }
        })
        .catch(error => {
            console.error('Error checking automation status:', error);

            const statusBadge = document.getElementById('status-badge');
            if (statusBadge) {
                statusBadge.textContent = 'Unknown';
                statusBadge.className = 'badge bg-secondary';
            }
        });
}

// Load stats from server
loadStatsFromServer();

// Check automation status
checkAutomationStatus();

// Try to set up WebSocket for real-time updates
try {
    connectWebSocket();
} catch (e) {
    console.log('WebSocket setup failed, falling back to polling:', e);
    // Poll for updates every 5 seconds
    setInterval(function () {
        loadStatsFromServer();
        checkAutomationStatus();
    }, 5000);
}

// Show dashboard by default
showSection('dashboard');

