from flask import Flask, jsonify, request, render_template_string
from sedaro import SedaroApiClient
from pprint import pprint
import json
from typing import Dict, List, Any

API_KEY = "PKDqMrtcTK4plJgL7qVlQD.0xQph1lyKzd-pV0-ZL7bRIH7BX54Yjqbz6tluwut3Hvp8XE-RVbfHSz2o5vC77scUhg2xBFuBybplxY6FyXXMQ"
TEMP_AGENT_REPO_BRANCH_ID = "PS5ZPCp6mh5yXLH3lkCWFj" # Specific Repo of the Templated agent 
SCENARIO_BRANCH_VERSION_ID = "PRx5rSwrGfkK4n9vFXmVbt" # Version 2
WORKSPACE_ID = "PQtnGZNNPdzZM5JdVhP5P9" # Violet/Ethreal workspace

# Define modules
sedaro = SedaroApiClient(api_key = API_KEY)
# agent template is only for satellite model (agent), and don't copy the model repo ID, only the branch ID (version)
agent_template_branch = sedaro.agent_template(TEMP_AGENT_REPO_BRANCH_ID) # we are going to change this templated agent

app = Flask(__name__, static_folder='static', static_url_path='')

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

def get_block_properties(block_id: str) -> Dict[str, Any]:
    """
    Get properties of a specific block
    """
    try:
        block = agent_template_branch.block(block_id)
        block_data = block.data
        # Filter out internal fields and return editable properties
        return {k: v for k, v in block_data.items() if not k.startswith('_')}
    except Exception as e:
        return {'error': str(e)}

def get_all_block_ids() -> List[str]:
    """
    Get all available block IDs from the agent template
    """
    block_ids = []
    try:
        agent_data = agent_template_branch.data
        
        # Try to find blocks in the data structure
        if 'blocks' in agent_data:
            for block in agent_data['blocks']:
                if isinstance(block, dict) and 'id' in block:
                    block_ids.append(block['id'])
        elif 'data' in agent_data and 'blocks' in agent_data['data']:
            for block in agent_data['data']['blocks']:
                if isinstance(block, dict) and 'id' in block:
                    block_ids.append(block['id'])
        
        # If no blocks found, try known IDs
        if not block_ids:
            known_block_ids = [
                'PK3PCpCJRn6LpwvhWzNtsb',  # battery_cell_id
                'PRx5qGqQD59tCW4V9tBGQb',  # battery_pack_id
                'PRx7YwymYJgtlTDBjPKfJG',  # RCS_Z_id
                'PRybmF9qkFSZFVf2gxYSk5',  # RCS_Y_id
                'PRybm3zT77x3kCSSYHCKgG',  # RCS_X_id
            ]
            
            for block_id in known_block_ids:
                try:
                    block = agent_template_branch.block(block_id)
                    block_ids.append(block_id)
                except:
                    pass
        
    except Exception as e:
        print(f"Error getting block IDs: {e}")
    
    return block_ids

def update_block_property(block_id: str, property_name: str, new_value: Any) -> Dict[str, Any]:
    """
    Update a specific property of a block
    """
    try:
        block = agent_template_branch.block(block_id)
        update_data = {property_name: new_value}
        block.update(**update_data)
        
        # Return updated block data
        return {
            'success': True,
            'message': f'Successfully updated {property_name} to {new_value}',
            'updated_data': get_block_properties(block_id)
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
                background: #007bff;
                color: white;
                border: none;
                padding: 0.25rem 0.5rem;
                border-radius: 3px;
                cursor: pointer;
                font-size: 0.8em;
                margin-left: 0.5rem;
            }
            .edit-button:hover {
                background: #0056b3;
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
                background: #28a745;
                color: white;
                border: none;
                padding: 0.5rem 1rem;
                border-radius: 4px;
                cursor: pointer;
                margin-top: 1rem;
            }
            .save-button:hover {
                background: #218838;
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
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔧 Sedaro Agent Template Editor</h1>
            <div style="text-align: center; margin-bottom: 2rem;">
                <button id="simulateBtn" class="save-button" onclick="startSimulation()" style="background: #17a2b8; margin-right: 1rem;">
                    🚀 Start Simulation
                </button>
                <button id="refreshBtn" class="save-button" onclick="loadBlocks()" style="background: #6c757d;">
                    🔄 Refresh Blocks
                </button>
            </div>
            <div id="loading" class="loading">Discovering blocks and properties...</div>
            <div id="content" style="display: none;"></div>
            <div id="simulationStatus" style="display: none;"></div>
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

            async function startSimulation() {
                const statusDiv = document.getElementById('simulationStatus');
                const simulateBtn = document.getElementById('simulateBtn');
                
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
                        statusDiv.innerHTML = `
                            <div class="success">
                                <h4>✅ Simulation Started Successfully!</h4>
                                <p><strong>Simulation ID:</strong> ${result.simulation_id}</p>
                                <p><strong>Status:</strong> ${result.status}</p>
                                <p><strong>Message:</strong> ${result.message}</p>
                            </div>
                        `;
                    } else {
                        statusDiv.innerHTML = `<div class="error">❌ Failed to start simulation: ${result.error}</div>`;
                    }
                } catch (error) {
                    statusDiv.innerHTML = `<div class="error">❌ Error starting simulation: ${error.message}</div>`;
                } finally {
                    simulateBtn.disabled = false;
                }
            }

            // Load blocks when page loads
            document.addEventListener('DOMContentLoaded', loadBlocks);
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

@app.route("/api/block/<block_id>/properties")
def api_block_properties(block_id):
    """API endpoint to get properties of a specific block"""
    try:
        properties = get_block_properties(block_id)
        return jsonify(properties)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/block_ids")
def api_block_ids():
    """API endpoint to get all available block IDs"""
    try:
        block_ids = get_all_block_ids()
        return jsonify({
            'block_ids': block_ids,
            'count': len(block_ids)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/update_property", methods=['POST'])
def api_update_property():
    """API endpoint to update a block property"""
    try:
        data = request.get_json()
        block_id = data.get('block_id')
        property_name = data.get('property_name')
        new_value = data.get('new_value')
        
        if not all([block_id, property_name, new_value]):
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
        
        result = update_block_property(block_id, property_name, new_value)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/simulate", methods=['POST'])
def api_simulate():
    """API endpoint to start a simulation"""
    try:
        # Get scenario branch and start simulation
        scenario_branch = sedaro.scenario(SCENARIO_BRANCH_VERSION_ID)
        sim = scenario_branch.simulation
        
        simulation_handle = sim.start(wait=False)
        
        return jsonify({
            'success': True,
            'simulation_id': simulation_handle.get('id'),
            'status': simulation_handle.get('status'),
            'message': 'Simulation started successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
