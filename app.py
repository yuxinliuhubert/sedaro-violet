from flask import Flask, jsonify, request, render_template_string
from sedaro import SedaroApiClient
from pprint import pprint
import json
from typing import Dict, List, Any, Optional

API_KEY = "PKDqMrtcTK4plJgL7qVlQD.0xQph1lyKzd-pV0-ZL7bRIH7BX54Yjqbz6tluwut3Hvp8XE-RVbfHSz2o5vC77scUhg2xBFuBybplxY6FyXXMQ"
TEMP_AGENT_REPO_BRANCH_ID = "PS5ZPCp6mh5yXLH3lkCWFj" # Specific Repo of the Templated agent 
SCENARIO_BRANCH_VERSION_ID = "PRx5rSwrGfkK4n9vFXmVbt" # Version 2
WORKSPACE_ID = "PQtnGZNNPdzZM5JdVhP5P9" # Violet/Ethreal workspace

# Define modules
sedaro = SedaroApiClient(api_key = API_KEY)
# agent template is only for satellite model (agent), and don't copy the model repo ID, only the branch ID (version)
agent_template_branch = sedaro.agent_template(TEMP_AGENT_REPO_BRANCH_ID) # we are going to change this templated agent

def refresh_agent_template(template_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Refresh the agent template connection with a new template ID
    """
    global agent_template_branch
    
    try:
        # Use provided ID or fall back to the constant
        template_id = template_id or TEMP_AGENT_REPO_BRANCH_ID
        
        # Create new agent template connection
        agent_template_branch = sedaro.agent_template(template_id)
        
        # Test the connection by trying to access data
        test_data = agent_template_branch.data
        print(f"Successfully connected to agent template: {template_id}")
        
        return {
            'success': True,
            'message': f'Successfully switched to agent template: {template_id}',
            'template_id': template_id,
            'data_keys': list(test_data.keys()) if isinstance(test_data, dict) else []
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Failed to connect to agent template {template_id}: {str(e)}'
        }

app = Flask(__name__, static_folder='Static', static_url_path='')

def discover_blocks() -> Dict[str, List[Dict[str, Any]]]:
    """
    Discover all blocks in the agent template and categorize them by type
    """
    blocks_by_type = {}
    
    try:
        # Get all blocks from the agent template data
        agent_data = agent_template_branch.data
        print("Agent data keys:", list(agent_data.keys()))
        
        # The blocks might be in different locations depending on the data structure
        all_blocks = []
        if 'blocks' in agent_data:
            all_blocks = agent_data['blocks']
            print(f"Found {len(all_blocks)} blocks in 'blocks' key")
        elif 'data' in agent_data and 'blocks' in agent_data['data']:
            all_blocks = agent_data['data']['blocks']
            print(f"Found {len(all_blocks)} blocks in 'data.blocks' key")
        else:
            # If no blocks found, try to find any block-like structures
            for key, value in agent_data.items():
                if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                    if 'id' in value[0] and 'type' in value[0]:
                        all_blocks = value
                        print(f"Found {len(all_blocks)} blocks in '{key}' key")
                        break
        
        print(f"Total blocks found: {len(all_blocks)}")
        
        # Process blocks from data structure if found
        for block in all_blocks:
            if not isinstance(block, dict):
                continue
                
            block_type = block.get('type', 'Unknown')
            if block_type not in blocks_by_type:
                blocks_by_type[block_type] = []
            
            # Get block data and filter out internal fields
            block_data = block
            filtered_data = {k: v for k, v in block_data.items() if not k.startswith('_')}
            
            blocks_by_type[block_type].append({
                'id': block.get('id', 'unknown'),
                'name': block_data.get('name', f'{block_type}_{block.get("id", "unknown")}'),
                'data': filtered_data,
                'type': block_type
            })
        
        # If we still don't have blocks, try to get them by known IDs
        if not blocks_by_type:
            print("No blocks found in data structure, trying known block IDs...")
            known_block_ids = [
                'PK3PCpCJRn6LpwvhWzNtsb',  # battery_cell_id from notebook
                'PRx5qGqQD59tCW4V9tBGQb',  # battery_pack_id from notebook
                'PRx7YwymYJgtlTDBjPKfJG',  # RCS_Z_id from notebook
                'PRybmF9qkFSZFVf2gxYSk5',  # RCS_Y_id from notebook
                'PRybm3zT77x3kCSSYHCKgG',  # RCS_X_id from notebook
            ]
            
            for block_id in known_block_ids:
                try:
                    block = agent_template_branch.block(block_id)
                    block_data = block.data
                    block_type = block_data.get('type', 'Unknown')
                    
                    if block_type not in blocks_by_type:
                        blocks_by_type[block_type] = []
                    
                    # Filter out internal fields
                    filtered_data = {k: v for k, v in block_data.items() if not k.startswith('_')}
                    
                    blocks_by_type[block_type].append({
                        'id': block_id,
                        'name': block_data.get('name', f'{block_type}_{block_id}'),
                        'data': filtered_data,
                        'type': block_type
                    })
                except Exception as e:
                    print(f"Could not access block {block_id}: {e}")
    
    except Exception as e:
        print(f"Error discovering blocks: {e}")
        import traceback
        traceback.print_exc()
        blocks_by_type = {}
    
    return blocks_by_type

def get_agent_template_structure() -> Dict[str, Any]:
    """
    Get the complete structure of the agent template data for dropdown exploration
    """
    try:
        agent_data = agent_template_branch.data
        return {
            'success': True,
            'data': agent_data,
            'keys': list(agent_data.keys()) if isinstance(agent_data, dict) else []
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def get_property_mutability(block_id: Optional[str] = None, property_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Check if a property is mutable by attempting to get its metadata or trying a test update
    """
    try:
        if block_id:
            # For block properties
            block = agent_template_branch.block(block_id)
            block_data = block.data
            
            # Check if property exists
            if property_name not in block_data:
                return {
                    'success': False,
                    'error': f'Property {property_name} not found in block {block_id}'
                }
            
            # Try to get property metadata if available
            try:
                # Some properties might have metadata indicating mutability
                property_info = getattr(block, f'_{property_name}_info', None)
                if property_info:
                    return {
                        'success': True,
                        'mutable': getattr(property_info, 'mutable', True),
                        'reason': getattr(property_info, 'reason', 'No metadata available')
                    }
            except:
                pass
            
            # For now, assume most properties are mutable except known immutable ones
            immutable_properties = ['id', 'type', '_id', '_type', '_version', '_created', '_updated']
            is_mutable = property_name not in immutable_properties
            
            return {
                'success': True,
                'mutable': is_mutable,
                'reason': 'Immutable system property' if not is_mutable else 'Editable property'
            }
        else:
            # For root properties
            agent_data = agent_template_branch.data
            
            if property_name not in agent_data:
                return {
                    'success': False,
                    'error': f'Root property {property_name} not found'
                }
            
            # Root properties are generally mutable
            immutable_root_properties = ['_id', '_type', '_version', '_created', '_updated']
            is_mutable = property_name not in immutable_root_properties
            
            return {
                'success': True,
                'mutable': is_mutable,
                'reason': 'Immutable system property' if not is_mutable else 'Editable property'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def get_block_by_path(path: str) -> Dict[str, Any]:
    """
    Get a specific block or data by path (e.g., 'blocks.0' or 'components.battery')
    """
    try:
        agent_data = agent_template_branch.data
        
        # Navigate through the path
        current = agent_data
        path_parts = path.split('.')
        
        for part in path_parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            elif isinstance(current, list) and part.isdigit():
                current = current[int(part)]
            else:
                return {'success': False, 'error': f'Invalid path: {path}'}
        
        return {
            'success': True,
            'data': current,
            'path': path
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def update_block_property(block_id: str, property_name: str, new_value: Any) -> Dict[str, Any]:
    """
    Update a specific property of a block using Sedaro client directly
    """
    try:
        # Get the block and update it directly
        block = agent_template_branch.block(block_id)
        block.update(**{property_name: new_value})
        
        # Get the updated value from the block
        updated_value = getattr(block, property_name, new_value)
        
        return {
            'success': True,
            'message': f'Successfully updated {property_name} to {updated_value}',
            'updated_value': updated_value
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def update_root_property(property_name: str, new_value: Any) -> Dict[str, Any]:
    """
    Update a root-level property of the agent template
    """
    try:
        # Update the root property directly
        response = agent_template_branch.update(**{property_name: new_value})
        
        # Get the updated value from the response
        updated_value = getattr(response, property_name, new_value)
        
        return {
            'success': True,
            'message': f'Successfully updated root property {property_name} to {updated_value}',
            'updated_value': updated_value
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def start_simulation() -> Dict[str, Any]:
    """
    Start a simulation using Sedaro client directly
    """
    try:
        # Get scenario branch and start simulation (like in the notebook)
        scenario_branch = sedaro.scenario(SCENARIO_BRANCH_VERSION_ID)
        sim = scenario_branch.simulation
        
        # Start simulation without waiting
        simulation_handle = sim.start(wait=False)
        
        return {
            'success': True,
            'simulation_id': simulation_handle.get('id'),
            'status': simulation_handle.get('status'),
            'message': 'Simulation started successfully'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def get_simulation_status(simulation_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get simulation status and progress without blocking
    """
    try:
        scenario_branch = sedaro.scenario(SCENARIO_BRANCH_VERSION_ID)
        sim = scenario_branch.simulation
        
        if simulation_id:
            # Get specific simulation status
            simulation_handle = sim.status(job_id=simulation_id)
        else:
            # Get latest simulation status
            simulation_handle = sim.status()
        
        status_data = simulation_handle.status()
        status = status_data.get('status', 'UNKNOWN')
        
        # Extract detailed progress information
        progress_info = {}
        if status == 'RUNNING':
            # Get detailed progress data
            progress_data = status_data.get('progress', {})
            if isinstance(progress_data, dict):
                progress_info = {
                    'percentComplete': progress_data.get('percentComplete', 0),
                    'currentTime': progress_data.get('currentTime', 0),
                    'startTime': progress_data.get('startTime', 0),
                    'stopTime': progress_data.get('stopTime', 0),
                    'minTimeStep': progress_data.get('minTimeStep', 0),
                    'argMinTimeStep': progress_data.get('argMinTimeStep', [])
                }
            else:
                progress_info = {'percentComplete': progress_data}
        else:
            progress_info = {'percentComplete': 0}
        
        progress = progress_info.get('percentComplete', 0)
        
        # Create detailed message
        if status == 'RUNNING' and progress_info:
            message = f"Simulation RUNNING ({progress}% complete)"
        else:
            message = f"Simulation {status} ({progress}% complete)"
        
        return {
            'success': True,
            'simulation_id': simulation_handle.get('id'),
            'status': status,
            'progress': progress,
            'progress_info': progress_info,
            'is_complete': status in ['SUCCEEDED', 'FAILED', 'TERMINATED'],
            'message': message
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def abort_simulation(simulation_id: str) -> Dict[str, Any]:
    """
    Abort a running simulation
    """
    try:
        scenario_branch = sedaro.scenario(SCENARIO_BRANCH_VERSION_ID)
        sim = scenario_branch.simulation
        
        # Abort the simulation
        simulation_handle = sim.status(job_id=simulation_id)
        simulation_handle.terminate()
        
        return {
            'success': True,
            'message': f'Simulation {simulation_id} aborted successfully'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def get_simulation_results(simulation_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get simulation results using Sedaro client directly
    """
    try:
        scenario_branch = sedaro.scenario(SCENARIO_BRANCH_VERSION_ID)
        sim = scenario_branch.simulation
        
        if simulation_id:
            # Get specific simulation
            simulation_handle = sim.status(job_id=simulation_id)
        else:
            # Get latest simulation
            simulation_handle = sim.status()
        
        # Get results
        results = simulation_handle.results()
        stats = sim.stats()
        
        return {
            'success': True,
            'simulation_status': simulation_handle.status()['status'],
            'end_time': results.end_time,
            'stats': stats
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

@app.route("/")
def index():
    """Main page with block discovery and property editing interface"""
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Sedaro Agent Template Editor</title>
        <style>
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                padding: 2rem; 
                background-color: #f5f5f5;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                padding: 2rem;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 { color: #333; text-align: center; margin-bottom: 2rem; }
            .block-section {
                margin-bottom: 2rem;
                padding: 1rem;
                border: 1px solid #ddd;
                border-radius: 5px;
                background: #fafafa;
            }
            .block-type {
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 1rem;
                font-size: 1.2em;
            }
            .block-item {
                margin: 1rem 0;
                padding: 1rem;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background: white;
            }
            .block-name {
                font-weight: bold;
                color: #34495e;
                margin-bottom: 0.5rem;
            }
            .property-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 1rem;
                margin-top: 1rem;
            }
            .property-item {
                padding: 0.5rem;
                border: 1px solid #ddd;
                border-radius: 3px;
                background: #f8f9fa;
            }
            .property-name {
                font-weight: bold;
                color: #495057;
                font-size: 0.9em;
            }
            .property-value {
                color: #6c757d;
                font-family: monospace;
                word-break: break-all;
            }
            .edit-button {
                background: #c3adff;
                color: white;
                border: none;
                padding: 0.25rem 0.5rem;
                border-radius: 3px;
                cursor: pointer;
                font-size: 0.8em;
                margin-left: 0.5rem;
            }
            .edit-button:hover {
                background: #a78bfa;
            }
            .modal {
                display: none;
                position: fixed;
                z-index: 1000;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0,0,0,0.5);
            }
            .modal-content {
                background-color: white;
                margin: 15% auto;
                padding: 2rem;
                border-radius: 8px;
                width: 80%;
                max-width: 500px;
            }
            .close {
                color: #aaa;
                float: right;
                font-size: 28px;
                font-weight: bold;
                cursor: pointer;
            }
            .close:hover {
                color: black;
            }
            input, select, textarea {
                width: 100%;
                padding: 0.5rem;
                margin: 0.5rem 0;
                border: 1px solid #ddd;
                border-radius: 4px;
                box-sizing: border-box;
            }
            .save-button {
                background: #c3adff;
                color: white;
                border: none;
                padding: 0.5rem 1rem;
                border-radius: 4px;
                cursor: pointer;
                margin-top: 1rem;
            }
            .save-button:hover {
                background: #a78bfa;
            }
            .loading {
                text-align: center;
                color: #666;
                font-style: italic;
            }
            .error {
                color: #dc3545;
                background: #f8d7da;
                padding: 0.5rem;
                border-radius: 4px;
                margin: 0.5rem 0;
            }
            .success {
                color: #155724;
                background: #d4edda;
                padding: 0.5rem;
                border-radius: 4px;
                margin: 0.5rem 0;
            }
            .simulation-controls {
                text-align: center;
                margin-bottom: 2rem;
                padding: 1rem;
                background: #e9ecef;
                border-radius: 5px;
            }
            .simulation-controls button {
                margin: 0 0.5rem;
            }
            .template-explorer {
                margin-top: 3rem;
                padding: 2rem;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                background: #f8f9fa;
            }
            .template-explorer h2 {
                color: #495057;
                margin-bottom: 1rem;
            }
            .component-selector {
                margin-bottom: 2rem;
            }
            .dropdown-container {
                position: relative;
                max-width: 400px;
            }
            .dropdown-container label {
                display: block;
                font-weight: bold;
                color: #495057;
                margin-bottom: 0.5rem;
            }
            .searchable-dropdown {
                position: relative;
            }
            .searchable-dropdown input {
                width: 100%;
                padding: 0.75rem;
                border: 2px solid #dee2e6;
                border-radius: 4px;
                font-size: 1rem;
                background: white;
            }
            .searchable-dropdown input:focus {
                outline: none;
                border-color: #007bff;
                box-shadow: 0 0 0 0.2rem rgba(0,123,255,.25);
            }
            .dropdown-list {
                position: absolute;
                top: 100%;
                left: 0;
                right: 0;
                background: white;
                border: 1px solid #dee2e6;
                border-top: none;
                border-radius: 0 0 4px 4px;
                max-height: 200px;
                overflow-y: auto;
                z-index: 1000;
                display: none;
            }
            .dropdown-item {
                padding: 0.5rem 0.75rem;
                cursor: pointer;
                border-bottom: 1px solid #f8f9fa;
            }
            .dropdown-item:hover {
                background: #f8f9fa;
            }
            .dropdown-item.selected {
                background: #007bff;
                color: white;
            }
            .editor-section {
                background: white;
                padding: 1.5rem;
                border-radius: 5px;
                border: 1px solid #dee2e6;
            }
            .editor-section h3 {
                color: #495057;
                margin-bottom: 1rem;
                border-bottom: 2px solid #e9ecef;
                padding-bottom: 0.5rem;
            }
            .property-item {
                margin-bottom: 1rem;
                padding: 1rem;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                background: #f8f9fa;
            }
            .property-name {
                font-weight: bold;
                color: #495057;
                margin-bottom: 0.5rem;
                font-size: 0.9em;
            }
            .property-value {
                display: flex;
                gap: 0.5rem;
                align-items: center;
            }
            .property-value input {
                flex: 1;
                margin: 0;
            }
            .property-value button {
                margin: 0;
                padding: 0.25rem 0.5rem;
                font-size: 0.8em;
            }
            .property-item.immutable {
                opacity: 0.6;
                background: #f8f9fa;
                border: 1px solid #dee2e6;
            }
            .property-item.immutable .property-name {
                color: #6c757d;
            }
            .property-item.immutable .property-value input {
                background: #e9ecef;
                color: #6c757d;
                cursor: not-allowed;
            }
            .property-item.immutable .property-value button {
                background: #6c757d;
                cursor: not-allowed;
            }
            .property-item.immutable .property-value button:hover {
                background: #6c757d;
            }
            .mutability-indicator {
                font-size: 0.8em;
                margin-left: 0.5rem;
                padding: 0.2rem 0.4rem;
                border-radius: 3px;
                font-weight: normal;
            }
            .mutability-indicator.mutable {
                background: #d4edda;
                color: #155724;
            }
            .mutability-indicator.immutable {
                background: #f8d7da;
                color: #721c24;
            }
            .simulation-progress {
                margin: 2rem 0;
                padding: 1.5rem;
                background: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #dee2e6;
            }
            .simulation-progress h3 {
                margin-bottom: 1rem;
                color: #495057;
            }
            .progress-container {
                display: flex;
                align-items: center;
                gap: 1rem;
                margin-bottom: 1rem;
            }
            .progress-bar {
                flex: 1;
                height: 20px;
                background: #e9ecef;
                border-radius: 10px;
                overflow: hidden;
            }
            .progress-fill {
                height: 100%;
                background: linear-gradient(90deg, #c3adff, #a78bfa);
                width: 0%;
                transition: width 0.3s ease;
            }
            .progress-text {
                font-weight: bold;
                color: #495057;
                min-width: 50px;
            }
            .status-text {
                color: #6c757d;
                font-style: italic;
            }
            
            .progress-details {
                margin-top: 15px;
                padding: 10px;
                background: #f8f9fa;
                border-radius: 5px;
                border-left: 3px solid #c3adff;
            }
            
            .detail-item {
                margin: 5px 0;
                font-size: 14px;
            }
            
            .detail-item strong {
                color: #495057;
            }
            .toast-notification {
                position: fixed;
                top: 20px;
                right: 20px;
                background: #28a745;
                color: white;
                padding: 1rem 1.5rem;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                z-index: 10000;
                transform: translateX(400px);
                transition: transform 0.3s ease-in-out;
                max-width: 300px;
                font-weight: 500;
            }
            .toast-notification.show {
                transform: translateX(0);
            }
            .toast-notification.success {
                background: #28a745;
                border-left: 4px solid #1e7e34;
            }
            .toast-notification.error {
                background: #dc3545;
                border-left: 4px solid #c82333;
            }
            .toast-notification .toast-icon {
                margin-right: 0.5rem;
                font-size: 1.2em;
            }
        </style>
    </head>
    <body>
        <!-- Toast Notification -->
        <div id="toastNotification" class="toast-notification" style="display: none;">
            <span class="toast-icon">✅</span>
            <span id="toastMessage">Property updated successfully!</span>
        </div>

        <div class="container">
            <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 2rem; gap: 15px;">
                <img src="/violetlabsinc_logo.jpeg" alt="Violet Labs Logo" style="height: 60px; max-width: 200px; object-fit: contain;">
                <h1 style="margin: 0; color: #c3adff; font-size: 2.5rem; font-weight: bold;">Violet Sedaro Platform</h1>
            </div>
            
            <div class="simulation-controls">
                <button id="simulateBtn" class="save-button" onclick="startSimulation()" style="background: #17a2b8;">
                    🚀 Start Simulation
                </button>
                <button id="statusBtn" class="save-button" onclick="checkSimulationStatus()" style="background: #ffc107; color: #212529;">
                    📈 Check Status
                </button>
                <button id="resultsBtn" class="save-button" onclick="getSimulationResults()" style="background: #6f42c1;">
                    📊 Get Results
                </button>
                <button id="refreshBtn" class="save-button" onclick="loadBlocks()" style="background: #6c757d;">
                    🔄 Refresh Blocks
                </button>
                <button id="refreshTemplateBtn" class="save-button" onclick="refreshTemplate()" style="background: #fd7e14;">
                    🔄 Refresh Template
                </button>
            </div>
            
            <!-- Simulation Progress -->
            <div id="simulationProgress" style="display: none;" class="simulation-progress">
                <h3>🔄 Simulation Progress</h3>
                <div class="progress-container">
                    <div class="progress-bar">
                        <div id="progressFill" class="progress-fill"></div>
                    </div>
                    <div id="progressText" class="progress-text">0%</div>
                    <button id="abortBtn" class="save-button" onclick="abortSimulation()" style="background: #dc3545;">
                        🛑 Abort
                    </button>
                </div>
                <div id="statusText" class="status-text">Starting simulation...</div>
                <div id="progressDetails" class="progress-details" style="display: none;">
                    <div class="detail-item">
                        <strong>Current Time:</strong> <span id="currentTime">-</span>
                    </div>
                    <div class="detail-item">
                        <strong>Time Range:</strong> <span id="timeRange">-</span>
                    </div>
                    <div class="detail-item">
                        <strong>Min Time Step:</strong> <span id="minTimeStep">-</span>
                    </div>
                </div>
            </div>
            
            <div id="loading" class="loading">Discovering blocks and properties...</div>
            <div id="content" style="display: none;"></div>
            <div id="simulationStatus" style="display: none;"></div>
            
            <!-- Interactive Template Explorer -->
            <div class="template-explorer">
                <h2>🔍 Interactive Template Explorer</h2>
                <p>Select a component from the dropdown and edit its properties:</p>
                
                <div class="component-selector">
                    <div class="dropdown-container">
                        <label for="componentDropdown">Select Component:</label>
                        <div class="searchable-dropdown">
                            <input type="text" id="searchInput" placeholder="Search components..." onkeyup="filterDropdown()">
                            <div id="dropdownList" class="dropdown-list"></div>
                        </div>
                    </div>
                </div>
                
                <div id="componentEditor" style="display: none;">
                    <div class="editor-section">
                        <h3 id="selectedComponentName">Component Properties</h3>
                        <div id="componentProperties"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Edit Modal -->
        <div id="editModal" class="modal">
            <div class="modal-content">
                <span class="close">&times;</span>
                <h3>Edit Property</h3>
                <div id="editForm">
                    <label for="propertyName">Property:</label>
                    <input type="text" id="propertyName" readonly>
                    
                    <label for="propertyValue">New Value:</label>
                    <input type="text" id="propertyValue">
                    
                    <button class="save-button" onclick="saveProperty()">Save Changes</button>
                </div>
                <div id="editResult"></div>
            </div>
        </div>

        <script>
            let currentBlockId = null;
            let currentPropertyName = null;
            let currentSimulationId = null;
            let progressInterval = null;

            async function loadBlocks() {
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
                        return false;
                    }
                } catch (error) {
                    console.error('Error checking simulation status:', error);
                    return false;
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

            // Close dropdown when clicking outside
            document.addEventListener('click', function(event) {
                const dropdown = document.querySelector('.searchable-dropdown');
                if (!dropdown.contains(event.target)) {
                    document.getElementById('dropdownList').style.display = 'none';
                }
            });

            // Load components when page loads
            document.addEventListener('DOMContentLoaded', function() {
                loadBlocks();
                loadComponents();
            });

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
                        
                        // Reload components and blocks
                        await loadComponents();
                        await loadBlocks();
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
        </script>
    </body>
    </html>
    """
    return render_template_string(html_template)

@app.route("/api/blocks")
def api_blocks():
    """API endpoint to get all blocks and their properties"""
    try:
        blocks = discover_blocks()
        return jsonify(blocks)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/update_property", methods=['POST'])
def api_update_property():
    """API endpoint to update a block property using Sedaro client directly"""
    try:
        data = request.get_json()
        block_id = data.get('block_id')
        property_name = data.get('property_name')
        new_value = data.get('new_value')
        
        if not all([block_id, property_name, new_value]):
            return jsonify({'error': 'Missing required parameters'}), 400
        
        # Try to convert value to appropriate type
        try:
            if isinstance(new_value, str):
                if new_value.replace('.', '').replace('-', '').isdigit():
                    if '.' in new_value:
                        new_value = float(new_value)
                    else:
                        new_value = int(new_value)
                elif new_value.lower() in ['true', 'false']:
                    new_value = new_value.lower() == 'true'
        except:
            pass  # Keep as string if conversion fails
        
        result = update_block_property(block_id, property_name, new_value)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/update_root_property", methods=['POST'])
def api_update_root_property():
    """API endpoint to update a root-level property of the agent template"""
    try:
        data = request.get_json()
        property_name = data.get('property_name')
        new_value = data.get('new_value')
        
        if not all([property_name, new_value]):
            return jsonify({'error': 'Missing required parameters'}), 400
        
        # Try to convert value to appropriate type
        try:
            # Check if it's a number
            if new_value.replace('.', '').replace('-', '').isdigit():
                if '.' in new_value:
                    new_value = float(new_value)
                else:
                    new_value = int(new_value)
            elif new_value.lower() in ['true', 'false']:
                new_value = new_value.lower() == 'true'
        except:
            pass  # Keep as string if conversion fails
        
        result = update_root_property(property_name, new_value)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/simulate", methods=['POST'])
def api_simulate():
    """API endpoint to start a simulation using Sedaro client directly"""
    try:
        result = start_simulation()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/simulation_status", methods=['GET'])
def api_simulation_status():
    """API endpoint to get simulation status and progress"""
    try:
        simulation_id = request.args.get('simulation_id')
        result = get_simulation_status(simulation_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/abort_simulation", methods=['POST'])
def api_abort_simulation():
    """API endpoint to abort a simulation"""
    try:
        data = request.get_json()
        simulation_id = data.get('simulation_id')
        
        if not simulation_id:
            return jsonify({'error': 'Missing simulation_id parameter'}), 400
        
        result = abort_simulation(simulation_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/results", methods=['GET'])
def api_results():
    """API endpoint to get simulation results using Sedaro client directly"""
    try:
        result = get_simulation_results()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/template_structure", methods=['GET'])
def api_template_structure():
    """API endpoint to get the complete agent template structure"""
    try:
        result = get_agent_template_structure()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/block/<block_id>/properties", methods=['GET'])
def api_block_properties(block_id):
    """API endpoint to get properties of a specific block"""
    try:
        block = agent_template_branch.block(block_id)
        block_data = block.data
        # Filter out internal fields and return editable properties
        return jsonify({k: v for k, v in block_data.items() if not k.startswith('_')})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/mutability", methods=['GET'])
def api_mutability():
    """API endpoint to check if a property is mutable"""
    try:
        block_id = request.args.get('block_id')
        property_name = request.args.get('property_name')
        
        if not property_name:
            return jsonify({'error': 'Missing property_name parameter'}), 400
        
        result = get_property_mutability(block_id, property_name)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/explore_path", methods=['POST'])
def api_explore_path():
    """API endpoint to explore a specific path in the agent template data"""
    try:
        data = request.get_json()
        path = data.get('path')
        
        if not path:
            return jsonify({'error': 'Missing path parameter'}), 400
        
        result = get_block_by_path(path)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/refresh_template", methods=['POST'])
def api_refresh_template():
    """API endpoint to refresh the agent template connection"""
    try:
        data = request.get_json()
        template_id = data.get('template_id') if data else None
        
        result = refresh_agent_template(template_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)

