# Agent Template Deduplication Script

This script generates a new model using only the non-duplicate parts of the `agent_template.data`. It identifies duplicate blocks based on their type and name, removes duplicates while preserving one instance of each, and creates a new repository with the deduplicated model.

## Features

- **Duplicate Detection**: Identifies blocks with the same type and name
- **Dependency Analysis**: Analyzes which blocks reference duplicate blocks that will be removed
- **Reference Mapping**: Automatically fixes references to point to the kept duplicate
- **New Repository Creation**: Creates a fresh repository with the deduplicated model
- **Verbose Logging**: Provides detailed information about the deduplication process

## Files

- `deduplicate_agent_template_simple.py` - Main script (simplified version without complex type annotations)
- `deduplicate_agent_template.py` - Full version with type annotations (may have linter warnings)

## Configuration

Update these values in the script before running:

```python
API_KEY = "your_api_key_here"
TEMP_AGENT_REPO_BRANCH_ID = "your_template_branch_id"
WORKSPACE_ID = "your_workspace_id"
```

## Usage

### Basic Usage

```bash
python deduplicate_agent_template_simple.py
```

### Programmatic Usage

```python
from deduplicate_agent_template_simple import create_new_model_with_deduplication

# Create a new deduplicated model
new_branch = create_new_model_with_deduplication(
    api_key="your_api_key",
    workspace_id="your_workspace_id",
    template_branch_id="your_template_branch_id",
    new_repo_name="My_Deduplicated_Model",
    verbose=True
)

print(f"New branch ID: {new_branch.id}")
```

## How It Works

1. **Load Template Data**: Fetches the agent template data from the specified branch
2. **Identify Duplicates**: Groups blocks by (type, name) and identifies duplicates
3. **Select Representatives**: Keeps one instance of each duplicate group
4. **Analyze Dependencies**: Finds blocks that reference duplicate blocks
5. **Create New Repository**: Creates a new Spacecraft repository
6. **Map References**: Builds a mapping from old IDs to new IDs
7. **Fix References**: Updates references to point to kept duplicates
8. **Create Blocks**: Creates the deduplicated blocks in the new repository

## Output

The script provides detailed output including:

- Total number of blocks in the template
- Number of unique blocks to keep
- Number of duplicate groups found
- Details about each duplicate group (type, name, instances)
- Number of blocks that reference removed duplicates
- List of created/updated block IDs

## Example Output

```
=== Agent Template Deduplication Script ===

Loading template data from branch: PRkHJlBrpwLDCqPqfbkdrb
Total blocks in template: 150
Duplicate group found: Component 'Battery' - 3 instances
  Keeping: PS2RplQSj4BWmhzMmPjhcw
  Removing: ['PS2RplQVhDb66QvJmsYCLW', 'PS2RplQXbXTTTvk39J6CTw']
Unique blocks to keep: 120
Duplicate groups found: 10
Found 5 removed blocks that are referenced by other blocks
Creating new repository: Deduplicated_Agent_Model
Creating 45 new blocks...
✅ Created/updated: ['NSghWfrUj9OyAK8OBAXa-', 'NSghYm2RqDibih0igHFc-', ...]

=== Summary ===
New branch ID: PRx5rSwrGfkK4n9vFXmVbt
Deduplication complete!
```

## Requirements

- Python 3.6+
- `sedaro` package
- Valid Sedaro API key
- Access to the specified workspace and template branch

## Notes

- The script preserves the **last instance** of each duplicate group and removes the first and middle instances
- All references to removed duplicates are automatically updated to point to the kept instance
- The new repository is created as a Spacecraft metamodel type
- The script handles both string and list references to other blocks 