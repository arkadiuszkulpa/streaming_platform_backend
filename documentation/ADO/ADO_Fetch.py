import boto3
import requests
import json
import base64
import os
import shutil
from datetime import datetime

class ADOClient:
    def __init__(self):
        self._pat = None
        self._headers = None
        self.organization = "myai4"
        self.project = "myai4"
    
    def get_headers(self, content_type='application/json'):
        """Get authenticated headers for ADO API calls, using cached PAT"""
        if self._headers is None:
            pat = self._get_pat()
            pat = pat.strip()
            if ':' in pat:
                auth_token = base64.b64encode(pat.encode('utf-8')).decode('utf-8')
            else:
                auth_token = base64.b64encode(f":{pat}".encode('utf-8')).decode('utf-8')
            
            self._headers = {
                'Authorization': f'Basic {auth_token}',
                'Accept': 'application/json',
                'X-TFS-FedAuthRedirect': 'Suppress'
            }
        
        return {**self._headers, 'Content-Type': content_type}
    
    def _get_pat(self):
        """Get PAT from cache or AWS"""
        if self._pat is None:
            print("Initializing AWS session...")
            session = boto3.session.Session()
            client = session.client(
                service_name='secretsmanager',
                region_name='eu-west-2'
            )
            
            try:
                print("Fetching secret from AWS...")
                response = client.get_secret_value(
                    SecretId="WorkItemFetcher"
                )
                secret_dict = json.loads(response['SecretString'])
                self._pat = secret_dict['WorkItemFetcher']
                print(f"Secret retrieved successfully (length: {len(self._pat)} characters)")
            except Exception as e:
                print(f"Error fetching secret: {e}")
                raise
        
        return self._pat

# Create a global instance
ado_client = ADOClient()

# ADO setup
organization = "myai4"
project = "myai4"
base_url = f"https://dev.azure.com/{organization}/{project}"

# Set up directories
script_dir = os.path.dirname(os.path.abspath(__file__))
download_dir = os.path.join(script_dir, "work_items", "download")
snapshot_dir = os.path.join(script_dir, "work_items", ".snapshot")

def execute_wiql_query(query):
    """Execute a WIQL query and return work item IDs"""
    headers = ado_client.get_headers('application/json')
    url = f"{base_url}/_apis/wit/wiql?api-version=7.0"
    
    try:
        response = requests.post(url, headers=headers, json={'query': query})
        response.raise_for_status()
        work_items = response.json().get('workItems', [])
        return [item['id'] for item in work_items]
    except requests.exceptions.RequestException as e:
        print(f"Error executing WIQL query: {e}")
        raise

def get_all_work_items():
    """Get all work items ordered by ID"""
    query = """
    SELECT [System.Id]
    FROM WorkItems 
    ORDER BY [System.Id]
    """
    return execute_wiql_query(query)

def fetch_work_item(work_item_id):
    """Fetch a single work item from ADO"""
    headers = ado_client.get_headers('application/json-patch+json')
    url = f"{base_url}/_apis/wit/workitems/{work_item_id}?$expand=all&api-version=7.0"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching work item #{work_item_id}: {e}")
        raise

def save_work_item(work_item_data):
    """Save work item data to the download directory"""
    work_id = work_item_data['id']
    work_type = work_item_data['fields']['System.WorkItemType'].replace(' ', '_')
    title = work_item_data['fields']['System.Title']
    title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
    title = title.replace(' ', '_')[:50]
    
    filename = f"{work_type}_{work_id}_{title}.json"
    filepath = os.path.join(download_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(work_item_data, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {filename}")
    return filepath

def main():
    print("Starting ADO work item export...")
    
    # Clean and create directories
    if os.path.exists(download_dir):
        shutil.rmtree(download_dir)
    os.makedirs(download_dir)
    
    # Get and process all work items
    work_item_ids = get_all_work_items()
    print(f"Found {len(work_item_ids)} work items")
    
    processed_count = 0
    for work_id in work_item_ids:
        print(f"Processing work item #{work_id}...")
        work_item_data = fetch_work_item(work_id)
        save_work_item(work_item_data)
        processed_count += 1
    
    # Create snapshot by copying download directory
    if os.path.exists(snapshot_dir):
        shutil.rmtree(snapshot_dir)
    shutil.copytree(download_dir, snapshot_dir)
    
    print(f"\nExport completed successfully!")
    print(f"Processed {processed_count} work items")
    print(f"Files saved to {download_dir}")
    print(f"Snapshot created in {snapshot_dir}")
    
    # Generate documentation
    print("\nGenerating documentation...")
    import generate_documentation
    generate_documentation.generate_documentation()

if __name__ == "__main__":
    main()
