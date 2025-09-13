from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from openai import OpenAI
import json
import os
from typing import Dict, List, Tuple, Any
from dotenv import load_dotenv

load_dotenv("../.env")

class CoordinateExtractor:
    """
    Extracts field coordinates from Azure Document Intelligence analysis results
    and uses OpenAI to intelligently map field positions for precise positioning.
    """
    
    def __init__(self, endpoint: str, key: str):
        """
        Initialize the coordinate extractor with Azure credentials.
        
        Args:
            endpoint (str): Azure Document Intelligence endpoint
            key (str): Azure Document Intelligence key
        """
        self.client = DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(key))
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    def analyze_document(self, file_path: str):
        """
        Analyze a document using Azure Document Intelligence.
        
        Args:
            file_path (str): Path to the document image
            
        Returns:
            dict: Raw analysis result
        """
        with open(file_path, "rb") as f:
            poller = self.client.begin_analyze_document(
                model_id="prebuilt-layout",
                body=f,
                content_type="image/jpeg"
            )
        result = poller.result()
        return result.as_dict()
    
    def extract_field_coordinates_with_openai(self, analysis_result: dict) -> Dict[str, Tuple[float, float]]:
        """
        Use OpenAI to intelligently map field positions based on Azure analysis.
        
        Args:
            analysis_result (dict): Raw Azure analysis result
            
        Returns:
            Dict[str, Tuple[float, float]]: Mapping of field labels to (x, y) coordinates
        """
        # Get page dimensions
        pages = analysis_result.get('pages', [])
        if not pages:
            return {}
        
        page = pages[0]  # Assuming single page form
        page_width = page.get('width', 1)
        page_height = page.get('height', 1)
        
        # Extract all text elements with their positions
        text_elements = []
        
        # Collect paragraphs
        paragraphs = analysis_result.get('paragraphs', [])
        for paragraph in paragraphs:
            content = paragraph.get('content', '').strip()
            if content:
                bounding_regions = paragraph.get('boundingRegions', [])
                if bounding_regions:
                    region = bounding_regions[0]
                    polygon = region.get('polygon', [])
                    if len(polygon) >= 4:
                        x_coords = [polygon[i] for i in range(0, len(polygon), 2)]
                        y_coords = [polygon[i + 1] for i in range(0, len(polygon), 2)]
                        center_x = sum(x_coords) / len(x_coords)
                        center_y = sum(y_coords) / len(y_coords)
                        
                        text_elements.append({
                            'text': content,
                            'x': center_x,
                            'y': center_y,
                            'width': max(x_coords) - min(x_coords),
                            'height': max(y_coords) - min(y_coords)
                        })
        
        # Collect lines
        lines = page.get('lines', [])
        for line in lines:
            content = line.get('content', '').strip()
            if content:
                polygon = line.get('polygon', [])
                if len(polygon) >= 4:
                    x_coords = [polygon[i] for i in range(0, len(polygon), 2)]
                    y_coords = [polygon[i + 1] for i in range(0, len(polygon), 2)]
                    center_x = sum(x_coords) / len(x_coords)
                    center_y = sum(y_coords) / len(y_coords)
                    
                    text_elements.append({
                        'text': content,
                        'x': center_x,
                        'y': center_y,
                        'width': max(x_coords) - min(x_coords),
                        'height': max(y_coords) - min(y_coords)
                    })
        
        # Use OpenAI to intelligently map field positions
        return self._openai_field_mapping(text_elements, page_width, page_height)
    
    def _openai_field_mapping(self, text_elements: List[Dict], page_width: float, page_height: float) -> Dict[str, Tuple[float, float]]:
        """
        Use OpenAI to intelligently map field labels to input positions.
        
        Args:
            text_elements (List[Dict]): List of text elements with positions
            page_width (float): Page width
            page_height (float): Page height
            
        Returns:
            Dict[str, Tuple[float, float]]: Field mapping to coordinates
        """
        
        # Prepare text elements for OpenAI
        elements_text = []
        for elem in text_elements:
            elements_text.append(f"Text: '{elem['text']}' at ({elem['x']:.1f}, {elem['y']:.1f})")
        
        prompt = f"""
You are analyzing a form layout to determine where user input fields should be positioned.

Here are the text elements detected on the form with their coordinates:
{chr(10).join(elements_text)}

Page dimensions: {page_width:.1f} x {page_height:.1f}

Your task is to identify where each form field input should be positioned. For each field label (like "Phone:", "Job Title:", "Email:", etc.), determine the (x, y) coordinates where the user would type their answer.

Rules:
1. Input fields are usually to the right of or below the field label
2. Look for patterns like "Phone: _____" where the blank line is the input area
3. Consider typical form layouts and spacing
4. Return ONLY valid JSON with field names mapped to coordinates

Return a JSON object like:
{{
  "phone": [x, y],
  "job_title": [x, y],
  "email": [x, y],
  "name": [x, y],
  "address": [x, y],
  "city": [x, y],
  "state": [x, y],
  "zip_code": [x, y],
  "company_name": [x, y],
  "dates": [x, y],
  "reason_for_leaving": [x, y]
}}

Use the actual coordinates from the detected text elements and estimate input positions based on form layout patterns.
"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model='gpt-4-1106-preview',
                messages=[
                    {'role': 'system', 'content': 'You are a form layout analysis expert. Return only valid JSON.'},
                    {'role': 'user', 'content': prompt}
                ],
                max_tokens=1000,
                temperature=0
            )
            
            answer = response.choices[0].message.content.strip()
            
            # Clean up the response
            if answer.startswith("```json"):
                answer = answer[7:]
            if answer.endswith("```"):
                answer = answer[:-3]
            
            # Parse the JSON response
            field_coordinates = json.loads(answer)
            
            # Convert to normalized coordinates (0-1 range)
            normalized_coords = {}
            for field, coords in field_coordinates.items():
                if isinstance(coords, list) and len(coords) == 2:
                    x, y = coords[0], coords[1]
                    normalized_x = x / page_width
                    normalized_y = y / page_height
                    normalized_coords[field] = (normalized_x, normalized_y)
            
            return normalized_coords
            
        except Exception as e:
            print(f"❌ OpenAI coordinate mapping failed: {str(e)}")
            print("Falling back to basic coordinate extraction...")
            return self.extract_field_coordinates(analysis_result)
    
    def extract_field_coordinates(self, analysis_result: dict) -> Dict[str, Tuple[float, float]]:
        """
        Extract field coordinates from Azure analysis results (fallback method).
        
        Args:
            analysis_result (dict): Raw Azure analysis result
            
        Returns:
            Dict[str, Tuple[float, float]]: Mapping of field labels to (x, y) coordinates
        """
        field_coordinates = {}
        
        # Get page dimensions
        pages = analysis_result.get('pages', [])
        if not pages:
            return field_coordinates
        
        page = pages[0]  # Assuming single page form
        page_width = page.get('width', 1)
        page_height = page.get('height', 1)
        
        # Extract coordinates from paragraphs (form fields)
        paragraphs = analysis_result.get('paragraphs', [])
        
        for paragraph in paragraphs:
            content = paragraph.get('content', '').strip()
            if not content:
                continue
            
            # Get bounding region coordinates
            bounding_regions = paragraph.get('boundingRegions', [])
            if bounding_regions:
                region = bounding_regions[0]
                polygon = region.get('polygon', [])
                
                if len(polygon) >= 4:  # Need at least 2 points (x,y pairs)
                    # Calculate center point of the field
                    x_coords = [polygon[i] for i in range(0, len(polygon), 2)]
                    y_coords = [polygon[i + 1] for i in range(0, len(polygon), 2)]
                    
                    center_x = sum(x_coords) / len(x_coords)
                    center_y = sum(y_coords) / len(y_coords)
                    
                    # Normalize coordinates to 0-1 range
                    normalized_x = center_x / page_width
                    normalized_y = center_y / page_height
                    
                    # Map content to field labels
                    field_label = self._identify_field_label(content)
                    if field_label:
                        field_coordinates[field_label] = (normalized_x, normalized_y)
        
        # Also extract from lines for additional field detection
        lines = page.get('lines', [])
        for line in lines:
            content = line.get('content', '').strip()
            if not content:
                continue
            
            polygon = line.get('polygon', [])
            if len(polygon) >= 4:
                x_coords = [polygon[i] for i in range(0, len(polygon), 2)]
                y_coords = [polygon[i + 1] for i in range(0, len(polygon), 2)]
                
                center_x = sum(x_coords) / len(x_coords)
                center_y = sum(y_coords) / len(y_coords)
                
                normalized_x = center_x / page_width
                normalized_y = center_y / page_height
                
                field_label = self._identify_field_label(content)
                if field_label:
                    field_coordinates[field_label] = (normalized_x, normalized_y)
        
        return field_coordinates
    
    def _identify_field_label(self, content: str) -> str:
        """
        Identify what type of field this content represents.
        
        Args:
            content (str): Text content from Azure analysis
            
        Returns:
            str: Field label for coordinate mapping
        """
        content_lower = content.lower()
        
        # Common form field patterns
        field_patterns = {
            'name': ['name', 'legal name', 'business name'],
            'address': ['address', 'street address', 'business address'],
            'city': ['city', 'town'],
            'state': ['state', 'province'],
            'zip': ['zip', 'postal', 'zip code', 'postal code'],
            'ssn': ['ssn', 'social security', 'social security number'],
            'ein': ['ein', 'employer identification', 'employer id'],
            'business_name': ['business name', 'company name', 'employer name'],
            'account_number': ['account number', 'account #'],
            'date': ['date', 'signature date'],
            'signature': ['signature', 'sign here']
        }
        
        for field_type, patterns in field_patterns.items():
            for pattern in patterns:
                if pattern in content_lower:
                    return field_type
        
        return None
    
    def get_coordinate_mapping(self, file_path: str) -> Dict[str, Tuple[float, float]]:
        """
        Get coordinate mapping for a document using OpenAI-powered detection.
        
        Args:
            file_path (str): Path to the document image
            
        Returns:
            Dict[str, Tuple[float, float]]: Field label to coordinate mapping
        """
        print(f"🔍 Analyzing document: {file_path}")
        analysis_result = self.analyze_document(file_path)
        
        print("🤖 Using OpenAI to intelligently map field positions...")
        coordinates = self.extract_field_coordinates_with_openai(analysis_result)
        
        print(f"✅ Found {len(coordinates)} field coordinates:")
        for field, coords in coordinates.items():
            print(f"  • {field}: ({coords[0]:.3f}, {coords[1]:.3f})")
        
        return coordinates

def main():
    """
    Test the enhanced coordinate extraction system
    """
    # Azure credentials (from your existing code)
    endpoint = 'https://aiformfilling-doc-ai.cognitiveservices.azure.com/'
    key = 'CTVcKut0gFiwLBPWB5dvHfJg33Lf3OCnPLmwHl0HmmYnrT1mh0pdJQQJ99BGACYeBjFXJ3w3AAALACOGVNkh'
    
    # Initialize extractor
    extractor = CoordinateExtractor(endpoint, key)
    
    # Test with the form in sample_data folder starting with 427
    image_path = "/Users/asfawy/jsonTest/sample_data/simple-job-application-form-27d287c8e2b97cd3f175c12ef67426b2-classic.png"
    
    if os.path.exists(image_path):
        coordinates = extractor.get_coordinate_mapping(image_path)
        
        # Save coordinates for use in image generation
        output_file = "field_coordinates.json"
        with open(output_file, 'w') as f:
            json.dump(coordinates, f, indent=2)
        
        print(f"\n💾 Coordinates saved to: {output_file}")
        print("\n🎯 Use these coordinates with FormImageGenerator.generate_filled_image_with_coordinates()")
        
    else:
        print(f"❌ Image not found: {image_path}")

if __name__ == "__main__":
    main() 