let currentBlockId = null;
let currentPropertyName = null;
let currentSimulationId = null;
let progressInterval = null;
let spreadsheetData = {};
let allTemplateProperties = [];
let blockIdToNameMapping = {}; // Add this new global variable

// State persistence functions
function saveState() {
    const state = {
        currentSimulationId: currentSimulationId,
        spreadsheetData: spreadsheetData,
        autoSimEnabled: document.getElementById('autoSimToggle')?.checked || false
    };
    localStorage.setItem('sedaroVioletState', JSON.stringify(state));
}

function loadState() {
    try {
        const savedState = localStorage.getItem('sedaroVioletState');
        if (savedState) {
            const state = JSON.parse(savedState);
            
            // Restore simulation ID
            if (state.currentSimulationId) {
                currentSimulationId = state.currentSimulationId;
                // Check if simulation is still running
                checkAndRestoreSimulation(state.currentSimulationId);
            }

            
            
            // Restore spreadsheet data
            if (state.spreadsheetData) {
                spreadsheetData = state.spreadsheetData;
                restoreSpreadsheetUI();
            }
            
            // Restore auto-sim toggle
            if (state.autoSimEnabled !== undefined) {
                const autoSimToggle = document.getElementById('autoSimToggle');
                if (autoSimToggle) {
                    autoSimToggle.checked = state.autoSimEnabled;
                }
            }
            
            console.log('State restored from localStorage');
        }
    } catch (error) {
        console.error('Error loading state:', error);
        // Clear corrupted state
        localStorage.removeItem('sedaroVioletState');
    }
}

async function checkAndRestoreSimulation(simulationId) {
    try {
        const response = await fetch(`/api/simulation_status?simulation_id=${simulationId}`);
        const result = await response.json();
        
        if (result.success && !result.is_complete) {
            // Simulation is still running, restore progress monitoring
            const progressDiv = document.getElementById('simulationProgress');
            if (progressDiv) {
                progressDiv.style.display = 'block';
            }
            startProgressMonitoring(simulationId);
            showToast('Restored simulation monitoring', 'info');
        } else {
            // Simulation is complete or doesn't exist, clear the ID
            currentSimulationId = null;
            saveState();
        }
    } catch (error) {
        console.error('Error checking simulation status:', error);
        currentSimulationId = null;
        saveState();
    }
}

function restoreSpreadsheetUI() {
    const tbody = document.getElementById('bomTableBody');
    if (!tbody) return;
    
    // Clear existing rows
    tbody.innerHTML = '';
    
    // Restore rows from saved data
    for (const [rowId, data] of Object.entries(spreadsheetData)) {
        addSpreadsheetRow(rowId, data);
    }
    
    // Add empty rows if needed to maintain minimum of 5 rows
    const currentRows = Object.keys(spreadsheetData).length;
    for (let i = currentRows; i < 5; i++) {
        addSpreadsheetRow();
    }
}

// Save state periodically and on important events
function setupStatePersistence() {
    // Save state every 5 seconds
    setInterval(saveState, 5000);
    
    // Save state on page unload
    window.addEventListener('beforeunload', saveState);
    
    // Save state when spreadsheet data changes
    const originalUpdateSpreadsheetData = updateSpreadsheetData;
    updateSpreadsheetData = function(rowId, field, value) {
        originalUpdateSpreadsheetData(rowId, field, value);
        saveState();
    };
}

async function loadBlocks() {
    // Commented out battery block display for now
    /*
    try {
        const response = await fetch('/api/blocks');
        const blocks = await response.json();
        
        const contentDiv = document.getElementById('content');
        const loadingDiv = document.getElementById('loading');
        
        if (blocks.error) {
            contentDiv.innerHTML = `<div class="error">Error: ${blocks.error}</div>`;
        } else {
            contentDiv.innerHTML = generateBlocksHTML(blocks);
        }
        
        loadingDiv.style.display = 'none';
        contentDiv.style.display = 'block';
    } catch (error) {
        document.getElementById('content').innerHTML = 
            `<div class="error">Failed to load blocks: ${error.message}</div>`;
        document.getElementById('loading').style.display = 'none';
    }
    */
    
    // Hide the loading and content divs since we're not using battery blocks
    const loadingDiv = document.getElementById('loading');
    const contentDiv = document.getElementById('content');
    if (loadingDiv) loadingDiv.style.display = 'none';
    if (contentDiv) contentDiv.style.display = 'none';
}

function generateBlocksHTML(blocks) {
    let html = '';
    
    for (const [blockType, blockList] of Object.entries(blocks)) {
        html += `<div class="block-section">
            <div class="block-type">${blockType} (${blockList.length})</div>`;
        
        blockList.forEach(block => {
            html += `<div class="block-item">
                <div class="block-name">${block.name}</div>
                <div class="property-grid">`;
            
            for (const [propName, propValue] of Object.entries(block.data)) {
                html += `<div class="property-item">
                    <div class="property-name">${propName}</div>
                    <div class="property-value">${JSON.stringify(propValue)}</div>
                    <button class="edit-button" onclick="editProperty('${block.id}', '${propName}', '${propValue}')">
                        Edit
                    </button>
                </div>`;
            }
            
            html += `</div></div>`;
        });
        
        html += `</div>`;
    }
    
    return html;
}

function editProperty(blockId, propertyName, currentValue) {
    currentBlockId = blockId;
    currentPropertyName = propertyName;
    
    document.getElementById('propertyName').value = propertyName;
    document.getElementById('propertyValue').value = currentValue;
    document.getElementById('editResult').innerHTML = '';
    
    document.getElementById('editModal').style.display = 'block';
}

async function saveProperty() {
    const newValue = document.getElementById('propertyValue').value;
    const resultDiv = document.getElementById('editResult');
    
    try {
        const response = await fetch('/api/update_property', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                block_id: currentBlockId,
                property_name: currentPropertyName,
                new_value: newValue
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            resultDiv.innerHTML = `<div class="success">${result.message}</div>`;
            // Reload blocks to show updated values
            setTimeout(() => loadBlocks(), 1000);
        } else {
            resultDiv.innerHTML = `<div class="error">Error: ${result.error}</div>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<div class="error">Failed to update: ${error.message}</div>`;
    }
}

async function startSimulation() {
    const statusDiv = document.getElementById('simulationStatus');
    const simulateBtn = document.getElementById('simulateBtn');
    const progressDiv = document.getElementById('simulationProgress');
    
    statusDiv.style.display = 'block';
    statusDiv.innerHTML = '<div class="loading">Starting simulation...</div>';
    simulateBtn.disabled = true;
    
    try {
        const response = await fetch('/api/simulate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            currentSimulationId = result.simulation_id;
            
            statusDiv.innerHTML = `
                <div class="success">
                    <h4>✅ Simulation Started Successfully!</h4>
                    <p><strong>Simulation ID:</strong> ${result.simulation_id}</p>
                    <p><strong>Status:</strong> ${result.status}</p>
                    <p><strong>Message:</strong> ${result.message}</p>
                </div>
            `;
            
            // Show progress bar and start monitoring
            progressDiv.style.display = 'block';
            
            // Make sure progress bar and abort button are visible
            const progressBar = document.querySelector('.progress-container');
            const abortBtn = document.getElementById('abortBtn');
            if (progressBar) progressBar.style.display = 'flex';
            if (abortBtn) abortBtn.style.display = 'block';
            
            startProgressMonitoring(result.simulation_id);
        } else {
            statusDiv.innerHTML = `<div class="error">❌ Failed to start simulation: ${result.error}</div>`;
        }
    } catch (error) {
        statusDiv.innerHTML = `<div class="error">❌ Error starting simulation: ${error.message}</div>`;
    } finally {
        simulateBtn.disabled = false;
    }
}

async function checkSimulationStatus() {
    if (!currentSimulationId) {
        alert('No simulation running. Start a simulation first.');
        return;
    }
    
    await updateProgress(currentSimulationId);
}

function startProgressMonitoring(simulationId) {
    // Clear any existing interval
    if (progressInterval) {
        clearInterval(progressInterval);
    }
    
    // Update immediately
    updateProgress(simulationId);
    
    // Then update every 2 seconds
    progressInterval = setInterval(async () => {
        const isComplete = await updateProgress(simulationId);
        if (isComplete) {
            clearInterval(progressInterval);
            progressInterval = null;
        }
    }, 2000);
    
    // Safety timeout: stop polling after 30 minutes (1800 seconds) to prevent infinite polling
    setTimeout(() => {
        if (progressInterval) {
            console.warn('Stopping simulation monitoring due to timeout (30 minutes)');
            clearInterval(progressInterval);
            progressInterval = null;
            showToast('Simulation monitoring stopped due to timeout', 'info');
            
            // Update UI to show timeout
            const statusText = document.getElementById('statusText');
            if (statusText) {
                statusText.textContent = '⏰ Simulation monitoring timed out after 30 minutes';
            }
        }
    }, 30 * 60 * 1000); // 30 minutes
}

async function updateProgress(simulationId) {
    try {
        const response = await fetch(`/api/simulation_status?simulation_id=${simulationId}`);
        const result = await response.json();
        
        if (result.success) {
            const progressFill = document.getElementById('progressFill');
            const progressText = document.getElementById('progressText');
            const statusText = document.getElementById('statusText');
            const progressDetails = document.getElementById('progressDetails');
            
            // Update progress bar
            const progress = result.progress || 0;
            progressFill.style.width = `${progress}%`;
            progressText.textContent = `${Math.round(progress)}%`;
            
            // Update status text
            statusText.textContent = result.message;
            
            // Update detailed progress information if available
            if (result.progress_info && result.status === 'RUNNING') {
                const currentTime = document.getElementById('currentTime');
                const timeRange = document.getElementById('timeRange');
                const minTimeStep = document.getElementById('minTimeStep');
                
                if (result.progress_info.currentTime !== undefined) {
                    currentTime.textContent = result.progress_info.currentTime.toFixed(1);
                }
                
                if (result.progress_info.startTime !== undefined && result.progress_info.stopTime !== undefined) {
                    timeRange.textContent = `${result.progress_info.startTime.toFixed(1)} - ${result.progress_info.stopTime.toFixed(1)}`;
                }
                
                if (result.progress_info.minTimeStep !== undefined) {
                    minTimeStep.textContent = result.progress_info.minTimeStep.toExponential(1);
                }
                
                progressDetails.style.display = 'block';
            } else {
                progressDetails.style.display = 'none';
            }
            
            // Check if simulation is complete
            if (result.is_complete) {
                if (result.status === 'SUCCEEDED') {
                    statusText.textContent = '✅ Simulation completed successfully!';
                    showToast('Simulation completed successfully!', 'success');
                } else {
                    statusText.textContent = `❌ Simulation ${result.status.toLowerCase()}`;
                    showToast(`Simulation ${result.status.toLowerCase()}`, 'error');
                }
                
                // Hide progress bar and abort button, but keep status message
                const progressBar = document.querySelector('.progress-container');
                const abortBtn = document.getElementById('abortBtn');
                if (progressBar) progressBar.style.display = 'none';
                if (abortBtn) abortBtn.style.display = 'none';
                
                // Reset simulation ID to allow new simulations
                currentSimulationId = null;
                
                return true; // Stop polling
            }
            
            return false; // Continue polling
        } else {
            console.error('Failed to get simulation status:', result.error);
            // If we can't get status, stop polling to avoid infinite loops
            showToast('Failed to get simulation status, stopping monitoring', 'error');
            return true; // Stop polling
        }
    } catch (error) {
        console.error('Error checking simulation status:', error);
        // If there's a network error, stop polling to avoid infinite loops
        showToast('Error checking simulation status, stopping monitoring', 'error');
        return true; // Stop polling
    }
}

async function abortSimulation() {
    if (!currentSimulationId) {
        showToast('No simulation running to abort', 'error');
        return;
    }
    
    if (!confirm('Are you sure you want to abort the current simulation?')) {
        return;
    }
    
    try {
        const response = await fetch('/api/abort_simulation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                simulation_id: currentSimulationId
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('Simulation aborted successfully', 'success');
            
            // Stop progress monitoring
            if (progressInterval) {
                clearInterval(progressInterval);
                progressInterval = null;
            }
            
            // Update UI
            const statusText = document.getElementById('statusText');
            const progressDetails = document.getElementById('progressDetails');
            const progressBar = document.querySelector('.progress-container');
            const abortBtn = document.getElementById('abortBtn');
            
            statusText.textContent = 'Simulation aborted';
            progressDetails.style.display = 'none';
            if (progressBar) progressBar.style.display = 'none';
            if (abortBtn) abortBtn.style.display = 'none';
            
            currentSimulationId = null;
        } else {
            showToast(`Failed to abort simulation: ${result.error}`, 'error');
        }
    } catch (error) {
        showToast(`Error aborting simulation: ${error.message}`, 'error');
    }
}

async function getSimulationResults() {
    const statusDiv = document.getElementById('simulationStatus');
    const resultsBtn = document.getElementById('resultsBtn');
    
    statusDiv.style.display = 'block';
    statusDiv.innerHTML = '<div class="loading">Getting simulation results...</div>';
    resultsBtn.disabled = true;
    
    try {
        const response = await fetch('/api/results', {
            method: 'GET'
        });
        
        const result = await response.json();
        
        if (result.success) {
            statusDiv.innerHTML = `
                <div class="success">
                    <h4>📊 Simulation Results</h4>
                    <p><strong>Status:</strong> ${result.simulation_status}</p>
                    <p><strong>End Time:</strong> ${result.end_time}</p>
                    <pre style="background: #f8f9fa; padding: 1rem; border-radius: 4px; overflow-x: auto;">
${JSON.stringify(result.stats, null, 2)}
                    </pre>
                </div>
            `;
        } else {
            statusDiv.innerHTML = `<div class="error">❌ Failed to get results: ${result.error}</div>`;
        }
    } catch (error) {
        statusDiv.innerHTML = `<div class="error">❌ Error getting results: ${error.message}</div>`;
    } finally {
        resultsBtn.disabled = false;
    }
}

// Close modal when clicking on X or outside
document.querySelector('.close').onclick = function() {
    document.getElementById('editModal').style.display = 'none';
}

window.onclick = function(event) {
    const modal = document.getElementById('editModal');
    if (event.target == modal) {
        modal.style.display = 'none';
    }
}

let allComponents = [];
let selectedComponent = null;

function showToast(message, type = 'success') {
    const toast = document.getElementById('toastNotification');
    const toastMessage = document.getElementById('toastMessage');
    
    // Set message and type
    toastMessage.textContent = message;
    toast.className = `toast-notification ${type}`;
    
    // Update icon based on type
    const icon = toast.querySelector('.toast-icon');
    if (type === 'success') {
        icon.textContent = '✅';
    } else if (type === 'error') {
        icon.textContent = '❌';
    } else if (type === 'info') {
        icon.textContent = 'ℹ️';
    }
    
    // Show toast
    toast.style.display = 'block';
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);
    
    // Hide toast after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            toast.style.display = 'none';
        }, 300);
    }, 3000);
}

async function loadComponents() {
    try {
        const response = await fetch('/api/template_structure');
        const result = await response.json();
        
        if (result.success) {
            console.log('Template structure:', result.data);
            allComponents = extractComponents(result.data);
            console.log('Extracted components:', allComponents);
            populateDropdown(allComponents);
        } else {
            alert('Error loading components: ' + result.error);
        }
    } catch (error) {
        alert('Failed to load components: ' + error.message);
    }
}

function extractComponents(data, prefix = '') {
    let components = [];
    
    if (typeof data === 'object' && data !== null) {
        if (Array.isArray(data)) {
            data.forEach((item, index) => {
                const path = prefix ? `${prefix}.${index}` : `${index}`;
                if (typeof item === 'object' && item !== null) {
                    if (item.id && item.type) {
                        // This looks like a block/component
                        components.push({
                            path: path,
                            id: item.id,
                            name: item.name || `${item.type}_${item.id}`,
                            type: item.type,
                            data: item
                        });
                    }
                    // Recursively extract from nested objects
                    components = components.concat(extractComponents(item, path));
                }
            });
        } else {
            Object.keys(data).forEach(key => {
                const path = prefix ? `${prefix}.${key}` : key;
                const value = data[key];
                
                if (typeof value === 'object' && value !== null) {
                    if (value.id && value.type) {
                        // This looks like a block/component
                        components.push({
                            path: path,
                            id: value.id,
                            name: value.name || `${value.type}_${value.id}`,
                            type: value.type,
                            data: value
                        });
                    }
                    // Recursively extract from nested objects
                    components = components.concat(extractComponents(value, path));
                } else if (prefix === '' && (typeof value === 'number' || typeof value === 'string' || typeof value === 'boolean')) {
                    // Root-level properties (like mass, name, etc.)
                    components.push({
                        path: path,
                        id: path, // Use path as ID for root properties
                        name: key,
                        type: 'root_property',
                        data: { [key]: value }
                    });
                }
            });
        }
    }
    
    return components;
}

function populateDropdown(components) {
    const dropdownList = document.getElementById('dropdownList');
    dropdownList.innerHTML = '';
    
    components.forEach(component => {
        const item = document.createElement('div');
        item.className = 'dropdown-item';
        item.textContent = `${component.name} (${component.type})`;
        item.onclick = () => selectComponent(component);
        dropdownList.appendChild(item);
    });
}

function filterDropdown() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const dropdownList = document.getElementById('dropdownList');
    const items = dropdownList.getElementsByClassName('dropdown-item');
    
    dropdownList.style.display = 'block';
    
    Array.from(items).forEach(item => {
        const text = item.textContent.toLowerCase();
        if (text.includes(searchTerm)) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
}

async function selectComponent(component) {
    selectedComponent = component;
    document.getElementById('searchInput').value = component.name;
    document.getElementById('dropdownList').style.display = 'none';
    document.getElementById('componentEditor').style.display = 'block';
    document.getElementById('selectedComponentName').textContent = `${component.name} Properties`;
    
    // Refresh component data from server before displaying
    await refreshComponentData(component);
    displayComponentProperties(selectedComponent);
}

async function refreshComponentData(component) {
    try {
        if (component.type === 'root_property') {
            // For root properties, get fresh agent template data
            const response = await fetch('/api/template_structure');
            const result = await response.json();
            
            if (result.success) {
                const freshValue = result.data[component.name];
                if (freshValue !== undefined) {
                    component.data[component.name] = freshValue;
                }
            }
        } else {
            // For block properties, get fresh block data
            const response = await fetch(`/api/block/${component.id}/properties`);
            const result = await response.json();
            
            if (result.success) {
                // Update the component data with fresh data
                Object.keys(result).forEach(key => {
                    if (!key.startsWith('_')) {
                        component.data[key] = result[key];
                    }
                });
            }
        }
    } catch (error) {
        console.log('Failed to refresh component data:', error);
    }
}

async function displayComponentProperties(component) {
    const propertiesDiv = document.getElementById('componentProperties');
    let html = '';
    
    if (component.type === 'root_property') {
        // For root properties, display the single property
        const propertyName = component.name;
        const value = component.data[propertyName];
        const mutability = await checkPropertyMutability(null, propertyName);
        
        html += `
            <div class="property-item ${mutability.mutable ? '' : 'immutable'}">
                <div class="property-name">
                    ${propertyName}
                    <span class="mutability-indicator ${mutability.mutable ? 'mutable' : 'immutable'}">
                        ${mutability.mutable ? 'Editable' : 'Read-only'}
                    </span>
                </div>
                <div class="property-value">
                    <input type="text" id="prop_${propertyName}" value="${JSON.stringify(value)}" 
                            onchange="updateComponentProperty('${propertyName}', this.value)"
                            ${mutability.mutable ? '' : 'disabled'}>
                    <button onclick="saveComponentProperty('${propertyName}', this)" class="save-button"
                            ${mutability.mutable ? '' : 'disabled'}>Save</button>
                    <button onclick="trackPropertyFromExplorer('${propertyName}', null, '${propertyName}')" 
                            class="track-button" title="Track this property in spreadsheet">
                        📊 Track
                    </button>
                </div>
            </div>
        `;
    } else {
        // For block properties, filter out internal fields and display editable properties
        for (const key of Object.keys(component.data)) {
            if (!key.startsWith('_') && key !== 'id' && key !== 'type') {
                const value = component.data[key];
                const mutability = await checkPropertyMutability(component.id, key);
                
                html += `
                    <div class="property-item ${mutability.mutable ? '' : 'immutable'}">
                        <div class="property-name">
                            ${key}
                            <span class="mutability-indicator ${mutability.mutable ? 'mutable' : 'immutable'}">
                                ${mutability.mutable ? 'Editable' : 'Read-only'}
                            </span>
                        </div>
                        <div class="property-value">
                            <input type="text" id="prop_${key}" value="${JSON.stringify(value)}" 
                                    onchange="updateComponentProperty('${key}', this.value)"
                                    ${mutability.mutable ? '' : 'disabled'}>
                            <button onclick="saveComponentProperty('${key}', this)" class="save-button"
                                    ${mutability.mutable ? '' : 'disabled'}>Save</button>
                            <button onclick="trackPropertyFromExplorer('${key}', '${component.id}', '${component.name}.${key}')" 
                                    class="track-button" title="Track this property in spreadsheet">
                                📊 Track
                            </button>
                        </div>
                    </div>
                `;
            }
        }
    }
    
    propertiesDiv.innerHTML = html;
}

async function checkPropertyMutability(blockId, propertyName) {
    try {
        const url = blockId 
            ? `/api/mutability?block_id=${blockId}&property_name=${propertyName}`
            : `/api/mutability?property_name=${propertyName}`;
        
        const response = await fetch(url);
        const result = await response.json();
        
        if (result.success) {
            return result;
        } else {
            // Default to mutable if check fails
            return { mutable: true, reason: 'Mutability check failed' };
        }
    } catch (error) {
        console.log('Failed to check mutability:', error);
        // Default to mutable if check fails
        return { mutable: true, reason: 'Mutability check failed' };
    }
}

async function updateComponentProperty(propertyName, newValue) {
    if (!selectedComponent) return;
    
    // Try to convert value to appropriate type
    try {
        if (newValue.replace('.', '').replace('-', '').isdigit()) {
            if ('.' in newValue) {
                newValue = parseFloat(newValue);
            } else {
                newValue = parseInt(newValue);
            }
        } else if (newValue.toLowerCase() === 'true' || newValue.toLowerCase() === 'false') {
            newValue = newValue.toLowerCase() === 'true';
        }
    } catch {
        // Keep as string if conversion fails
    }
    
    // Update the component data
    selectedComponent.data[propertyName] = newValue;
}

async function saveComponentProperty(propertyName, buttonElement) {
    if (!selectedComponent) return;
    
    const newValue = selectedComponent.data[propertyName];
    
    try {
        let response;
        
        if (selectedComponent.type === 'root_property') {
            // For root-level properties, use a different endpoint
            response = await fetch('/api/update_root_property', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    property_name: selectedComponent.name,
                    new_value: newValue
                })
            });
        } else {
            // For block properties, use the existing endpoint
            response = await fetch('/api/update_property', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    block_id: selectedComponent.id,
                    property_name: propertyName,
                    new_value: newValue
                })
            });
        }
        
        const result = await response.json();
        
        if (result.success) {
            // Show success message on button
            if (buttonElement) {
                const originalText = buttonElement.textContent;
                buttonElement.textContent = 'Saved!';
                buttonElement.style.background = '#28a745';
                setTimeout(() => {
                    buttonElement.textContent = originalText;
                    buttonElement.style.background = '';
                }, 2000);
            }
            
            // Show toast notification
            showToast(result.message, 'success');
            
            // Update the input field with the actual updated value
            if (result.updated_value !== undefined) {
                const inputField = document.getElementById(`prop_${propertyName}`);
                if (inputField) {
                    inputField.value = JSON.stringify(result.updated_value);
                }
                
                // Update the local component data to match the server
                if (selectedComponent.type === 'root_property') {
                    selectedComponent.data[selectedComponent.name] = result.updated_value;
                } else {
                    selectedComponent.data[propertyName] = result.updated_value;
                }
            }
            
            console.log('Property updated successfully:', result.message);
        } else {
            showToast('Error saving property: ' + result.error, 'error');
        }
    } catch (error) {
        showToast('Failed to save property: ' + error.message, 'error');
    }
}

function trackPropertyFromExplorer(propertyName, blockId, displayName) {
    // Normalize display name to match spreadsheet format
    let normalizedDisplayName = displayName;
    if (!blockId) {
        // For root properties, ensure we use the "(root)" suffix to match spreadsheet format
        if (!displayName.includes('(root)')) {
            normalizedDisplayName = `${displayName} (root)`;
        }
    }
    
    // Check if this property is already being tracked
    const existingRowId = findExistingTrackedProperty(propertyName, blockId);
    
    if (existingRowId) {
        showToast('This property is already being tracked in the spreadsheet', 'info');
        // Scroll to the existing row
        const row = document.getElementById(`row-${existingRowId}`);
        if (row) {
            row.scrollIntoView({ behavior: 'smooth', block: 'center' });
            row.style.backgroundColor = '#fff3cd';
            setTimeout(() => {
                row.style.backgroundColor = '';
            }, 2000);
        }
        return;
    }
    
    // Find an empty row or add a new one
    let targetRowId = null;
    for (const [rowId, data] of Object.entries(spreadsheetData)) {
        if (!data.name || data.name.trim() === '') {
            targetRowId = rowId;
            break;
        }
    }
    
    if (!targetRowId) {
        // Add a new row
        addSpreadsheetRow();
        // Get the ID of the newly added row
        const rows = document.querySelectorAll('#bomTableBody tr');
        targetRowId = rows[rows.length - 1].id.replace('row-', '');
    }
    
    // Set up the tracking data
    const propertyData = {
        name: propertyName,
        displayName: normalizedDisplayName,
        isBlock: blockId !== null,
        blockId: blockId,
        id: blockId
    };
    
    // Update the spreadsheet data
    spreadsheetData[targetRowId] = {
        name: propertyName,
        value: '',
        associatedProperty: propertyData,
        autoTrigger: false,
        lastAppliedValue: null
    };
    
    // Update the UI
    const row = document.getElementById(`row-${targetRowId}`);
    if (row) {
        const nameInput = row.querySelector('td:nth-child(1) input');
        const propertyInput = row.querySelector('td:nth-child(3) input');
        
        if (nameInput) nameInput.value = propertyName;
        if (propertyInput) propertyInput.value = displayName;
    }
    
    // Update the tracked properties display
    updateTrackedPropertiesDisplay();
    
    // Save state
    saveState();
    
    // Scroll to the spreadsheet
    const spreadsheetSection = document.querySelector('.bom-spreadsheet');
    if (spreadsheetSection) {
        spreadsheetSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    
    showToast(`Property "${propertyName}" is now being tracked in the spreadsheet`, 'success');
}

function findExistingTrackedProperty(propertyName, blockId) {
    for (const [rowId, data] of Object.entries(spreadsheetData)) {
        if (data.associatedProperty) {
            const prop = data.associatedProperty;
            // Check if this is the same property by name and block ID, regardless of display name
            if (prop.name === propertyName && prop.blockId === blockId) {
                return rowId;
            }
        }
    }
    return null;
}

function closeComponentEditor() {
    // Hide the component editor
    document.getElementById('componentEditor').style.display = 'none';
    
    // Clear the search input
    document.getElementById('searchInput').value = '';
    
    // Clear the selected component
    selectedComponent = null;
    
    // Show the dropdown list again
    document.getElementById('dropdownList').style.display = 'block';
    
    // Show a brief message
    showToast('Component editor closed', 'info');
}

// Close dropdown when clicking outside
document.addEventListener('click', function(event) {
    const dropdown = document.querySelector('.searchable-dropdown');
    if (!dropdown.contains(event.target)) {
        document.getElementById('dropdownList').style.display = 'none';
    }
});

// Load components when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Load saved state first
    loadState();
    
    // Initialize everything in the correct order
    initializeApplication();
});

async function initializeApplication() {
    try {
        // Load blocks and components first
        await loadBlocks();
        await loadComponents();
        
        // Create block ID to name mapping
        await createBlockIdToNameMapping();
        
        // Initialize spreadsheet after a short delay to ensure template properties are loaded
        setTimeout(() => {
            initializeSpreadsheet();
            
            // Setup state persistence after everything is initialized
            setupStatePersistence();
            
            // Update tracked properties display
            updateTrackedPropertiesDisplay();
            
            // Add event listener for auto-trigger toggle
            const autoSimToggle = document.getElementById('autoSimToggle');
            if (autoSimToggle) {
                autoSimToggle.addEventListener('change', function() {
                    updateTrackedPropertiesDisplay();
                });
            }
        }, 500);
        
        console.log('Application initialized successfully');
    } catch (error) {
        console.error('Error initializing application:', error);
        showToast('Error initializing application: ' + error.message, 'error');
    }
}

async function refreshTemplate() {
    const refreshBtn = document.getElementById('refreshTemplateBtn');
    refreshBtn.disabled = true;
    refreshBtn.textContent = '🔄 Refreshing...';
    
    try {
        const response = await fetch('/api/refresh_template', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast(`Template refreshed successfully! Template ID: ${result.template_id}`, 'success');
            
            // Reload components, blocks, and block mapping
            await loadComponents();
            await loadBlocks();
            await createBlockIdToNameMapping();
            
            // Refresh the tracked properties display with new mapping
            updateTrackedPropertiesDisplay();
        } else {
            showToast(`Failed to refresh template: ${result.error}`, 'error');
        }
    } catch (error) {
        showToast(`Error refreshing template: ${error.message}`, 'error');
    } finally {
        refreshBtn.disabled = false;
        refreshBtn.textContent = '🔄 Refresh Template';
    }
}

// BOM Spreadsheet Functions
async function initializeSpreadsheet() {
    console.log('Initializing spreadsheet...');
    
    // Load template properties first
    await loadTemplateProperties();
    
    // Only add initial rows if we don't have saved data
    if (Object.keys(spreadsheetData).length === 0) {
        // Add 5 initial rows
        for (let i = 0; i < 5; i++) {
            addSpreadsheetRow();
        }
    } else {
        // Restore the saved spreadsheet UI
        restoreSpreadsheetUI();
    }
    
    console.log('Spreadsheet initialized with', allTemplateProperties.length, 'properties available');
}

function addSpreadsheetRow(restoreRowId = null, restoreData = null) {
    const tbody = document.getElementById('bomTableBody');
    const rowId = restoreRowId || Math.floor(Math.random() * 1000000); // Use provided ID or generate new one
    
    const row = document.createElement('tr');
    row.id = `row-${rowId}`;
    row.innerHTML = `
        <td>
            <input type="text" class="spreadsheet-input" placeholder="Variable name" 
                    onchange="updateSpreadsheetData('${rowId}', 'name', this.value)">
        </td>
        <td>
            <input type="text" class="spreadsheet-input" placeholder="Input value" 
                    onchange="updateSpreadsheetData('${rowId}', 'value', this.value)">
        </td>
        <td>
            <div class="property-selector">
                <input type="text" placeholder="Click to select template property" readonly
                        onclick="showPropertyDropdown('${rowId}')">
                <div class="property-dropdown" id="dropdown-${rowId}"></div>
            </div>
        </td>
        <td>
            <label class="toggle-container-small">
                <input type="checkbox" id="autoTrigger-${rowId}" 
                        onchange="updateSpreadsheetData('${rowId}', 'autoTrigger', this.checked)">
                <span class="toggle-slider-small"></span>
            </label>
        </td>
        <td>
            <div class="action-buttons">
                <button class="action-btn save" onclick="saveProperty('${rowId}')">
                    💾 Save
                </button>
                <button class="action-btn delete" onclick="deleteRow('${rowId}')">
                    🗑️
                </button>
            </div>
        </td>
    `;
    
    tbody.appendChild(row);
    
    // Initialize data for this row
    if (restoreData) {
        spreadsheetData[rowId] = restoreData;
        
        // Restore the input values
        const nameInput = row.querySelector('td:nth-child(1) input');
        const valueInput = row.querySelector('td:nth-child(2) input');
        const propertyInput = row.querySelector('td:nth-child(3) input');
        
        if (nameInput && restoreData.name) {
            nameInput.value = restoreData.name;
        }
        if (valueInput && restoreData.value) {
            valueInput.value = restoreData.value;
        }
        if (propertyInput && restoreData.associatedProperty) {
            propertyInput.value = restoreData.associatedProperty.displayName;
        }
    } else {
        spreadsheetData[rowId] = {
            name: '',
            value: '',
            associatedProperty: null,
            lastAppliedValue: null
        };
    }
    
    console.log('Added spreadsheet row with ID:', rowId, restoreData ? '(restored)' : '(new)');
}

function deleteRow(rowId) {
    const row = document.getElementById(`row-${rowId}`);
    if (row) {
        row.remove();
        delete spreadsheetData[rowId];
        saveState();
    }
}

function clearSpreadsheet() {
    if (confirm('Are you sure you want to clear all rows?')) {
        const tbody = document.getElementById('bomTableBody');
        tbody.innerHTML = '';
        spreadsheetData = {};
        
        // Re-add 5 empty rows
        for (let i = 0; i < 5; i++) {
            addSpreadsheetRow();
        }
        
        saveState();
    }
}

async function loadTemplateProperties() {
    try {
        console.log('Loading template properties...');
        const response = await fetch('/api/template_structure');
        const result = await response.json();
        
        if (result.success) {
            allTemplateProperties = extractAllProperties(result.data);
            console.log('Loaded template properties:', allTemplateProperties);
            console.log('Total properties found:', allTemplateProperties.length);
        } else {
            console.error('Failed to load template structure:', result.error);
        }
    } catch (error) {
        console.error('Failed to load template properties:', error);
    }
}

function extractAllProperties(data, prefix = '') {
    let properties = [];
    
    if (typeof data === 'object' && data !== null) {
        if (Array.isArray(data)) {
            data.forEach((item, index) => {
                const path = prefix ? `${prefix}.${index}` : `${index}`;
                if (typeof item === 'object' && item !== null) {
                    if (item.id && item.type) {
                        // This is a block/component - add it and also drill into its properties
                        properties.push({
                            path: path,
                            id: item.id,
                            name: item.name || `${item.type}_${item.id}`,
                            type: item.type,
                            displayName: `${item.name || item.type} (${item.id})`,
                            isBlock: true
                        });
                        
                        // Drill into the block's properties
                        if (item.data) {
                            Object.keys(item.data).forEach(propKey => {
                                if (!propKey.startsWith('_') && propKey !== 'id' && propKey !== 'type') {
                                    const propValue = item.data[propKey];
                                    const propPath = `${path}.${propKey}`;
                                    properties.push({
                                        path: propPath,
                                        id: item.id,
                                        name: propKey,
                                        value: propValue,
                                        displayName: `${item.name || item.type}.${propKey}`,
                                        isBlock: false,
                                        blockId: item.id
                                    });
                                }
                            });
                        }
                    }
                    // Recursively extract from nested objects
                    properties = properties.concat(extractAllProperties(item, path));
                }
            });
        } else {
            Object.keys(data).forEach(key => {
                const path = prefix ? `${prefix}.${key}` : key;
                const value = data[key];
                
                if (typeof value === 'object' && value !== null) {
                    if (value.id && value.type) {
                        // This is a block/component - add it and also drill into its properties
                        properties.push({
                            path: path,
                            id: value.id,
                            name: value.name || `${value.type}_${value.id}`,
                            type: value.type,
                            displayName: `${value.name || value.type} (${value.id})`,
                            isBlock: true
                        });
                        
                        // Drill into the block's properties
                        if (value.data) {
                            Object.keys(value.data).forEach(propKey => {
                                if (!propKey.startsWith('_') && propKey !== 'id' && propKey !== 'type') {
                                    const propValue = value.data[propKey];
                                    const propPath = `${path}.${propKey}`;
                                    properties.push({
                                        path: propPath,
                                        id: value.id,
                                        name: propKey,
                                        value: propValue,
                                        displayName: `${value.name || value.type}.${propKey}`,
                                        isBlock: false,
                                        blockId: value.id
                                    });
                                }
                            });
                        }
                    }
                    // Recursively extract from nested objects
                    properties = properties.concat(extractAllProperties(value, path));
                } else if (prefix === '' && (typeof value === 'number' || typeof value === 'string' || typeof value === 'boolean')) {
                    // Root-level properties
                    properties.push({
                        path: path,
                        name: key,
                        value: value,
                        displayName: `${key} (root)`,
                        isBlock: false
                    });
                }
            });
        }
    }
    
    return properties;
}

function showPropertyDropdown(rowId) {
    console.log('=== showPropertyDropdown called ===');
    console.log('Row ID:', rowId, 'Type:', typeof rowId);
    console.log('Available properties:', allTemplateProperties);
    console.log('Properties length:', allTemplateProperties ? allTemplateProperties.length : 'undefined');
    console.log('Block ID to name mapping:', blockIdToNameMapping);
    
    const dropdown = document.getElementById(`dropdown-${rowId}`);
    const input = dropdown ? dropdown.previousElementSibling : null;
    
    console.log('Found dropdown:', dropdown);
    console.log('Found input:', input);
    
    if (!dropdown) {
        console.error('Could not find dropdown for row:', rowId);
        return;
    }
    
    // Clear previous content
    dropdown.innerHTML = '';
    
    // Add search functionality
    const searchInput = document.createElement('input');
    searchInput.type = 'text';
    searchInput.placeholder = 'Search properties...';
    searchInput.className = 'spreadsheet-input';
    searchInput.style = 'margin-bottom: 8px;';
    searchInput.onkeyup = function() {
        filterPropertyDropdown(dropdown, this.value);
    };
    dropdown.appendChild(searchInput);
    
    // Add property items
    if (allTemplateProperties && allTemplateProperties.length > 0) {
        // Group properties by block using the mapping
        const groupedProperties = groupPropertiesByBlock(allTemplateProperties);
        
        // Add all properties in a clean, organized way without technical labels
        Object.keys(groupedProperties).forEach(blockKey => {
            const blockGroup = groupedProperties[blockKey];
            const blockInfo = blockGroup.blockInfo;
            
            // Create section header (only if it's not root properties)
            if (blockKey !== 'root') {
                const blockHeader = document.createElement('div');
                blockHeader.className = 'property-item';
                blockHeader.style = 'background: #e9ecef; font-weight: bold; color: #495057;';
                blockHeader.innerHTML = `<div>🔧 ${blockInfo.displayName}</div>`;
                dropdown.appendChild(blockHeader);
            }
            
            // Add properties for this section
            blockGroup.properties.forEach(prop => {
                const item = document.createElement('div');
                item.className = 'property-item';
                item.style = 'padding-left: 20px;';
                item.innerHTML = `
                    <div>${prop.name || prop.displayName}</div>
                    <div class="property-path">${prop.path}</div>
                `;
                item.onclick = function(e) {
                    e.stopPropagation();
                    console.log('Property item clicked:', prop);
                    selectProperty(rowId, prop);
                };
                dropdown.appendChild(item);
            });
        });
        
        // Add block components with expand functionality (for blocks that don't have drilled properties)
        const blockProperties = allTemplateProperties.filter(p => p.isBlock);
        if (blockProperties.length > 0) {
            const compHeader = document.createElement('div');
            compHeader.className = 'property-item';
            compHeader.style = 'background: #f8f9fa; font-weight: bold; color: #495057;';
            compHeader.innerHTML = '<div>📦 Components (Click to expand)</div>';
            dropdown.appendChild(compHeader);
            
            blockProperties.forEach(prop => {
                const item = document.createElement('div');
                item.className = 'property-item';
                item.style = 'padding-left: 20px;';
                item.innerHTML = `
                    <div>${prop.displayName} ▶️</div>
                    <div class="property-path">${prop.path}</div>
                `;
                item.onclick = function(e) {
                    e.stopPropagation();
                    console.log('Block component clicked, expanding:', prop);
                    expandBlockComponent(rowId, prop, dropdown);
                };
                dropdown.appendChild(item);
            });
        }
    } else {
        // Show loading message if no properties available
        const loadingItem = document.createElement('div');
        loadingItem.className = 'property-item';
        loadingItem.innerHTML = '<div>Loading properties...</div>';
        dropdown.appendChild(loadingItem);
    }
    
    // Check available space and position dropdown accordingly
    const rect = dropdown.getBoundingClientRect();
    const viewportHeight = window.innerHeight;
    const dropdownHeight = 200; // max-height of dropdown
    
    // If there's not enough space below, show dropdown above
    if (rect.bottom + dropdownHeight > viewportHeight) {
        dropdown.classList.add('overflow-up');
    } else {
        dropdown.classList.remove('overflow-up');
    }
    
    dropdown.style.display = 'block';
    
    // Close dropdown when clicking outside
    setTimeout(() => {
        document.addEventListener('click', function closeDropdown(e) {
            if (!dropdown.contains(e.target) && !input.contains(e.target)) {
                dropdown.style.display = 'none';
                document.removeEventListener('click', closeDropdown);
            }
        });
    }, 100);
}

async function expandBlockComponent(rowId, blockProp, dropdown) {
    console.log('Expanding block component:', blockProp);
    
    try {
        // Get the block's properties from the server
        const response = await fetch(`/api/block/${blockProp.id}/properties`);
        const result = await response.json();
        
        if (result && typeof result === 'object') {
            // Clear the dropdown and show block properties
            dropdown.innerHTML = '';
            
            // Add back button
            const backButton = document.createElement('div');
            backButton.className = 'property-item';
            backButton.style = 'background: #e9ecef; font-weight: bold; color: #495057; cursor: pointer;';
            backButton.innerHTML = '<div>← Back to all properties</div>';
            backButton.onclick = function(e) {
                e.stopPropagation();
                showPropertyDropdown(rowId);
            };
            dropdown.appendChild(backButton);
            
            // Add header
            const header = document.createElement('div');
            header.className = 'property-item';
            header.style = 'background: #f8f9fa; font-weight: bold; color: #495057;';
            header.innerHTML = `<div>🔧 ${blockProp.displayName} Properties</div>`;
            dropdown.appendChild(header);
            
            // Add each property
            Object.keys(result).forEach(propKey => {
                if (!propKey.startsWith('_') && propKey !== 'id' && propKey !== 'type') {
                    const propValue = result[propKey];
                    const item = document.createElement('div');
                    item.className = 'property-item';
                    item.style = 'padding-left: 20px;';
                    item.innerHTML = `
                        <div>${propKey}</div>
                        <div class="property-path">Current: ${JSON.stringify(propValue)}</div>
                    `;
                    item.onclick = function(e) {
                        e.stopPropagation();
                        const property = {
                            path: `${blockProp.path}.${propKey}`,
                            id: blockProp.id,
                            name: propKey,
                            value: propValue,
                            displayName: `${blockProp.displayName}.${propKey}`,
                            isBlock: false,
                            blockId: blockProp.id
                        };
                        console.log('Block property selected:', property);
                        selectProperty(rowId, property);
                    };
                    dropdown.appendChild(item);
                }
            });
        } else {
            console.error('Failed to get block properties:', result);
        }
    } catch (error) {
        console.error('Error expanding block component:', error);
        // Show error in dropdown
        dropdown.innerHTML = '<div class="property-item">Error loading block properties</div>';
    }
}

function filterPropertyDropdown(dropdown, searchTerm) {
    const items = dropdown.querySelectorAll('.property-item');
    const searchLower = searchTerm.toLowerCase();
    
    items.forEach(item => {
        const text = item.textContent.toLowerCase();
        if (text.includes(searchLower)) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
}

function selectProperty(rowId, property) {
    console.log('Selecting property:', property, 'for row:', rowId);
    
    const input = document.querySelector(`#row-${rowId} .property-selector input`);
    const dropdown = document.getElementById(`dropdown-${rowId}`);
    
    if (!input) {
        console.error('Could not find input field for row:', rowId);
        return;
    }
    
    if (!dropdown) {
        console.error('Could not find dropdown for row:', rowId);
        return;
    }
    
    // Update the input field
    input.value = property.displayName;
    
    // Update the spreadsheet data
    if (!spreadsheetData[rowId]) {
        spreadsheetData[rowId] = {};
    }
    spreadsheetData[rowId].associatedProperty = property;
    
    // Hide the dropdown
    dropdown.style.display = 'none';
    
    // Update tracked properties display
    updateTrackedPropertiesDisplay();
    
    // Show success message
    showToast(`Associated with ${property.displayName}`, 'success');
    
    // Apply the current value if auto-sim is enabled
    if (document.getElementById('autoSimToggle').checked) {
        applySpreadsheetChanges();
    }
}

function updateSpreadsheetData(rowId, field, value) {
    if (!spreadsheetData[rowId]) {
        spreadsheetData[rowId] = {};
    }
    spreadsheetData[rowId][field] = value;
    
    // Update tracked properties display
    updateTrackedPropertiesDisplay();
    
    // Check if this specific row has auto-trigger enabled and we have both name and associated property
    if (spreadsheetData[rowId].autoTrigger && 
        spreadsheetData[rowId].name && 
        spreadsheetData[rowId].associatedProperty) {
        applySpreadsheetChanges();
    }
}

function updateTrackedPropertiesDisplay() {
    const container = document.getElementById('trackedPropertiesContainer');
    const noTrackedDiv = document.getElementById('noTrackedProperties');
    
    if (!container) return;
    
    // Get tracked properties (rows with associated properties) - prevent duplicates
    const trackedProperties = [];
    const seenProperties = new Set(); // Track unique property associations
    
    for (const [rowId, data] of Object.entries(spreadsheetData)) {
        if (data.name && data.associatedProperty) {
            // Create a unique key for this property association using name and block ID
            const propertyKey = `${data.associatedProperty.blockId || 'root'}-${data.associatedProperty.name}`;
            
            // Only add if we haven't seen this property before
            if (!seenProperties.has(propertyKey)) {
                seenProperties.add(propertyKey);
                trackedProperties.push({
                    rowId: rowId,
                    ...data
                });
            }
        }
    }
    
    if (trackedProperties.length === 0) {
        container.innerHTML = '';
        if (noTrackedDiv) noTrackedDiv.style.display = 'block';
        return;
    }
    
    if (noTrackedDiv) noTrackedDiv.style.display = 'none';
    
    // Group tracked properties by block
    const groupedTrackedProperties = groupPropertiesByBlock(trackedProperties);
    
    let html = '';
    
    // Display root properties first
    if (groupedTrackedProperties['root']) {
        html += `
            <div class="tracked-property-group">
                <div class="tracked-property-group-header">
                    <h4>🌐 Template Properties</h4>
                </div>
        `;
        
        groupedTrackedProperties['root'].properties.forEach(prop => {
            const hasAutoTrigger = prop.autoTrigger && prop.value && prop.value.trim() !== '';
            
            html += `
                <div class="tracked-property-block">
                    <div class="tracked-property-header">
                        <div class="tracked-property-name">
                            ${prop.name}
                            ${hasAutoTrigger ? '<span class="auto-trigger-badge">🔄 Auto</span>' : ''}
                        </div>
                        <div class="tracked-property-actions">
                            <button class="edit-btn" onclick="editTrackedProperty('${prop.rowId}')">
                                ✏️ Edit
                            </button>
                            <button class="delete-btn" onclick="deleteTrackedProperty('${prop.rowId}')">
                                🗑️ Stop Tracking
                            </button>
                        </div>
                    </div>
                    <div class="tracked-property-details">
                        <div class="tracked-property-item">
                            <div class="tracked-property-label">Variable Name</div>
                            <div class="tracked-property-value">${prop.name}</div>
                        </div>
                        <div class="tracked-property-item">
                            <div class="tracked-property-label">Current Value</div>
                            <div class="tracked-property-value">${prop.value || 'Not set'}</div>
                        </div>
                        <div class="tracked-property-item">
                            <div class="tracked-property-label">Template Property</div>
                            <div class="tracked-property-value">${prop.associatedProperty.displayName}</div>
                        </div>
                        <div class="tracked-property-item">
                            <div class="tracked-property-label">Last Applied Value</div>
                            <div class="tracked-property-value">${prop.lastAppliedValue !== null ? prop.lastAppliedValue : 'Not applied'}</div>
                        </div>
                        <div class="tracked-property-item">
                            <div class="tracked-property-label">Auto-Trigger Status</div>
                            <div class="tracked-property-value">
                                ${hasAutoTrigger ? 
                                    '<span style="color: #28a745; font-weight: bold;">🔄 Active</span>' : 
                                    '<span style="color: #6c757d;">⏸️ Inactive</span>'
                                }
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += `</div>`;
    }
    
    // Display block properties grouped by block
    Object.keys(groupedTrackedProperties).forEach(blockKey => {
        if (blockKey !== 'root') {
            const blockGroup = groupedTrackedProperties[blockKey];
            const blockInfo = blockGroup.blockInfo;
            
            html += `
                <div class="tracked-property-group">
                    <div class="tracked-property-group-header">
                        <h4>🔧 ${blockInfo.displayName}</h4>
                        <span class="block-type-badge">${blockInfo.type}</span>
                    </div>
            `;
            
            blockGroup.properties.forEach(prop => {
                const hasAutoTrigger = prop.autoTrigger && prop.value && prop.value.trim() !== '';
                
                html += `
                    <div class="tracked-property-block">
                        <div class="tracked-property-header">
                            <div class="tracked-property-name">
                                ${prop.name}
                                ${hasAutoTrigger ? '<span class="auto-trigger-badge">🔄 Auto</span>' : ''}
                            </div>
                            <div class="tracked-property-actions">
                                <button class="edit-btn" onclick="editTrackedProperty('${prop.rowId}')">
                                    ✏️ Edit
                                </button>
                                <button class="delete-btn" onclick="deleteTrackedProperty('${prop.rowId}')">
                                    🗑️ Stop Tracking
                                </button>
                            </div>
                        </div>
                        <div class="tracked-property-details">
                            <div class="tracked-property-item">
                                <div class="tracked-property-label">Variable Name</div>
                                <div class="tracked-property-value">${prop.name}</div>
                            </div>
                            <div class="tracked-property-item">
                                <div class="tracked-property-label">Current Value</div>
                                <div class="tracked-property-value">${prop.value || 'Not set'}</div>
                            </div>
                            <div class="tracked-property-item">
                                <div class="tracked-property-label">Template Property</div>
                                <div class="tracked-property-value">${prop.associatedProperty.displayName}</div>
                            </div>
                            <div class="tracked-property-item">
                                <div class="tracked-property-label">Last Applied Value</div>
                                <div class="tracked-property-value">${prop.lastAppliedValue !== null ? prop.lastAppliedValue : 'Not applied'}</div>
                            </div>
                            <div class="tracked-property-item">
                                <div class="tracked-property-label">Auto-Trigger Status</div>
                                <div class="tracked-property-value">
                                    ${hasAutoTrigger ? 
                                        '<span style="color: #28a745; font-weight: bold;">🔄 Active</span>' : 
                                        '<span style="color: #6c757d;">⏸️ Inactive</span>'
                                    }
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            html += `</div>`;
        }
    });
    
    container.innerHTML = html;
}

function editTrackedProperty(rowId) {
    // Find the row in the spreadsheet and focus on it
    const row = document.getElementById(`row-${rowId}`);
    if (row) {
        row.scrollIntoView({ behavior: 'smooth', block: 'center' });
        // Highlight the row briefly
        row.style.backgroundColor = '#fff3cd';
        setTimeout(() => {
            row.style.backgroundColor = '';
        }, 2000);
    }
}

function deleteTrackedProperty(rowId) {
    if (confirm('Are you sure you want to stop tracking this property? This will remove the association but keep the row.')) {
        // Clear the associated property but keep the row
        if (spreadsheetData[rowId]) {
            spreadsheetData[rowId].associatedProperty = null;
            spreadsheetData[rowId].lastAppliedValue = null;
            
            // Clear the property input in the spreadsheet
            const row = document.getElementById(`row-${rowId}`);
            if (row) {
                const propertyInput = row.querySelector('td:nth-child(3) input');
                if (propertyInput) {
                    propertyInput.value = '';
                }
            }
            
            // Update the display
            updateTrackedPropertiesDisplay();
            saveState();
            
            showToast('Property tracking stopped', 'info');
        }
    }
}

async function applySpreadsheetChanges() {
    let hasChanges = false;
    let hasErrors = false;
    
    for (const [rowId, data] of Object.entries(spreadsheetData)) {
        // Only process rows that have auto-trigger enabled
        if (data.autoTrigger && data.name && data.value && data.associatedProperty) {
            const currentValue = parseValue(data.value);
            const lastValue = data.lastAppliedValue;
            
            // Check if value has actually changed locally
            if (JSON.stringify(currentValue) !== JSON.stringify(lastValue)) {
                try {
                    let updateResponse;
                    
                    if (data.associatedProperty.isBlock) {
                        // Update block property
                        updateResponse = await fetch('/api/update_property', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                block_id: data.associatedProperty.id,
                                property_name: data.associatedProperty.name,
                                new_value: currentValue
                            })
                        });
                    } else if (data.associatedProperty.blockId) {
                        // Update block property (drilled down)
                        updateResponse = await fetch('/api/update_property', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                block_id: data.associatedProperty.blockId,
                                property_name: data.associatedProperty.name,
                                new_value: currentValue
                            })
                        });
                    } else {
                        // Update root property
                        updateResponse = await fetch('/api/update_root_property', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                property_name: data.associatedProperty.name,
                                new_value: currentValue
                            })
                        });
                    }
                    
                    const updateResult = await updateResponse.json();
                    
                    if (updateResult.success) {
                        // Check if the property actually changed on the server
                        const actualChanged = updateResult.updated_value !== data.lastAppliedValue;
                        
                        if (actualChanged) {
                            hasChanges = true;
                            showToast(`Updated ${data.name} to ${data.value}`, 'success');
                        } else {
                            showToast(`No change needed for ${data.name}`, 'info');
                        }
                        
                        // Update last applied value with the actual server value
                        spreadsheetData[rowId].lastAppliedValue = updateResult.updated_value;
                    } else {
                        hasErrors = true;
                        showToast(`Failed to update ${data.name}: ${updateResult.error}`, 'error');
                    }
                } catch (error) {
                    hasErrors = true;
                    showToast(`Failed to update ${data.name}: ${error.message}`, 'error');
                }
            }
        }
    }
    
    // Only trigger simulation if we actually had changes on the server AND no errors occurred
    if (hasChanges && !hasErrors) {
        setTimeout(() => {
            startSimulation();
        }, 1000); // Small delay to ensure all updates are processed
    } else if (hasErrors) {
        showToast('Simulation skipped due to update errors', 'error');
    }
}

function parseValue(value) {
    // Try to convert to appropriate type
    if (value === 'true' || value === 'false') {
        return value === 'true';
    }
    if (!isNaN(value) && value !== '') {
        return Number(value);
    }
    return value;
}

async function saveProperty(rowId) {
    console.log('=== saveProperty called ===');
    console.log('Row ID:', rowId);
    
    const data = spreadsheetData[rowId];
    console.log('Row data:', data);
    
    if (!data || !data.associatedProperty) {
        console.log('No associated property found');
        showToast('Please select a template property first', 'error');
        return;
    }
    
    if (!data.value || data.value.trim() === '') {
        console.log('No value to save');
        showToast('Please enter a value to save', 'error');
        return;
    }
    
    try {
        const property = data.associatedProperty;
        const value = parseValue(data.value);
        
        console.log('Property to save:', property);
        console.log('Value to save:', value, 'Type:', typeof value);
        
        let endpoint, payload;
        
        if (property.blockId) {
            // Save to block property
            endpoint = '/api/update_property';
            payload = {
                block_id: property.blockId,
                property_name: property.name,
                new_value: value
            };
            console.log('Saving to block property:', payload);
        } else {
            // Save to root property
            endpoint = '/api/update_root_property';
            payload = {
                property_name: property.name,
                new_value: value
            };
            console.log('Saving to root property:', payload);
        }
        
        console.log('Making request to:', endpoint);
        console.log('Payload:', JSON.stringify(payload));
        
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        console.log('Response status:', response.status);
        console.log('Response ok:', response.ok);
        
        const result = await response.json();
        console.log('Response result:', result);
        
        if (result.success) {
            // Update the last applied value to prevent auto-trigger
            data.lastAppliedValue = data.value;
            
            // Refresh blocks to get updated values
            try {
                console.log('Refreshing blocks to get updated values...');
                const blocksResponse = await fetch('/api/blocks');
                const blocksResult = await blocksResponse.json();
                
                if (blocksResult && typeof blocksResult === 'object') {
                    // Find the updated value in the refreshed data
                    let updatedValue = null;
                    let foundInBlock = false;
                    
                    if (property.blockId) {
                        // Look for the block property
                        for (const blockType in blocksResult) {
                            const blocks = blocksResult[blockType];
                            for (const block of blocks) {
                                if (block.id === property.blockId && block.data && block.data[property.name] !== undefined) {
                                    updatedValue = block.data[property.name];
                                    foundInBlock = true;
                                    break;
                                }
                            }
                            if (foundInBlock) break;
                        }
                    } else {
                        // Look for root property (this might need adjustment based on actual data structure)
                        // For now, we'll use the result from the save operation
                        updatedValue = result.updated_value;
                    }
                    
                    const valueDisplay = updatedValue !== null ? ` (now: ${updatedValue})` : '';
                    showToast(`Successfully saved ${data.name} to ${property.displayName}${valueDisplay}`, 'success');
                } else {
                    showToast(`Successfully saved ${data.name} to ${property.displayName}`, 'success');
                }
            } catch (refreshError) {
                console.error('Error refreshing blocks:', refreshError);
                showToast(`Successfully saved ${data.name} to ${property.displayName}`, 'success');
            }
        } else {
            console.error('Save failed:', result.error);
            showToast(`Failed to save: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('Error saving property:', error);
        console.error('Error details:', {
            message: error.message,
            stack: error.stack
        });
        showToast(`Error saving property: ${error.message}`, 'error');
    }
}

// Statistics Functions
function toggleStatisticsSection() {
    const statsSection = document.querySelector('.simulation-statistics');
    if (statsSection.style.display === 'none') {
        statsSection.style.display = 'block';
        loadAvailableStreams();
        showToast('Statistics section opened', 'info');
    } else {
        statsSection.style.display = 'none';
        showToast('Statistics section closed', 'info');
    }
}



async function fetchSimulationStats() {
    const simulationId = document.getElementById('statsSimulationId').value.trim();
    const waitForStats = document.getElementById('statsWaitToggle').checked;
    const resultsDiv = document.getElementById('statisticsResults');
    const fetchBtn = document.getElementById('fetchStatsBtn');
    
    // Show loading state
    resultsDiv.innerHTML = '<div class="statistics-loading">Fetching statistics...</div>';
    fetchBtn.disabled = true;
    
    try {
        const response = await fetch('/api/simulation_statistics', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                simulation_id: simulationId || null,
                wait: waitForStats,
                streams: null  // Get all available statistics
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            displayStatistics(result.statistics, result.simulation_id);
            showToast('Statistics fetched successfully', 'success');
        } else {
            resultsDiv.innerHTML = `<div class="statistics-error">❌ Failed to fetch statistics: ${result.error}</div>`;
            showToast('Failed to fetch statistics: ' + result.error, 'error');
        }
    } catch (error) {
        resultsDiv.innerHTML = `<div class="statistics-error">❌ Error fetching statistics: ${error.message}</div>`;
        showToast('Error fetching statistics: ' + error.message, 'error');
    } finally {
        fetchBtn.disabled = false;
    }
}

function displayStatistics(statistics, simulationId) {
    const resultsDiv = document.getElementById('statisticsResults');
    
    if (!statistics || Object.keys(statistics).length === 0) {
        resultsDiv.innerHTML = '<div class="no-statistics">No statistics available for this simulation.</div>';
        return;
    }
    
    // First, get agent information to map IDs to names
    getAgentMapping().then(agentMapping => {
        let html = `
            <div class="statistics-success">
                <h4>✅ Statistics Retrieved Successfully</h4>
                <p><strong>Simulation ID:</strong> ${simulationId || 'Latest'}</p>
                <p><strong>Total Statistics:</strong> ${Object.keys(statistics).length}</p>
            </div>
        `;
        
        // Group statistics by agent first, then by block within each agent
        const groupedStats = groupStatisticsByAgentAndBlock(statistics, agentMapping);
        
        // Display statistics grouped by agent, then by block
        Object.keys(groupedStats).forEach((agentName, agentIndex) => {
            const agentData = groupedStats[agentName];
            const agentId = `agent-${agentIndex}`;
            
            html += `
                <div class="agent-statistics-section">
                    <div class="agent-statistics-header" onclick="toggleSection('${agentId}')">
                        <h3>📊 ${agentName}</h3>
                        <span class="toggle-icon" id="toggle-${agentId}">▼</span>
                    </div>
                    <div class="agent-statistics-content" id="content-${agentId}">
            `;
            
            // Display root properties first (if any)
            if (agentData.rootProperties && agentData.rootProperties.length > 0) {
                const rootId = `${agentId}-root`;
                html += `
                    <div class="block-statistics-subsection">
                        <div class="block-statistics-header" onclick="toggleSection('${rootId}')">
                            <h4>🌐 Template Properties (${agentData.rootProperties.length})</h4>
                            <span class="toggle-icon" id="toggle-${rootId}">▼</span>
                        </div>
                        <div class="block-statistics-content" id="content-${rootId}">
                            <table class="statistics-table">
                                <thead>
                                    <tr>
                                        <th>Property</th>
                                        <th>Value</th>
                                        <th>Type</th>
                                    </tr>
                                </thead>
                                <tbody>
                `;
                
                agentData.rootProperties.forEach(stat => {
                    const valueType = getValueType(stat.value);
                    const formattedValue = formatValue(stat.value);
                    
                    html += `
                        <tr>
                            <td><strong>${stat.property}</strong></td>
                            <td class="statistic-value ${valueType}">${formattedValue}</td>
                            <td><span class="badge badge-${valueType}">${valueType}</span></td>
                        </tr>
                    `;
                });
                
                html += `
                                </tbody>
                            </table>
                        </div>
                    </div>
                `;
            }
            
            // Display block properties grouped by block
            Object.keys(agentData.blocks).forEach((blockName, blockIndex) => {
                const blockStats = agentData.blocks[blockName];
                const blockId = `${agentId}-block-${blockIndex}`;
                
                html += `
                    <div class="block-statistics-subsection">
                        <div class="block-statistics-header" onclick="toggleSection('${blockId}')">
                            <h4>🔧 ${blockName} (${blockStats.length})</h4>
                            <span class="toggle-icon" id="toggle-${blockId}">▼</span>
                        </div>
                        <div class="block-statistics-content" id="content-${blockId}">
                            <table class="statistics-table">
                                <thead>
                                    <tr>
                                        <th>Property</th>
                                        <th>Value</th>
                                        <th>Type</th>
                                    </tr>
                                </thead>
                                <tbody>
                `;
                
                blockStats.forEach(stat => {
                    const valueType = getValueType(stat.value);
                    const formattedValue = formatValue(stat.value);
                    
                    html += `
                        <tr>
                            <td><strong>${stat.property}</strong></td>
                            <td class="statistic-value ${valueType}">${formattedValue}</td>
                            <td><span class="badge badge-${valueType}">${valueType}</span></td>
                        </tr>
                    `;
                });
                
                html += `
                                </tbody>
                            </table>
                        </div>
                    </div>
                `;
            });
            
            html += `
                    </div>
                </div>
            `;
        });
        
        resultsDiv.innerHTML = html;
    }).catch(error => {
        // Fallback to original display if agent mapping fails
        console.error('Error getting agent mapping:', error);
        displayStatisticsFallback(statistics, simulationId);
    });
}

async function getAgentMapping() {
    try {
        const response = await fetch('/api/available_streams');
        const result = await response.json();
        
        if (result.success) {
            const agentMapping = {};
            result.streams.forEach(stream => {
                if (stream.agent_id && stream.display_name) {
                    // Extract agent name from display name (e.g., "My In-orbit Spacecraft - Position" -> "My In-orbit Spacecraft")
                    const agentName = stream.display_name.split(' - ')[0];
                    agentMapping[stream.agent_id] = agentName;
                }
            });
            return agentMapping;
        }
    } catch (error) {
        console.error('Error fetching agent mapping:', error);
    }
    
    return {};
}

function groupStatisticsByAgentAndBlock(statistics, agentMapping) {
    const groupedStats = {};
    
    // Recursively process statistics and group by agent first, then by block
    function processStatisticsRecursive(obj, prefix = '') {
        for (const [key, value] of Object.entries(obj)) {
            const fullKey = prefix ? `${prefix}.${key}` : key;
            
            if (getValueType(value) === 'object' && value !== null) {
                // Continue recursion for nested objects
                processStatisticsRecursive(value, fullKey);
            } else {
                // This is a leaf node (actual statistic value)
                const agentId = extractAgentId(fullKey);
                const agentName = agentMapping[agentId] || `Unknown Agent (${agentId})`;
                const blockId = extractBlockId(fullKey);
                const blockInfo = getBlockNameById(blockId);
                const propertyName = extractPropertyName(fullKey);
                
                // Initialize agent structure if it doesn't exist
                if (!groupedStats[agentName]) {
                    groupedStats[agentName] = {
                        rootProperties: [],
                        blocks: {}
                    };
                }
                
                // Determine if this is a root property or block property
                const isRootProperty = isRootLevelProperty(fullKey, agentId);
                
                if (isRootProperty) {
                    // This is a root-level property for the agent
                    groupedStats[agentName].rootProperties.push({
                        property: propertyName,
                        value: value,
                        fullKey: fullKey
                    });
                } else {
                    // This is a block property
                    const blockKey = blockInfo.name;
                    
                    if (!groupedStats[agentName].blocks[blockKey]) {
                        groupedStats[agentName].blocks[blockKey] = [];
                    }
                    
                    groupedStats[agentName].blocks[blockKey].push({
                        property: propertyName,
                        value: value,
                        fullKey: fullKey,
                        blockInfo: blockInfo
                    });
                }
            }
        }
    }
    
    processStatisticsRecursive(statistics);
    return groupedStats;
}

function groupStatisticsByBlock(statistics) {
    const groupedStats = {};
    
    // Recursively process statistics and group by block
    function processStatisticsRecursive(obj, prefix = '') {
        for (const [key, value] of Object.entries(obj)) {
            const fullKey = prefix ? `${prefix}.${key}` : key;
            
            if (getValueType(value) === 'object' && value !== null) {
                // Continue recursion for nested objects
                processStatisticsRecursive(value, fullKey);
            } else {
                // This is a leaf node (actual statistic value)
                const blockId = extractBlockId(fullKey);
                const blockInfo = getBlockNameById(blockId);
                const propertyName = extractPropertyName(fullKey);
                
                const blockKey = blockInfo.name;
                
                if (!groupedStats[blockKey]) {
                    groupedStats[blockKey] = [];
                }
                
                groupedStats[blockKey].push({
                    property: propertyName,
                    value: value,
                    fullKey: fullKey,
                    blockInfo: blockInfo
                });
            }
        }
    }
    
    processStatisticsRecursive(statistics);
    return groupedStats;
}

function groupStatisticsByAgent(statistics, agentMapping) {
    const groupedStats = {};
    
    // Recursively process statistics and group by agent
    function processStatisticsRecursive(obj, prefix = '') {
        for (const [key, value] of Object.entries(obj)) {
            const fullKey = prefix ? `${prefix}.${key}` : key;
            
            if (getValueType(value) === 'object' && value !== null) {
                // Continue recursion for nested objects
                processStatisticsRecursive(value, fullKey);
            } else {
                // This is a leaf node (actual statistic value)
                const agentId = extractAgentId(fullKey);
                const agentName = agentMapping[agentId] || `Unknown Agent (${agentId})`;
                const propertyName = extractPropertyName(fullKey);
                
                if (!groupedStats[agentName]) {
                    groupedStats[agentName] = [];
                }
                
                groupedStats[agentName].push({
                    property: propertyName,
                    value: value,
                    fullKey: fullKey
                });
            }
        }
    }
    
    processStatisticsRecursive(statistics);
    return groupedStats;
}

function isRootLevelProperty(key, agentId) {
    // Determine if a property is a root-level property for an agent
    // Root properties typically have the pattern: agentId.property.statistic
    // Block properties typically have the pattern: agentId.blockId.property.statistic
    
    const parts = key.split('.');
    
    // If we only have 2 parts after the agent ID, it's likely a root property
    // agentId.property.statistic
    if (parts.length === 2) {
        return true;
    }
    
    // If we have 3+ parts, check if the second part looks like a block ID
    if (parts.length >= 3) {
        const secondPart = parts[1];
        // If the second part is short or doesn't look like a block ID, it might be a root property
        if (secondPart.length < 10 || !secondPart.match(/^[A-Za-z0-9]{20,}$/)) {
            return true;
        }
    }
    
    return false;
}

function extractBlockId(key) {
    // Extract block ID from statistics key
    // Examples:
    // "PRkHzzmM9MMY9JPfBDd7LC/2.PS5ZhpB776TSq4JND74VJm.powerConsumed.absAvg" -> "PS5ZhpB776TSq4JND74VJm"
    // "PRknkFRHNYJhkCV8b53CLG/0.position.llaDeg.2.absAvg" -> "PRknkFRHNYJhkCV8b53CLG"
    
    const parts = key.split('.');
    if (parts.length >= 2) {
        // Look for block ID in the second part (after agent ID)
        const secondPart = parts[1];
        if (secondPart && secondPart.length > 10) {
            // This looks like a block ID
            return secondPart;
        }
    }
    
    // Fallback: use the first part as block ID
    if (parts.length > 0) {
        const firstPart = parts[0];
        const agentId = firstPart.split('/')[0];
        return agentId;
    }
    
    return 'unknown';
}

function extractAgentId(key) {
    // Extract agent ID from statistics key
    // Examples:
    // "PRkHzzmM9MMY9JPfBDd7LC/2.PS5ZhpB776TSq4JND74VJm.powerConsumed.absAvg" -> "PRkHzzmM9MMY9JPfBDd7LC"
    // "PRknkFRHNYJhkCV8b53CLG/0.position.llaDeg.2.absAvg" -> "PRknkFRHNYJhkCV8b53CLG"
    
    const parts = key.split('.');
    if (parts.length > 0) {
        // The agent ID is typically the first part before any additional identifiers
        const firstPart = parts[0];
        // Remove any trailing numbers or additional identifiers
        const agentId = firstPart.split('/')[0];
        return agentId;
    }
    return 'unknown';
}

function extractPropertyName(key) {
    // Extract a readable property name from the statistics key
    // Examples:
    // "PRkHzzmM9MMY9JPfBDd7LC/2.PS5ZhpB776TSq4JND74VJm.powerConsumed.absAvg" -> "Power Consumed - Absolute Average"
    // "PRknkFRHNYJhkCV8b53CLG/0.position.llaDeg.2.absAvg" -> "Position LLA (Altitude) - Absolute Average"
    // "PRkHzzmM9MMY9JPfBDd7LC.orbitNumber.absAvg" -> "Orbit Number - Absolute Average"
    
    const parts = key.split('.');
    
    // Handle root properties (agentId.property.statistic)
    if (parts.length === 2) {
        const propertyPart = parts[0];
        const statType = parts[1];
        const statTypeName = getStatisticTypeName(statType);
        
        let propertyName = '';
        if (propertyPart.includes('orbitNumber')) {
            propertyName = 'Orbit Number';
        } else if (propertyPart.includes('mass')) {
            propertyName = 'Mass';
        } else if (propertyPart.includes('position')) {
            propertyName = 'Position';
        } else if (propertyPart.includes('velocity')) {
            propertyName = 'Velocity';
        } else {
            // Use the property part as is
            propertyName = propertyPart.charAt(0).toUpperCase() + propertyPart.slice(1);
        }
        
        return `${propertyName} - ${statTypeName}`;
    }
    
    // Handle block properties (agentId.blockId.property.statistic)
    if (parts.length >= 3) {
        // Skip the agent ID and block ID, get the meaningful parts
        const meaningfulParts = parts.slice(2);
        
        // Convert to readable format
        let propertyName = '';
        
        // Handle special cases
        if (meaningfulParts.includes('powerConsumed')) {
            propertyName = 'Power Consumed';
        } else if (meaningfulParts.includes('position')) {
            propertyName = 'Position';
            if (meaningfulParts.includes('llaDeg')) {
                propertyName += ' (LLA)';
            }
        } else if (meaningfulParts.includes('velocity')) {
            propertyName = 'Velocity';
        } else if (meaningfulParts.includes('attitude')) {
            propertyName = 'Attitude';
        } else if (meaningfulParts.includes('rainData')) {
            propertyName = 'Rain Data';
        } else if (meaningfulParts.includes('speed')) {
            propertyName = 'Speed';
        } else if (meaningfulParts.includes('soc')) {
            propertyName = 'State of Charge';
        } else if (meaningfulParts.includes('voltage')) {
            propertyName = 'Voltage';
        } else if (meaningfulParts.includes('current')) {
            propertyName = 'Current';
        } else if (meaningfulParts.includes('temperature')) {
            propertyName = 'Temperature';
        } else {
            // Use the first meaningful part
            propertyName = meaningfulParts[0].charAt(0).toUpperCase() + meaningfulParts[0].slice(1);
        }
        
        // Add the statistic type
        const statType = meaningfulParts[meaningfulParts.length - 1];
        const statTypeName = getStatisticTypeName(statType);
        
        return `${propertyName} - ${statTypeName}`;
    }
    
    return key;
}

function getStatisticTypeName(statType) {
    const typeMap = {
        'absAvg': 'Absolute Average',
        'average': 'Average',
        'integral': 'Integral',
        'max': 'Maximum',
        'min': 'Minimum',
        'negativeMax': 'Negative Maximum',
        'positiveMax': 'Positive Maximum',
        'stdDev': 'Standard Deviation',
        'variance': 'Variance'
    };
    
    return typeMap[statType] || statType;
}

function displayStatisticsFallback(statistics, simulationId) {
    // Fallback to original display method
    const resultsDiv = document.getElementById('statisticsResults');
    
    let html = `
        <div class="statistics-success">
            <h4>✅ Statistics Retrieved Successfully</h4>
            <p><strong>Simulation ID:</strong> ${simulationId || 'Latest'}</p>
            <p><strong>Total Statistics:</strong> ${Object.keys(statistics).length}</p>
        </div>
        <table class="statistics-table">
            <thead>
                <tr>
                    <th>Stream/Property</th>
                    <th>Value</th>
                    <th>Type</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    // Recursively process statistics object
    function processStatistics(obj, prefix = '') {
        for (const [key, value] of Object.entries(obj)) {
            const fullKey = prefix ? `${prefix}.${key}` : key;
            const valueType = getValueType(value);
            const formattedValue = formatValue(value);
            
            html += `
                <tr>
                    <td><strong>${fullKey}</strong></td>
                    <td class="statistic-value ${valueType}">${formattedValue}</td>
                    <td><span class="badge badge-${valueType}">${valueType}</span></td>
                </tr>
            `;
            
            // Recursively process nested objects
            if (valueType === 'object' && value !== null) {
                processStatistics(value, fullKey);
            }
        }
    }
    
    processStatistics(statistics);
    
    html += `
            </tbody>
        </table>
    `;
    
    resultsDiv.innerHTML = html;
}

function getValueType(value) {
    if (value === null) return 'null';
    if (Array.isArray(value)) return 'array';
    if (typeof value === 'object') return 'object';
    if (typeof value === 'number') return 'number';
    if (typeof value === 'boolean') return 'boolean';
    if (typeof value === 'string') return 'string';
    return 'unknown';
}

function formatValue(value) {
    if (value === null) return 'null';
    if (Array.isArray(value)) {
        if (value.length <= 10) {
            return `[${value.map(v => formatValue(v)).join(', ')}]`;
        } else {
            return `[${value.slice(0, 10).map(v => formatValue(v)).join(', ')}... (${value.length} items)]`;
        }
    }
    if (typeof value === 'object') {
        const keys = Object.keys(value);
        if (keys.length <= 5) {
            return `{${keys.map(k => `${k}: ${formatValue(value[k])}`).join(', ')}}`;
        } else {
            return `{${keys.slice(0, 5).map(k => `${k}: ${formatValue(value[k])}`).join(', ')}... (${keys.length} keys)}`;
        }
    }
    if (typeof value === 'number') {
        return value.toFixed(6);
    }
    if (typeof value === 'boolean') {
        return value ? 'true' : 'false';
    }
    if (typeof value === 'string') {
        return value.length > 100 ? value.substring(0, 100) + '...' : value;
    }
    return String(value);
}

function clearStatistics() {
    document.getElementById('statisticsResults').innerHTML = `
        <div class="no-statistics">
            <p>Click "Fetch Statistics" to get simulation statistics</p>
            <p>Statistics will show summary data like min, max, mean, and standard deviation for simulation variables</p>
        </div>
    `;
    document.getElementById('statsSimulationId').value = '';
    showToast('Statistics cleared', 'info');
}

function toggleSection(sectionId) {
    const content = document.getElementById(`content-${sectionId}`);
    const toggleIcon = document.getElementById(`toggle-${sectionId}`);
    
    if (content && toggleIcon) {
        if (content.style.display === 'none') {
            content.style.display = 'block';
            toggleIcon.textContent = '▼';
        } else {
            content.style.display = 'none';
            toggleIcon.textContent = '▶';
        }
    }
}

async function createBlockIdToNameMapping() {
    try {
        console.log('Creating block ID to name mapping...');
        
        // Get the template structure
        const response = await fetch('/api/template_structure');
        const result = await response.json();
        
        if (result.success) {
            blockIdToNameMapping = extractBlockIdToNameMapping(result.data);
            console.log('Block ID to name mapping created:', blockIdToNameMapping);
            return blockIdToNameMapping;
        } else {
            console.error('Failed to get template structure for mapping:', result.error);
            return {};
        }
    } catch (error) {
        console.error('Error creating block ID to name mapping:', error);
        return {};
    }
}

function extractBlockIdToNameMapping(data, prefix = '') {
    let mapping = {};
    
    if (typeof data === 'object' && data !== null) {
        if (Array.isArray(data)) {
            data.forEach((item, index) => {
                const path = prefix ? `${prefix}.${index}` : `${index}`;
                if (typeof item === 'object' && item !== null) {
                    if (item.id && item.type) {
                        // This is a block/component
                        const blockName = item.name || `${item.type}_${item.id}`;
                        mapping[item.id] = {
                            name: blockName,
                            type: item.type,
                            path: path,
                            displayName: `${blockName} (${item.type})`,
                            fullPath: path
                        };
                    }
                    // Recursively extract from nested objects
                    const nestedMapping = extractBlockIdToNameMapping(item, path);
                    Object.assign(mapping, nestedMapping);
                }
            });
        } else {
            Object.keys(data).forEach(key => {
                const path = prefix ? `${prefix}.${key}` : key;
                const value = data[key];
                
                if (typeof value === 'object' && value !== null) {
                    if (value.id && value.type) {
                        // This is a block/component
                        const blockName = value.name || `${value.type}_${value.id}`;
                        mapping[value.id] = {
                            name: blockName,
                            type: value.type,
                            path: path,
                            displayName: `${blockName} (${value.type})`,
                            fullPath: path
                        };
                    }
                    // Recursively extract from nested objects
                    const nestedMapping = extractBlockIdToNameMapping(value, path);
                    Object.assign(mapping, nestedMapping);
                }
            });
        }
    }
    
    return mapping;
}

// Function to get block name by ID with fallback
function getBlockNameById(blockId) {
    if (blockIdToNameMapping[blockId]) {
        return blockIdToNameMapping[blockId];
    }
    return {
        name: `Unknown_${blockId}`,
        type: 'Unknown',
        path: '',
        displayName: `Unknown Block (${blockId})`,
        fullPath: ''
    };
}

// Function to group properties by block
function groupPropertiesByBlock(properties) {
    const grouped = {};
    
    properties.forEach(prop => {
        if (prop.blockId) {
            const blockInfo = getBlockNameById(prop.blockId);
            const blockKey = blockInfo.name;
            
            if (!grouped[blockKey]) {
                grouped[blockKey] = {
                    blockInfo: blockInfo,
                    properties: []
                };
            }
            
            grouped[blockKey].properties.push(prop);
        } else {
            // Root properties - add them without a special label
            if (!grouped['root']) {
                grouped['root'] = {
                    blockInfo: {
                        name: 'root',
                        type: 'root',
                        displayName: 'Template Properties'
                    },
                    properties: []
                };
            }
            grouped['root'].properties.push(prop);
        }
    });
    
    return grouped;
}

// Debug function to test block mapping (can be called from browser console)
function debugBlockMapping() {
    console.log('=== Block ID to Name Mapping Debug ===');
    console.log('Mapping object:', blockIdToNameMapping);
    console.log('Total blocks mapped:', Object.keys(blockIdToNameMapping).length);
    
    // Show some examples
    const blockIds = Object.keys(blockIdToNameMapping);
    if (blockIds.length > 0) {
        console.log('Example mappings:');
        blockIds.slice(0, 5).forEach(id => {
            const info = blockIdToNameMapping[id];
            console.log(`  ${id} -> ${info.displayName} (${info.type})`);
        });
    }
    
    // Test the grouping function
    if (allTemplateProperties.length > 0) {
        console.log('Testing property grouping...');
        const grouped = groupPropertiesByBlock(allTemplateProperties);
        console.log('Grouped properties:', grouped);
        
        Object.keys(grouped).forEach(groupKey => {
            const group = grouped[groupKey];
            console.log(`  ${groupKey}: ${group.properties.length} properties`);
        });
    }
    
    console.log('=== End Debug ===');
}

// Function to get a summary of all blocks
function getBlockSummary() {
    if (!blockIdToNameMapping || Object.keys(blockIdToNameMapping).length === 0) {
        console.log('No block mapping available. Run createBlockIdToNameMapping() first.');
        return;
    }
    
    const summary = {};
    Object.values(blockIdToNameMapping).forEach(blockInfo => {
        if (!summary[blockInfo.type]) {
            summary[blockInfo.type] = [];
        }
        summary[blockInfo.type].push({
            id: Object.keys(blockIdToNameMapping).find(id => blockIdToNameMapping[id] === blockInfo),
            name: blockInfo.name,
            displayName: blockInfo.displayName
        });
    });
    
    console.log('=== Block Summary by Type ===');
    Object.keys(summary).forEach(type => {
        console.log(`${type} (${summary[type].length} blocks):`);
        summary[type].forEach(block => {
            console.log(`  - ${block.displayName} (ID: ${block.id})`);
        });
    });
    console.log('=== End Summary ===');
    
    return summary;
}

// Debug function to test statistics grouping
function debugStatisticsGrouping(statistics) {
    console.log('=== Statistics Grouping Debug ===');
    
    if (!statistics) {
        console.log('No statistics provided');
        return;
    }
    
    // Test agent mapping
    getAgentMapping().then(agentMapping => {
        console.log('Agent mapping:', agentMapping);
        
        // Test the new grouping function
        const grouped = groupStatisticsByAgentAndBlock(statistics, agentMapping);
        console.log('Grouped statistics by agent and block:', grouped);
        
        Object.keys(grouped).forEach(agentName => {
            const agentData = grouped[agentName];
            console.log(`\nAgent: ${agentName}`);
            console.log(`  Root properties: ${agentData.rootProperties.length}`);
            console.log(`  Blocks: ${Object.keys(agentData.blocks).length}`);
            
            Object.keys(agentData.blocks).forEach(blockName => {
                console.log(`    ${blockName}: ${agentData.blocks[blockName].length} properties`);
            });
        });
    }).catch(error => {
        console.error('Error testing statistics grouping:', error);
    });
    
    console.log('=== End Statistics Debug ===');
}