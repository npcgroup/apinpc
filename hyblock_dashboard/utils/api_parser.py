import json
import os
import sys
from pathlib import Path

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database import get_logger

# Set up logger
logger = get_logger("api_parser")

def load_api_spec(file_path):
    """Load the Hyblock API specification from the given file path"""
    try:
        with open(file_path, 'r') as f:
            api_spec = json.load(f)
        return api_spec
    except Exception as e:
        logger.error(f"Error loading API spec: {e}")
        return None

def extract_endpoints(api_spec):
    """Extract all endpoints from the API specification"""
    if not api_spec or 'paths' not in api_spec:
        logger.error("Invalid API specification")
        return {}
    
    endpoints = {}
    
    for path, methods in api_spec['paths'].items():
        endpoint_name = path.strip('/')
        if not endpoint_name:
            continue
        
        # Get the GET method details if available
        if 'get' in methods:
            method_details = methods['get']
            
            # Extract description
            description = method_details.get('description', '')
            
            # Extract parameters
            parameters = []
            for param in method_details.get('parameters', []):
                parameters.append({
                    'name': param.get('name', ''),
                    'in': param.get('in', ''),
                    'type': param.get('type', ''),
                    'description': param.get('description', ''),
                    'required': param.get('required', False)
                })
            
            endpoints[endpoint_name] = {
                'path': path,
                'description': description,
                'parameters': parameters
            }
    
    return endpoints

def get_required_params(endpoint_info):
    """Get the required parameters for an endpoint"""
    required_params = []
    
    for param in endpoint_info.get('parameters', []):
        if param.get('required', False):
            required_params.append(param.get('name', ''))
    
    return required_params

def get_all_endpoints():
    """Get all endpoints from the API specification"""
    # Get the path to the API spec file
    api_spec_path = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / 'endpoints_hyblock.json'
    
    # Load the API spec
    api_spec = load_api_spec(api_spec_path)
    if not api_spec:
        return {}
    
    # Extract endpoints
    endpoints = extract_endpoints(api_spec)
    
    return endpoints

if __name__ == "__main__":
    # Test the API parser
    endpoints = get_all_endpoints()
    print(f"Found {len(endpoints)} endpoints")
    
    # Print the first 5 endpoints
    for i, (name, info) in enumerate(endpoints.items()):
        if i >= 5:
            break
        
        print(f"\nEndpoint: {name}")
        print(f"Description: {info['description']}")
        print("Required parameters:")
        for param in info.get('parameters', []):
            if param.get('required', False):
                print(f"  - {param.get('name', '')}: {param.get('description', '')}") 