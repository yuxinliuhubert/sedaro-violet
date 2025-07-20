from flask import Flask, jsonify, request, render_template_string, render_template
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

def get_simulation_statistics(simulation_id: Optional[str] = None, wait: bool = True, streams: Optional[List] = None) -> Dict[str, Any]:
    """
    Get simulation statistics using Sedaro client directly
    """
    try:
        scenario_branch = sedaro.scenario(SCENARIO_BRANCH_VERSION_ID)
        sim = scenario_branch.simulation
        
        if simulation_id:
            # Get specific simulation
            simulation_handle = sim.status(job_id=simulation_id)
            # Get statistics for the specific simulation
            if streams:
                stats = simulation_handle.stats(wait=wait, streams=streams)
            else:
                stats = simulation_handle.stats(wait=wait)
        else:
            # Get latest simulation
            simulation_handle = sim.status()
            # Get statistics for the latest simulation
            if streams:
                stats = sim.stats(wait=wait, streams=streams)
            else:
                stats = sim.stats(wait=wait)
        
        return {
            'success': True,
            'simulation_id': simulation_handle.get('id'),
            'simulation_status': simulation_handle.status()['status'],
            'statistics': stats
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def get_available_streams() -> Dict[str, Any]:
    """
    Get available streams for statistics based on actual scenario branch structure
    """
    try:
        scenario_branch = sedaro.scenario(SCENARIO_BRANCH_VERSION_ID)
        available_streams = []
        
        # Get TemplatedAgent streams
        try:
            templated_agents = scenario_branch.TemplatedAgent.get_all()
            for agent in templated_agents:
                agent_id = agent.id
                agent_name = agent.name
                
                # Add agent-level streams
                available_streams.extend([
                    {
                        'name': f'{agent_name}_position',
                        'path': (agent_id, 'position'),
                        'display_name': f'{agent_name} - Position',
                        'agent_id': agent_id,
                        'agent_type': 'TemplatedAgent'
                    },
                    {
                        'name': f'{agent_name}_velocity',
                        'path': (agent_id, 'velocity'),
                        'display_name': f'{agent_name} - Velocity',
                        'agent_id': agent_id,
                        'agent_type': 'TemplatedAgent'
                    },
                    {
                        'name': f'{agent_name}_attitude',
                        'path': (agent_id, 'attitude'),
                        'display_name': f'{agent_name} - Attitude',
                        'agent_id': agent_id,
                        'agent_type': 'TemplatedAgent'
                    },
                    {
                        'name': f'{agent_name}_angular_velocity',
                        'path': (agent_id, 'angularVelocity'),
                        'display_name': f'{agent_name} - Angular Velocity',
                        'agent_id': agent_id,
                        'agent_type': 'TemplatedAgent'
                    }
                ])
                
                # Add coordinate system specific streams
                if hasattr(agent, 'position') and agent.position:
                    for coord_sys in agent.position.keys():
                        available_streams.extend([
                            {
                                'name': f'{agent_name}_position_{coord_sys}',
                                'path': (agent_id, 'position', coord_sys),
                                'display_name': f'{agent_name} - Position ({coord_sys.upper()})',
                                'agent_id': agent_id,
                                'agent_type': 'TemplatedAgent',
                                'coordinate_system': coord_sys
                            }
                        ])
                
                if hasattr(agent, 'velocity') and agent.velocity:
                    for coord_sys in agent.velocity.keys():
                        available_streams.extend([
                            {
                                'name': f'{agent_name}_velocity_{coord_sys}',
                                'path': (agent_id, 'velocity', coord_sys),
                                'display_name': f'{agent_name} - Velocity ({coord_sys.upper()})',
                                'agent_id': agent_id,
                                'agent_type': 'TemplatedAgent',
                                'coordinate_system': coord_sys
                            }
                        ])
                        
        except Exception as e:
            print(f"Error getting TemplatedAgent streams: {e}")
        
        # Get PeripheralAgent streams (includes all peripheral types)
        try:
            peripheral_agents = scenario_branch.PeripheralAgent.get_all()
            for agent in peripheral_agents:
                agent_id = agent.id
                agent_name = agent.name
                agent_type = agent.type
                
                # Add agent-level streams
                available_streams.extend([
                    {
                        'name': f'{agent_name}_position',
                        'path': (agent_id, 'position'),
                        'display_name': f'{agent_name} - Position ({agent_type})',
                        'agent_id': agent_id,
                        'agent_type': agent_type
                    },
                    {
                        'name': f'{agent_name}_velocity',
                        'path': (agent_id, 'velocity'),
                        'display_name': f'{agent_name} - Velocity ({agent_type})',
                        'agent_id': agent_id,
                        'agent_type': agent_type
                    },
                    {
                        'name': f'{agent_name}_attitude',
                        'path': (agent_id, 'attitude'),
                        'display_name': f'{agent_name} - Attitude ({agent_type})',
                        'agent_id': agent_id,
                        'agent_type': agent_type
                    },
                    {
                        'name': f'{agent_name}_angular_velocity',
                        'path': (agent_id, 'angularVelocity'),
                        'display_name': f'{agent_name} - Angular Velocity ({agent_type})',
                        'agent_id': agent_id,
                        'agent_type': agent_type
                    }
                ])
                
                # Add coordinate system specific streams
                if hasattr(agent, 'position') and agent.position:
                    for coord_sys in agent.position.keys():
                        available_streams.extend([
                            {
                                'name': f'{agent_name}_position_{coord_sys}',
                                'path': (agent_id, 'position', coord_sys),
                                'display_name': f'{agent_name} - Position ({coord_sys.upper()})',
                                'agent_id': agent_id,
                                'agent_type': agent_type,
                                'coordinate_system': coord_sys
                            }
                        ])
                
                if hasattr(agent, 'velocity') and agent.velocity:
                    for coord_sys in agent.velocity.keys():
                        available_streams.extend([
                            {
                                'name': f'{agent_name}_velocity_{coord_sys}',
                                'path': (agent_id, 'velocity', coord_sys),
                                'display_name': f'{agent_name} - Velocity ({coord_sys.upper()})',
                                'agent_id': agent_id,
                                'agent_type': agent_type,
                                'coordinate_system': coord_sys
                            }
                        ])
                
                # Add agent-specific properties
                if hasattr(agent, 'body') and agent.body:
                    available_streams.append({
                        'name': f'{agent_name}_body',
                        'path': (agent_id, 'body'),
                        'display_name': f'{agent_name} - Body ({agent_type})',
                        'agent_id': agent_id,
                        'agent_type': agent_type
                    })
                
                if hasattr(agent, 'timeStepConstraints') and agent.timeStepConstraints:
                    available_streams.append({
                        'name': f'{agent_name}_time_step_constraints',
                        'path': (agent_id, 'timeStepConstraints'),
                        'display_name': f'{agent_name} - Time Step Constraints ({agent_type})',
                        'agent_id': agent_id,
                        'agent_type': agent_type
                    })
                        
        except Exception as e:
            print(f"Error getting PeripheralAgent streams: {e}")
        
        # Add template-specific streams if we have access to the agent template
        try:
            # Get streams from the agent template
            template_streams = [
                {'name': 'template_power', 'path': ('power',), 'display_name': 'Power System'},
                {'name': 'template_thermal', 'path': ('thermal',), 'display_name': 'Thermal System'},
                {'name': 'template_battery', 'path': ('battery',), 'display_name': 'Battery System'},
                {'name': 'template_thruster', 'path': ('thruster',), 'display_name': 'Thruster System'},
                {'name': 'template_sensor', 'path': ('sensor',), 'display_name': 'Sensor System'},
                {'name': 'template_communication', 'path': ('communication',), 'display_name': 'Communication System'},
                {'name': 'template_gnc', 'path': ('gnc',), 'display_name': 'Guidance, Navigation & Control'},
                {'name': 'template_cdh', 'path': ('cdh',), 'display_name': 'Command & Data Handling'}
            ]
            available_streams.extend(template_streams)
            
        except Exception as e:
            print(f"Error getting template streams: {e}")
        
        return {
            'success': True,
            'streams': available_streams,
            'note': f'Found {len(available_streams)} streams from scenario branch'
        }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

@app.route("/")
def index():
    """Main page with block discovery and property editing interface"""
    return render_template('index.html')

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
        simulation_id = request.args.get('simulation_id')
        result = get_simulation_results(simulation_id)
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

@app.route("/api/simulation_statistics", methods=['POST'])
def api_simulation_statistics():
    """API endpoint to get simulation statistics"""
    try:
        data = request.get_json() or {}
        simulation_id = data.get('simulation_id')
        wait = data.get('wait', True)
        streams = data.get('streams')
        
        result = get_simulation_statistics(simulation_id, wait, streams)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/available_streams", methods=['GET'])
def api_available_streams():
    """API endpoint to get available streams for statistics"""
    try:
        result = get_available_streams()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)

