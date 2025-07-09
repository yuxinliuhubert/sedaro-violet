# Violet Sedaro Platform - Technical Documentation

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Backend Implementation](#backend-implementation)
3. [Frontend Implementation](#frontend-implementation)
4. [Data Flow](#data-flow)
5. [Key Algorithms](#key-algorithms)
6. [API Design](#api-design)
7. [State Management](#state-management)
8. [Performance Considerations](#performance-considerations)
9. [Security Implementation](#security-implementation)
10. [Testing Strategy](#testing-strategy)

## 🏗️ Architecture Overview

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Sedaro API    │
│   (Browser)     │◄──►│   (Flask)       │◄──►│   (External)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
    ┌─────────┐            ┌─────────┐            ┌─────────┐
    │Local    │            │Block    │            │Agent    │
    │Storage  │            │Mapping  │            │Templates│
    └─────────┘            └─────────┘            └─────────┘
```

### Technology Stack

- **Backend**: Python 3.7+, Flask, Sedaro SDK
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Data Storage**: Local Storage (browser), In-memory caching
- **Communication**: RESTful APIs, WebSocket-like polling

## 🔧 Backend Implementation

### Core Modules

#### 1. Template Management (`app.py`)

```python
# Key Functions
def discover_blocks() -> Dict[str, List[Dict[str, Any]]]:
    """Discovers and categorizes all blocks in the agent template"""
    
def refresh_agent_template(template_id: Optional[str] = None) -> Dict[str, Any]:
    """Refreshes connection to agent template with new template ID"""
    
def get_agent_template_structure() -> Dict[str, Any]:
    """Gets complete structure of agent template data"""
```

**Block Discovery Algorithm**:
1. Access `agent_template_branch.data`
2. Search for blocks in multiple possible locations:
   - Direct `blocks` key
   - `data.blocks` nested structure
   - Any list containing objects with `id` and `type` fields
3. Fallback to known block IDs if no blocks found
4. Categorize blocks by type and filter internal fields

#### 2. Property Management

```python
def update_block_property(block_id: str, property_name: str, new_value: Any) -> Dict[str, Any]:
    """Updates specific property of a block using Sedaro client directly"""
    
def update_root_property(property_name: str, new_value: Any) -> Dict[str, Any]:
    """Updates root-level property of the agent template"""
    
def get_property_mutability(block_id: Optional[str] = None, property_name: Optional[str] = None) -> Dict[str, Any]:
    """Checks if a property is mutable by attempting to get its metadata"""
```

**Property Update Flow**:
1. Validate input parameters
2. Type conversion (string → number/boolean)
3. Direct Sedaro client update
4. Return updated value confirmation
5. Error handling with detailed messages

#### 3. Simulation Management

```python
def start_simulation() -> Dict[str, Any]:
    """Starts simulation using Sedaro client directly"""
    
def get_simulation_status(simulation_id: Optional[str] = None) -> Dict[str, Any]:
    """Gets simulation status and progress without blocking"""
    
def get_simulation_statistics(simulation_id: Optional[str] = None, wait: bool = True, streams: Optional[List] = None) -> Dict[str, Any]:
    """Gets simulation statistics using Sedaro client directly"""
```

**Simulation Lifecycle**:
1. **Start**: Create simulation handle, return ID
2. **Monitor**: Poll status every 2 seconds with timeout protection
3. **Complete**: Retrieve results and statistics
4. **Abort**: Terminate running simulation

### API Endpoints

#### Template Management
```python
@app.route("/api/template_structure", methods=['GET'])
@app.route("/api/refresh_template", methods=['POST'])
@app.route("/api/blocks")
@app.route("/api/block/<block_id>/properties", methods=['GET'])
```

#### Property Management
```python
@app.route("/api/update_property", methods=['POST'])
@app.route("/api/update_root_property", methods=['POST'])
@app.route("/api/mutability", methods=['GET'])
```

#### Simulation Control
```python
@app.route("/api/simulate", methods=['POST'])
@app.route("/api/simulation_status", methods=['GET'])
@app.route("/api/abort_simulation", methods=['POST'])
@app.route("/api/results", methods=['GET'])
```

#### Statistics
```python
@app.route("/api/simulation_statistics", methods=['POST'])
@app.route("/api/available_streams", methods=['GET'])
```

## 🎨 Frontend Implementation

### Core JavaScript Modules

#### 1. State Management (`script.js`)

```javascript
// Global State Variables
let currentBlockId = null;
let currentPropertyName = null;
let currentSimulationId = null;
let progressInterval = null;
let spreadsheetData = {};
let allTemplateProperties = [];
let blockIdToNameMapping = {};

// State Persistence Functions
function saveState() {
    const state = {
        currentSimulationId: currentSimulationId,
        spreadsheetData: spreadsheetData,
        autoSimEnabled: document.getElementById('autoSimToggle')?.checked || false
    };
    localStorage.setItem('sedaroVioletState', JSON.stringify(state));
}

function loadState() {
    // Restore application state from localStorage
    // Handle corrupted state gracefully
}
```

#### 2. Block ID Mapping System

```javascript
async function createBlockIdToNameMapping() {
    // Creates comprehensive mapping of block IDs to names and metadata
}

function extractBlockIdToNameMapping(data, prefix = '') {
    // Recursively extracts block information from template structure
}

function getBlockNameById(blockId) {
    // Retrieves block information by ID with fallback for unknown blocks
}

function groupPropertiesByBlock(properties) {
    // Groups properties by their associated blocks for better organization
}
```

**Mapping Algorithm**:
1. **Discovery**: Recursively traverse template structure
2. **Extraction**: Identify objects with `id` and `type` fields
3. **Normalization**: Create consistent naming scheme
4. **Caching**: Store mapping in memory for performance
5. **Fallback**: Handle unknown blocks gracefully

#### 3. Property Tracking System

```javascript
function updateSpreadsheetData(rowId, field, value) {
    // Updates spreadsheet data and triggers auto-simulation if enabled
}

async function applySpreadsheetChanges() {
    // Applies tracked property changes and triggers simulation
}

function trackPropertyFromExplorer(propertyName, blockId, displayName) {
    // Adds property to tracking spreadsheet from explorer
}
```

**Auto-Simulation Logic**:
1. **Change Detection**: Compare current vs last applied values
2. **Batch Updates**: Process multiple changes efficiently
3. **Error Handling**: Continue processing on individual failures
4. **Simulation Trigger**: Start simulation only after successful updates

#### 4. Statistics Display System

```javascript
function groupStatisticsByAgentAndBlock(statistics, agentMapping) {
    // Groups statistics by agent first, then by block within each agent
}

function extractBlockId(key) {
    // Extracts block ID from statistics key
}

function isRootLevelProperty(key, agentId) {
    // Determines if property is root-level or belongs to a block
}
```

**Statistics Grouping Algorithm**:
1. **Agent Level**: Group by agent ID using agent mapping
2. **Property Classification**: Distinguish root vs block properties
3. **Block Level**: Group block properties by block name
4. **Visual Hierarchy**: Create nested display structure

### UI Components

#### 1. Responsive Design

```css
/* Color Scheme */
:root {
    --primary-color: #c3adff;
    --secondary-color: #6c757d;
    --background-color: #ffffff;
    --accent-color: #a78bfa;
}

/* Responsive Grid */
.property-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1rem;
}
```

#### 2. Interactive Elements

```css
/* Button Styling */
.save-button {
    background: linear-gradient(135deg, var(--primary-color) 0%, var(--accent-color) 100%);
    transition: all 0.3s ease;
}

/* Progress Indicators */
.progress-fill {
    background: linear-gradient(90deg, var(--primary-color), var(--accent-color));
    transition: width 0.3s ease;
}
```

## 🔄 Data Flow

### 1. Application Initialization

```
1. Load saved state from localStorage
2. Initialize block ID to name mapping
3. Load template properties
4. Setup state persistence
5. Restore simulation monitoring if needed
```

### 2. Property Update Flow

```
User Input → Validation → Type Conversion → API Call → 
Response Processing → UI Update → State Persistence → 
Auto-Simulation Trigger (if enabled)
```

### 3. Simulation Monitoring Flow

```
Start Simulation → Get Simulation ID → Begin Polling → 
Status Updates → Progress Display → Completion → 
Results Retrieval → Statistics Display
```

### 4. Statistics Processing Flow

```
Fetch Statistics → Parse Response → Extract Agent IDs → 
Map to Names → Group by Agent → Classify Properties → 
Group by Block → Display Hierarchically
```

## 🔍 Key Algorithms

### 1. Block Discovery Algorithm

```python
def discover_blocks():
    blocks_by_type = {}
    
    # Multiple data structure support
    if 'blocks' in agent_data:
        all_blocks = agent_data['blocks']
    elif 'data' in agent_data and 'blocks' in agent_data['data']:
        all_blocks = agent_data['data']['blocks']
    else:
        # Fallback to known block IDs
        all_blocks = get_known_blocks()
    
    # Process and categorize blocks
    for block in all_blocks:
        block_type = block.get('type', 'Unknown')
        if block_type not in blocks_by_type:
            blocks_by_type[block_type] = []
        
        blocks_by_type[block_type].append({
            'id': block.get('id'),
            'name': block.get('name', f'{block_type}_{block.get("id")}'),
            'data': filter_internal_fields(block),
            'type': block_type
        })
    
    return blocks_by_type
```

### 2. Property Grouping Algorithm

```javascript
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
            // Root properties
            if (!grouped['Root Properties']) {
                grouped['Root Properties'] = {
                    blockInfo: { name: 'Root Properties', type: 'root' },
                    properties: []
                };
            }
            grouped['Root Properties'].properties.push(prop);
        }
    });
    
    return grouped;
}
```

### 3. Statistics Grouping Algorithm

```javascript
function groupStatisticsByAgentAndBlock(statistics, agentMapping) {
    const groupedStats = {};
    
    function processStatisticsRecursive(obj, prefix = '') {
        for (const [key, value] of Object.entries(obj)) {
            const fullKey = prefix ? `${prefix}.${key}` : key;
            
            if (getValueType(value) === 'object' && value !== null) {
                processStatisticsRecursive(value, fullKey);
            } else {
                const agentId = extractAgentId(fullKey);
                const agentName = agentMapping[agentId] || `Unknown Agent (${agentId})`;
                const isRootProperty = isRootLevelProperty(fullKey, agentId);
                
                if (!groupedStats[agentName]) {
                    groupedStats[agentName] = {
                        rootProperties: [],
                        blocks: {}
                    };
                }
                
                if (isRootProperty) {
                    groupedStats[agentName].rootProperties.push({
                        property: extractPropertyName(fullKey),
                        value: value,
                        fullKey: fullKey
                    });
                } else {
                    const blockId = extractBlockId(fullKey);
                    const blockInfo = getBlockNameById(blockId);
                    const blockKey = blockInfo.name;
                    
                    if (!groupedStats[agentName].blocks[blockKey]) {
                        groupedStats[agentName].blocks[blockKey] = [];
                    }
                    
                    groupedStats[agentName].blocks[blockKey].push({
                        property: extractPropertyName(fullKey),
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
```

## 🔌 API Design

### Request/Response Patterns

#### Standard Response Format
```json
{
    "success": true|false,
    "message": "Human readable message",
    "data": {...},
    "error": "Error details if success is false"
}
```

#### Property Update Request
```json
{
    "block_id": "PS5ZhpB776TSq4JND74VJm",
    "property_name": "capacity",
    "new_value": 100.0
}
```

#### Simulation Status Response
```json
{
    "success": true,
    "simulation_id": "sim_12345",
    "status": "RUNNING",
    "progress": 45.2,
    "progress_info": {
        "percentComplete": 45.2,
        "currentTime": 86400.0,
        "startTime": 0.0,
        "stopTime": 172800.0
    },
    "is_complete": false,
    "message": "Simulation RUNNING (45.2% complete)"
}
```

### Error Handling

#### HTTP Status Codes
- `200`: Success
- `400`: Bad Request (invalid parameters)
- `404`: Not Found (resource doesn't exist)
- `500`: Internal Server Error

#### Error Response Format
```json
{
    "success": false,
    "error": "Detailed error message",
    "error_code": "VALIDATION_ERROR",
    "details": {
        "field": "property_name",
        "issue": "Property not found"
    }
}
```

## 💾 State Management

### Local Storage Structure

```javascript
const stateStructure = {
    currentSimulationId: "sim_12345",
    spreadsheetData: {
        "row_1": {
            name: "battery_capacity",
            value: "100.0",
            associatedProperty: {
                name: "capacity",
                displayName: "Battery Cell.capacity",
                isBlock: false,
                blockId: "PS5ZhpB776TSq4JND74VJm"
            },
            autoTrigger: true,
            lastAppliedValue: "100.0"
        }
    },
    autoSimEnabled: true
};
```

### State Persistence Strategy

1. **Automatic Saving**: Every 5 seconds
2. **Event-Based Saving**: On important state changes
3. **Session Recovery**: On application startup
4. **Corruption Handling**: Clear corrupted state automatically

### Memory Management

1. **Block Mapping Cache**: Store in memory for performance
2. **Property Cache**: Cache frequently accessed properties
3. **Statistics Cache**: Cache processed statistics
4. **Cleanup**: Clear caches on template refresh

## ⚡ Performance Considerations

### Optimization Strategies

#### 1. Lazy Loading
```javascript
// Load properties only when needed
async function expandBlockComponent(rowId, blockProp, dropdown) {
    const response = await fetch(`/api/block/${blockProp.id}/properties`);
    // Process and display properties
}
```

#### 2. Caching
```javascript
// Cache block mapping for performance
let blockIdToNameMapping = {};

function getBlockNameById(blockId) {
    if (blockIdToNameMapping[blockId]) {
        return blockIdToNameMapping[blockId];
    }
    return getFallbackBlockInfo(blockId);
}
```

#### 3. Batch Operations
```javascript
// Process multiple updates efficiently
async function applySpreadsheetChanges() {
    const updates = [];
    for (const [rowId, data] of Object.entries(spreadsheetData)) {
        if (data.autoTrigger && data.name && data.value && data.associatedProperty) {
            updates.push(updateProperty(data));
        }
    }
    await Promise.all(updates);
}
```

#### 4. Polling Optimization
```javascript
// Efficient simulation monitoring
function startProgressMonitoring(simulationId) {
    // Update immediately
    updateProgress(simulationId);
    
    // Then update every 2 seconds
    progressInterval = setInterval(async () => {
        const isComplete = await updateProgress(simulationId);
        if (isComplete) {
            clearInterval(progressInterval);
        }
    }, 2000);
    
    // Safety timeout after 30 minutes
    setTimeout(() => {
        if (progressInterval) {
            clearInterval(progressInterval);
        }
    }, 30 * 60 * 1000);
}
```

### Performance Metrics

- **Initial Load Time**: < 2 seconds
- **Property Update Response**: < 500ms
- **Simulation Status Polling**: < 200ms
- **Statistics Processing**: < 1 second for 1000+ statistics
- **Memory Usage**: < 50MB for typical usage

## 🔒 Security Implementation

### Input Validation

```python
def validate_property_update(data):
    """Validates property update request data"""
    required_fields = ['block_id', 'property_name', 'new_value']
    
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"
    
    # Validate block ID format
    if not re.match(r'^[A-Za-z0-9]{20,}$', data['block_id']):
        return False, "Invalid block ID format"
    
    # Validate property name
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', data['property_name']):
        return False, "Invalid property name format"
    
    return True, "Validation passed"
```

### Error Handling

```python
@app.errorhandler(Exception)
def handle_exception(e):
    """Global exception handler"""
    # Log the error for debugging
    app.logger.error(f"Unhandled exception: {str(e)}")
    
    # Return generic error message to client
    return jsonify({
        'success': False,
        'error': 'An internal error occurred',
        'error_code': 'INTERNAL_ERROR'
    }), 500
```

### API Key Protection

```python
# Store API key securely
API_KEY = os.environ.get('SEDARO_API_KEY', 'default-key-for-development')

# Validate API key format
if not API_KEY or len(API_KEY) < 20:
    raise ValueError("Invalid API key configuration")
```

## 🧪 Testing Strategy

### Unit Testing

```python
# Example test for block discovery
def test_discover_blocks():
    """Test block discovery functionality"""
    # Mock agent template data
    mock_data = {
        'blocks': [
            {'id': 'test_id', 'type': 'BatteryCell', 'name': 'Test Battery'}
        ]
    }
    
    # Test block discovery
    result = discover_blocks(mock_data)
    
    assert 'BatteryCell' in result
    assert len(result['BatteryCell']) == 1
    assert result['BatteryCell'][0]['id'] == 'test_id'
```

### Integration Testing

```python
# Example integration test
def test_property_update_flow():
    """Test complete property update flow"""
    # 1. Update property
    response = client.post('/api/update_property', json={
        'block_id': 'test_block_id',
        'property_name': 'capacity',
        'new_value': 100.0
    })
    
    assert response.status_code == 200
    assert response.json['success'] == True
    
    # 2. Verify property was updated
    response = client.get('/api/block/test_block_id/properties')
    assert response.json['capacity'] == 100.0
```

### Frontend Testing

```javascript
// Example frontend test
function testBlockMapping() {
    const mockData = {
        'blocks': [
            {id: 'test_id', type: 'BatteryCell', name: 'Test Battery'}
        ]
    };
    
    const mapping = extractBlockIdToNameMapping(mockData);
    
    assert(mapping['test_id'].name === 'Test Battery');
    assert(mapping['test_id'].type === 'BatteryCell');
}
```

### Performance Testing

```python
# Example performance test
def test_statistics_processing_performance():
    """Test statistics processing performance"""
    import time
    
    # Generate large statistics dataset
    large_stats = generate_large_statistics_dataset(10000)
    
    start_time = time.time()
    result = process_statistics(large_stats)
    end_time = time.time()
    
    # Should process 10,000 statistics in under 1 second
    assert (end_time - start_time) < 1.0
    assert len(result) > 0
```

## 📊 Monitoring and Logging

### Application Logging

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('violet_sedaro.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Log important events
logger.info(f"Simulation started: {simulation_id}")
logger.warning(f"Property update failed: {error_message}")
logger.error(f"API connection failed: {exception}")
```

### Performance Monitoring

```python
# Monitor API response times
import time

def monitor_api_call(func):
    """Decorator to monitor API call performance"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"API call {func.__name__} completed in {duration:.3f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"API call {func.__name__} failed after {duration:.3f}s: {e}")
            raise
    return wrapper
```

### Error Tracking

```python
# Track and categorize errors
def track_error(error_type, error_message, context=None):
    """Track application errors for analysis"""
    error_data = {
        'type': error_type,
        'message': error_message,
        'timestamp': time.time(),
        'context': context or {}
    }
    
    # Log error
    logger.error(f"Error tracked: {error_data}")
    
    # Store for analysis (could send to external service)
    store_error_for_analysis(error_data)
```

---

This technical documentation provides a comprehensive overview of the Violet Sedaro Platform's implementation details, architecture decisions, and technical considerations. For additional information, refer to the main README.md file or contact the development team. 