from PIL import Image, ImageDraw, ImageFont
import json
import os
from typing import Dict, List, Any, Tuple

class FormImageGenerator:
    def __init__(self, original_image_path: str):
        """
        Initialize the form image generator with the original form image.
        
        Args:
            original_image_path (str): Path to the original form image
        """
        self.original_image_path = original_image_path
        self.original_image = Image.open(original_image_path)
        self.draw = ImageDraw.Draw(self.original_image)
        
        # Try to load a font, fall back to default if not available
        try:
            # Try to use a system font
            self.font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
        except:
            try:
                # Fallback to a different system font
                self.font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
            except:
                # Use default font if system fonts aren't available
                self.font = ImageFont.load_default()
    
    def estimate_field_position(self, field: Dict[str, Any], image_width: int, image_height: int) -> tuple:
        """
        Estimate the position for a field based on its label and type.
        This is a simple heuristic - in a real implementation, you'd want to use
        the actual coordinates from Azure's analysis.
        
        Args:
            field (Dict): Field information from the schema
            image_width (int): Width of the image
            image_height (int): Height of the image
            
        Returns:
            tuple: (x, y) coordinates for the field
        """
        label = field.get('label', '').lower()
        field_type = field.get('type', '').lower()
        
        # Simple positioning logic based on common form field names
        if 'name' in label:
            return (image_width * 0.3, image_height * 0.15)
        elif 'address' in label:
            return (image_width * 0.3, image_height * 0.25)
        elif 'city' in label:
            return (image_width * 0.3, image_height * 0.35)
        elif 'state' in label:
            return (image_width * 0.3, image_height * 0.45)
        elif 'zip' in label or 'postal' in label:
            return (image_width * 0.3, image_height * 0.55)
        elif 'ssn' in label or 'social' in label:
            return (image_width * 0.3, image_height * 0.65)
        elif 'ein' in label or 'employer' in label:
            return (image_width * 0.3, image_height * 0.75)
        else:
            # Default position for unknown fields
            return (image_width * 0.3, image_height * 0.85)
    
    def find_best_coordinate_match(self, field: Dict[str, Any], field_coordinates: Dict[str, Tuple[float, float]]) -> Tuple[float, float]:
        """
        Find the best matching coordinate for a field based on label similarity.
        
        Args:
            field (Dict): Field information from the schema
            field_coordinates (Dict): Mapping of field labels to coordinates
            
        Returns:
            Tuple[float, float]: Best matching (x, y) coordinates
        """
        field_label = field.get('label', '').lower()
        
        # Try exact matches first
        for coord_label, coords in field_coordinates.items():
            if coord_label.lower() == field_label:
                return coords
        
        # Try partial matches
        for coord_label, coords in field_coordinates.items():
            coord_label_lower = coord_label.lower()
            
            # Check if field label contains coordinate label or vice versa
            if (coord_label_lower in field_label or 
                field_label in coord_label_lower or
                any(word in coord_label_lower for word in field_label.split()) or
                any(word in field_label for word in coord_label_lower.split())):
                return coords
        
        # Try semantic matching for common field types
        semantic_matches = {
            'name': ['name', 'legal', 'business'],
            'address': ['address', 'street'],
            'city': ['city', 'town'],
            'state': ['state', 'province'],
            'zip': ['zip', 'postal'],
            'ssn': ['ssn', 'social', 'security'],
            'ein': ['ein', 'employer', 'identification']
        }
        
        for semantic_type, keywords in semantic_matches.items():
            if any(keyword in field_label for keyword in keywords):
                for coord_label, coords in field_coordinates.items():
                    if any(keyword in coord_label.lower() for keyword in keywords):
                        return coords
        
        return None
    
    def generate_filled_image(self, filled_schema: Dict[str, Any], output_path: str = None) -> str:
        """
        Generate a filled form image by overlaying the filled values on the original image.
        
        Args:
            filled_schema (Dict): The filled form schema with values
            output_path (str): Path to save the output image. If None, generates a default name.
            
        Returns:
            str: Path to the generated filled image
        """
        if output_path is None:
            # Generate default output path
            base_name = os.path.splitext(os.path.basename(self.original_image_path))[0]
            output_path = f"filled_{base_name}.jpg"
        
        # Get image dimensions
        image_width, image_height = self.original_image.size
        
        # Process fields and overlay text
        fields = filled_schema.get('fields', [])
        if not fields and 'sections' in filled_schema:
            for section in filled_schema['sections']:
                fields.extend(section.get('fields', []))
        
        # Overlay each filled field
        for field in fields:
            if field.get('value') and field.get('value').strip():
                # Get field position
                x, y = self.estimate_field_position(field, image_width, image_height)
                
                # Get the value to display
                value = field['value']
                
                # Draw the text
                self.draw.text((x, y), value, fill='black', font=self.font)
                
                # Draw a small box around the text for visibility
                bbox = self.draw.textbbox((x, y), value, font=self.font)
                self.draw.rectangle(bbox, outline='blue', width=1)
        
        # Save the filled image
        self.original_image.save(output_path, 'JPEG', quality=95)
        
        return output_path
    
    def generate_filled_image_with_coordinates(self, filled_schema: Dict[str, Any], 
                                            field_coordinates: Dict[str, Tuple[float, float]], 
                                            output_path: str = None) -> str:
        """
        Generate a filled form image using provided field coordinates.
        This is more accurate than the heuristic positioning.
        
        Args:
            filled_schema (Dict): The filled form schema with values
            field_coordinates (Dict): Dictionary mapping field labels to (x, y) coordinates
            output_path (str): Path to save the output image
            
        Returns:
            str: Path to the generated filled image
        """
        if output_path is None:
            base_name = os.path.splitext(os.path.basename(self.original_image_path))[0]
            output_path = f"filled_{base_name}.jpg"
        
        # Get image dimensions
        image_width, image_height = self.original_image.size
        
        # Process fields and overlay text at specific coordinates
        fields = filled_schema.get('fields', [])
        if not fields and 'sections' in filled_schema:
            for section in filled_schema['sections']:
                fields.extend(section.get('fields', []))
        
        print(f"🎯 Processing {len(fields)} fields with precise coordinates...")
        
        for field in fields:
            if field.get('value') and field.get('value').strip():
                label = field.get('label', '')
                value = field['value']
                
                # Find coordinates for this field
                coordinates = self.find_best_coordinate_match(field, field_coordinates)
                
                if coordinates:
                    # Convert normalized coordinates to pixel coordinates
                    x = coordinates[0] * image_width
                    y = coordinates[1] * image_height
                    
                    print(f"  ✓ {label}: '{value}' at ({x:.1f}, {y:.1f})")
                    
                    # Draw the text at the specified coordinates
                    self.draw.text((x, y), value, fill='black', font=self.font)
                    
                    # Draw a box around the text
                    bbox = self.draw.textbbox((x, y), value, font=self.font)
                    self.draw.rectangle(bbox, outline='blue', width=1)
                else:
                    print(f"  ❌ {label}: No coordinates found, using estimated position")
                    # Fall back to estimated position
                    x, y = self.estimate_field_position(field, image_width, image_height)
                    self.draw.text((x, y), value, fill='red', font=self.font)  # Red for unmatched fields
        
        # Save the filled image
        self.original_image.save(output_path, 'JPEG', quality=95)
        
        return output_path
    
    def generate_filled_image_with_coordinate_file(self, filled_schema: Dict[str, Any], 
                                                coordinate_file: str = "field_coordinates.json",
                                                output_path: str = None) -> str:
        """
        Generate a filled form image using coordinates from a saved file.
        
        Args:
            filled_schema (Dict): The filled form schema with values
            coordinate_file (str): Path to the JSON file containing field coordinates
            output_path (str): Path to save the output image
            
        Returns:
            str: Path to the generated filled image
        """
        if not os.path.exists(coordinate_file):
            print(f"⚠️  Coordinate file not found: {coordinate_file}")
            print("Falling back to estimated positioning...")
            return self.generate_filled_image(filled_schema, output_path)
        
        try:
            with open(coordinate_file, 'r') as f:
                field_coordinates = json.load(f)
            
            print(f"📐 Loaded {len(field_coordinates)} field coordinates from {coordinate_file}")
            return self.generate_filled_image_with_coordinates(filled_schema, field_coordinates, output_path)
            
        except Exception as e:
            print(f"❌ Error loading coordinates: {str(e)}")
            print("Falling back to estimated positioning...")
            return self.generate_filled_image(filled_schema, output_path)

def main():
    """
    Example usage of the FormImageGenerator
    """
    # Example filled schema (you would get this from your interview.py)
    example_schema = {
        "fields": [
            {
                "label": "Full Name",
                "type": "text",
                "required": True,
                "value": "John Doe"
            },
            {
                "label": "Address",
                "type": "text", 
                "required": True,
                "value": "123 Main Street"
            },
            {
                "label": "City",
                "type": "text",
                "required": True,
                "value": "Anytown"
            }
        ]
    }
    
    # Initialize generator with your form image
    image_path = "sample_data/input_form.jpeg"  # Update this path
    
    if os.path.exists(image_path):
        generator = FormImageGenerator(image_path)
        
        # Generate filled image
        output_path = generator.generate_filled_image(example_schema)
        print(f"Generated filled form image: {output_path}")
    else:
        print(f"Image not found at: {image_path}")
        print("Please update the image_path variable to point to your form image.")

if __name__ == "__main__":
    main() 