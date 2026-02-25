// App state
let devices = [];
let commandLog = [];
let connectionStatus = 'unknown';

// DOM elements
const connectionEl = document.getElementById('connection-status');
const devicesListEl = document.getElementById('devices-list');
const commandLogEl = document.getElementById('command-log');
const deviceIdInput = document.getElementById('device-id');
const commandInput = document.getElementById('command');
const sendBtn = document.getElementById('send-command');
const refreshBtn = document.getElementById('refresh-status');
const resultBox = document.getElementById('command-result');

// API base URL (relative to current host)
const API_BASE = '/api';

// Helper to log messages
function log(message, type = 'info') {
    const entry = {
        timestamp: new Date().toLocaleTimeString(),
        message: message,
        type: type
    };
    commandLog.unshift(entry);
    if (commandLog.length > 20) commandLog.pop();
    renderLog();
}

// Render command log
function renderLog() {
    if (!commandLogEl) return;
    commandLogEl.innerHTML = commandLog.map(entry => 
        `<div class="log-entry log-${entry.type}">[${entry.timestamp}] ${entry.message}</div>`
    ).join('');
}

// Update connection status display
function updateConnectionStatus() {
    if (!connectionEl) return;
    let statusText = '';
    let statusClass = '';
    
    switch(connectionStatus) {
        case 'connected':
            statusText = '✅ Connected to gateway';
            statusClass = 'status-online';
            break;
        case 'error':
            statusText = '❌ Connection error';
            statusClass = 'status-offline';
            break;
        default:
            statusText = '⏳ Checking connection...';
            statusClass = '';
    }
    
    connectionEl.innerHTML = `<span class="device-status ${statusClass}">${statusText}</span>`;
}

// Fetch devices from C2 server
async function fetchDevices() {
    try {
        const response = await fetch(`${API_BASE}/status`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        devices = Array.isArray(data) ? data : [];
        connectionStatus = 'connected';
        log(`Fetched ${devices.length} devices`, 'success');
    } catch (error) {
        console.error('Fetch devices error:', error);
        connectionStatus = 'error';
        devices = [];
        log(`Failed to fetch devices: ${error.message}`, 'error');
    }
    updateConnectionStatus();
    renderDevices();
}

// Render devices list
function renderDevices() {
    if (!devicesListEl) return;
    
    if (devices.length === 0) {
        devicesListEl.innerHTML = '<div class="device-item">No devices registered</div>';
        return;
    }
    
    devicesListEl.innerHTML = devices.map(device => {
        const deviceId = device.client_serial || device.device_id || 'unknown';
        const lastSeen = device.last_seen ? new Date(device.last_seen).toLocaleString() : 'never';
        const status = device.operational_status === 'online' ? 'online' : 'offline';
        const statusClass = status === 'online' ? 'status-online' : 'status-offline';
        
        return `
            <div class="device-item">
                <span><strong>${deviceId}</strong><br><small>Last: ${lastSeen}</small></span>
                <span class="device-status ${statusClass}">${status}</span>
            </div>
        `;
    }).join('');
}

// Send command to device
async function sendCommand() {
    const deviceId = deviceIdInput.value.trim();
    const command = commandInput.value.trim();
    
    if (!deviceId || !command) {
        alert('Please enter both device ID and command');
        return;
    }
    
    resultBox.innerHTML = 'Sending command...';
    log(`Sending '${command}' to ${deviceId}`, 'info');
    
    try {
        const response = await fetch(`${API_BASE}/command`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ device_id: deviceId, command: command })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            resultBox.innerHTML = `✅ Command sent successfully\nResponse: ${JSON.stringify(data, null, 2)}`;
            log(`Command to ${deviceId} succeeded`, 'success');
        } else {
            resultBox.innerHTML = `❌ Error: ${data.error || response.statusText}`;
            log(`Command to ${deviceId} failed: ${data.error || response.statusText}`, 'error');
        }
    } catch (error) {
        resultBox.innerHTML = `❌ Network error: ${error.message}`;
        log(`Network error sending command: ${error.message}`, 'error');
    }
}

// Fetch device details (optional, could be used later)
async function fetchDeviceDetails(deviceId) {
    try {
        const response = await fetch(`${API_BASE}/device/${deviceId}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        log(`Fetched details for ${deviceId}`, 'info');
        return data;
    } catch (error) {
        log(`Failed to fetch device details: ${error.message}`, 'error');
        return null;
    }
}

// Initialize service worker for PWA
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js').then(registration => {
            console.log('ServiceWorker registered');
        }).catch(error => {
            console.log('ServiceWorker registration failed:', error);
        });
    });
}

// Event listeners
if (sendBtn) sendBtn.addEventListener('click', sendCommand);
if (refreshBtn) refreshBtn.addEventListener('click', fetchDevices);

// Initial load
document.addEventListener('DOMContentLoaded', () => {
    fetchDevices();
    // Refresh every 30 seconds
    setInterval(fetchDevices, 30000);
});