#!/usr/bin/env python3
"""
Script to generate a new model using only the non-duplicate parts of agent_template.data

This script:
1. Loads the agent template data
2. Identifies duplicate blocks based on type and name
3. Creates a new repository with only unique blocks
4. Handles reference mapping for dependencies
"""

from sedaro import SedaroApiClient
from pprint import pprint
import json
from collections import defaultdict

# Configuration - Update these values as needed
API_KEY = "PKDqMrtcTK4plJgL7qVlQD.0xQph1lyKzd-pV0-ZL7bRIH7BX54Yjqbz6tluwut3Hvp8XE-RVbfHSz2o5vC77scUhg2xBFuBybplxY6FyXXMQ"
TEMP_AGENT_REPO_BRANCH_ID = "PRkHJlBrpwLDCqPqfbkdrb"  # Specific Repo of the Templated agent
WORKSPACE_ID = "PQtnGZNNPdzZM5JdVhP5P9"  # Violet/Ethreal workspace


def identify_duplicates(blocks):
    """
    Identify duplicate blocks based on type and name.
    
    Args:
        blocks: Dictionary of block_id -> block_data
        
    Returns:
        Tuple of (duplicate_groups, unique_block_ids)
        - duplicate_groups: Dict mapping (type, name) -> list of block_ids
        - unique_block_ids: Set of block_ids to keep (one from each duplicate group)
    """
    # Group blocks by (type, name)
    type_name_groups = defaultdict(list)
    
    for block_id, block_data in blocks.items():
        block_type = block_data.get('type', '')
        block_name = block_data.get('name', '')
        key = (block_type, block_name)
        type_name_groups[key].append(block_id)
    
    # Identify duplicates and select unique representatives
    duplicate_groups = {}
    unique_block_ids = set()
    
    for (block_type, block_name), block_ids in type_name_groups.items():
        if len(block_ids) > 1:
            # This is a duplicate group
            duplicate_groups[(block_type, block_name)] = block_ids
            # Keep only the last entry
            unique_block_ids.add(block_ids[-1])
            print(f"Duplicate group found: {block_type} '{block_name}' - {len(block_ids)} instances")
            print(f"  Block IDs: {block_ids}")
            print(f"  Keeping ONLY LAST entry: {block_ids[-1]}")
            print(f"  Removing FIRST and middle entries: {block_ids[:-1]}")
        else:
            # This is a unique block
            unique_block_ids.add(block_ids[0])
    
    return duplicate_groups, unique_block_ids


def create_deduplicated_schema(blocks, unique_block_ids):
    """
    Create a new schema with only unique blocks.
    
    Args:
        blocks: Original blocks dictionary
        unique_block_ids: Set of block IDs to keep
        
    Returns:
        New blocks dictionary with only unique blocks
    """
    deduplicated_blocks = {}
    
    for block_id in unique_block_ids:
        if block_id in blocks:
            deduplicated_blocks[block_id] = blocks[block_id]
    
    return deduplicated_blocks


def analyze_dependencies(blocks, duplicate_groups):
    """
    Analyze which blocks reference the duplicate blocks that will be removed.
    
    Args:
        blocks: All blocks dictionary
        duplicate_groups: Duplicate groups mapping
        
    Returns:
        Dictionary mapping removed_block_id -> list of (referencing_block_id, field_name) tuples
    """
    # Create a reverse mapping for duplicate groups
    removed_to_kept = {}
    for (block_type, block_name), block_ids in duplicate_groups.items():
        kept_id = block_ids[0]
        for removed_id in block_ids[1:]:
            removed_to_kept[removed_id] = kept_id
    
    # Find blocks that reference removed blocks
    references_to_fix = defaultdict(list)
    
    for block_id, block_data in blocks.items():
        for key, value in block_data.items():
            if key in ('id', 'type'):
                continue
                
            # Check if this field references a removed block
            if isinstance(value, str) and value in removed_to_kept:
                references_to_fix[value].append((block_id, key))
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str) and item in removed_to_kept:
                        references_to_fix[item].append((block_id, key))
    
    return references_to_fix


def create_new_model_with_deduplication(
    api_key,
    workspace_id,
    template_branch_id,
    new_repo_name,
    verbose=True
):
    """
    Create a new model using only non-duplicate parts of the agent template.
    
    Args:
        api_key: Sedaro API key
        workspace_id: Workspace ID
        template_branch_id: Template branch ID
        new_repo_name: Name for the new repository
        verbose: Whether to print detailed information
        
    Returns:
        The new branch object
    """
    # Initialize client
    client = SedaroApiClient(api_key=api_key)
    
    # Load template data
    if verbose:
        print(f"Loading template data from branch: {template_branch_id}")
    
    agent_template_branch = client.agent_template(template_branch_id)
    template_data = agent_template_branch.data
    blocks = template_data.get('blocks', {})
    
    if verbose:
        print(f"Total blocks in template: {len(blocks)}")
    
    # Identify duplicates
    duplicate_groups, unique_block_ids = identify_duplicates(blocks)
    
    if verbose:
        print(f"Unique blocks to keep: {len(unique_block_ids)}")
        print(f"Duplicate groups found: {len(duplicate_groups)}")
    
    # Create deduplicated schema
    deduplicated_blocks = create_deduplicated_schema(blocks, unique_block_ids)
    
    # Analyze dependencies
    references_to_fix = analyze_dependencies(blocks, duplicate_groups)
    
    if verbose and references_to_fix:
        print(f"Found {len(references_to_fix)} removed blocks that are referenced by other blocks")
        for removed_id, references in references_to_fix.items():
            print(f"  Block {removed_id} is referenced by {len(references)} other blocks")
    
    # Create new repository
    if verbose:
        print(f"Creating new repository: {new_repo_name}")
    
    repo = client.Repository.create(
        name=new_repo_name,
        metamodelType="Spacecraft",
        workspace=workspace_id,
    )
    
    # Get the new branch
    new_branch_id = repo.branches[0].id
    new_branch = client.agent_template(new_branch_id)
    
    # Get existing blocks in new branch
    branch_data = new_branch.data
    existing_blocks = branch_data.get("blocks", {}) if isinstance(branch_data, dict) else {}
    existing_by_type_name = {
        (blk["type"], blk.get("name")): bid
        for bid, blk in existing_blocks.items()
    }
    
    # Build reference mapping
    ref_map = {}
    for old_id, blk in deduplicated_blocks.items():
        key = (blk["type"], blk.get("name"))
        if key in existing_by_type_name:
            # Reuse existing default block
            ref_map[old_id] = existing_by_type_name[key]
        else:
            # Create new block
            ref_map[old_id] = f"${old_id}"
    
    # Fix references to removed duplicate blocks (first and middle entries in each group)
    for (block_type, block_name), block_ids in duplicate_groups.items():
        if len(block_ids) > 1:
            # Map the first and middle (removed) entries to the last (kept) entry
            last_id = block_ids[-1]
            for removed_id in block_ids[:-1]:  # All except the last
                if last_id in ref_map:
                    ref_map[removed_id] = ref_map[last_id]
    
    # Build payload for new blocks
    payload = []
    for old_id, blk in deduplicated_blocks.items():
        ref_id = ref_map[old_id]
        if not isinstance(ref_id, str) or not ref_id.startswith("$"):
            # We're reusing an existing block → skip creation
            continue
        
        # Build new block entry
        b = {"id": ref_id, "type": blk["type"]}
        for k, v in blk.items():
            if k in ("id", "type"):
                continue
            
            # Remap any string or list of strings that point at other old_ids
            if isinstance(v, str) and v in ref_map:
                b[k] = ref_map[v]
            elif (
                isinstance(v, list)
                and all(isinstance(x, str) and x in ref_map for x in v)
            ):
                b[k] = [ref_map[x] for x in v]
            else:
                b[k] = v
        
        payload.append(b)
    
    # Create blocks in new branch
    if payload:
        if verbose:
            print(f"Creating {len(payload)} new blocks...")
        
        resp = new_branch.update(
            blocks=payload,
            include_response=True
        )
        
        if verbose:
            print("✅ Created/updated:", resp["crud"]["blocks"])
    else:
        if verbose:
            print("No new blocks to create (all were defaults)")
    
    return new_branch


def main():
    """Main function to run the deduplication process."""
    print("=== Agent Template Deduplication Script ===")
    print()
    
    # Create new model with deduplication
    new_branch = create_new_model_with_deduplication(
        api_key=API_KEY,
        workspace_id=WORKSPACE_ID,
        template_branch_id=TEMP_AGENT_REPO_BRANCH_ID,
        new_repo_name="Deduplicated_Agent_Model",
        verbose=True
    )
    
    print()
    print("=== Summary ===")
    print(f"New branch ID: {new_branch.id}")
    print("Deduplication complete!")


if __name__ == "__main__":
    main() 