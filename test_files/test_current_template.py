from sedaro import SedaroApiClient

API_KEY = "PKDqMrtcTK4plJgL7qVlQD.0xQph1lyKzd-pV0-ZL7bRIH7BX54Yjqbz6tluwut3Hvp8XE-RVbfHSz2o5vC77scUhg2xBFuBybplxY6FyXXMQ"
TEMPLATE_ID = "PS5ZPCp6mh5yXLH3lkCWFj"

print(f"Testing template ID: {TEMPLATE_ID}")

try:
    sedaro = SedaroApiClient(api_key=API_KEY)
    template = sedaro.agent_template(TEMPLATE_ID)
    data = template.data
    
    print("✅ Template connection successful!")
    print(f"Template ID: {TEMPLATE_ID}")
    print(f"Total keys: {len(data.keys())}")
    print("First 10 keys:", list(data.keys())[:10])
    
    # Check if it has blocks
    if 'blocks' in data:
        print(f"✅ Found {len(data['blocks'])} blocks")
        # Show first few block types
        block_types = set()
        for i, block in enumerate(data['blocks']):
            if i >= 10:  # Only check first 10 blocks
                break
            if isinstance(block, dict) and 'type' in block:
                block_types.add(block['type'])
        print(f"Block types found: {list(block_types)}")
    else:
        print("❌ No 'blocks' key found")
    
    # Check for mass property (common in spacecraft)
    if 'mass' in data:
        print(f"✅ Mass property found: {data['mass']}")
    else:
        print("❌ No mass property found")
        
    # Check for type property
    if 'type' in data:
        print(f"✅ Type property found: {data['type']}")
    else:
        print("❌ No type property found")
        
except Exception as e:
    print(f"❌ Template failed: {e}") 