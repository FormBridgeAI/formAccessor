#!/usr/bin/env python3
"""
Debug script to check coordinate matching issues
"""

import json
import os

def debug_coordinate_matching():
    """Debug the coordinate matching between schema and coordinates file"""
    
    # Load the coordinates file (check both current dir and server dir)
    coords_file = "field_coordinates.json"
    if not os.path.exists(coords_file):
        coords_file = "server/field_coordinates.json"
    
    if os.path.exists(coords_file):
        with open(coords_file, 'r') as f:
            coordinates = json.load(f)
        print("✅ Loaded coordinates file:")
        for field, coords in coordinates.items():
            print(f"  • {field}: ({coords[0]:.3f}, {coords[1]:.3f})")
    else:
        print("❌ No coordinates file found")
        return
    
    # Check if there's a completed schema file
    schema_file = "completed_schema.json"
    if not os.path.exists(schema_file):
        schema_file = "server/completed_schema.json"
    
    if os.path.exists(schema_file):
        with open(schema_file, 'r') as f:
            schema = json.load(f)
        
        print(f"\n📋 Schema fields:")
        fields = schema.get('fields', [])
        if not fields and 'sections' in schema:
            for section in schema['sections']:
                fields.extend(section.get('fields', []))
        
        for field in fields:
            label = field.get('label', 'Unknown')
            value = field.get('value', '')
            print(f"  • {label}: '{value}'")
            
            # Try to find matching coordinates
            found_coords = None
            matched_key = None
            for coord_key, coord_value in coordinates.items():
                if coord_key.lower() == label.lower() or coord_key.lower() in label.lower() or label.lower() in coord_key.lower():
                    found_coords = coord_value
                    matched_key = coord_key
                    break
            
            if found_coords:
                print(f"    ✅ Matched with coordinates: {matched_key} -> ({found_coords[0]:.3f}, {found_coords[1]:.3f})")
            else:
                print(f"    ❌ No coordinate match found")
    else:
        print("❌ No completed schema file found")
    
    print(f"\n🔍 Coordinate matching analysis:")
    print("The issue might be:")
    print("1. Field names don't match exactly between schema and coordinates")
    print("2. Case sensitivity in matching")
    print("3. Different label formats")
    print("\nTo fix this, ensure the coordinate keys match the schema field labels exactly")

if __name__ == "__main__":
    debug_coordinate_matching() 