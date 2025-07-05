import json
import os
import shutil
import requests
from typing import List, Dict
from dataclasses import dataclass

# Reuse ADOClient from ADO_Fetch.py
from ADO_Fetch import ADOClient, download_dir, snapshot_dir

@dataclass
class WorkItemChange:
    id: int
    changes: Dict[str, any]  # Field path -> new value

def get_important_fields(data: dict) -> dict:
    """Extract only the fields we care about for change detection"""
    fields = data.get('fields', {})
    return {
        'System.Title': fields.get('System.Title'),
        'System.Description': fields.get('System.Description'),
        'Microsoft.VSTS.Common.AcceptanceCriteria': fields.get('Microsoft.VSTS.Common.AcceptanceCriteria'),
        'System.State': fields.get('System.State'),
        'Microsoft.VSTS.Common.Priority': fields.get('Microsoft.VSTS.Common.Priority'),
    }

def detect_changes() -> List[WorkItemChange]:
    """Compare current work items with snapshot to find changes"""
    changes = []
    
    # Process each file in the download directory
    for filename in os.listdir(download_dir):
        if not filename.endswith('.json'):
            continue
            
        current_path = os.path.join(download_dir, filename)
        snapshot_path = os.path.join(snapshot_dir, filename)
        
        # Read current file
        with open(current_path, 'r', encoding='utf-8') as f:
            current_data = json.load(f)
        
        # If file doesn't exist in snapshot, it's a new item
        if not os.path.exists(snapshot_path):
            changes.append(WorkItemChange(
                id=current_data['id'],
                changes=get_important_fields(current_data)
            ))
            continue
        
        # Read snapshot file
        with open(snapshot_path, 'r', encoding='utf-8') as f:
            snapshot_data = json.load(f)
        
        # Compare important fields
        current_fields = get_important_fields(current_data)
        snapshot_fields = get_important_fields(snapshot_data)
        
        field_changes = {}
        for field, value in current_fields.items():
            if value != snapshot_fields.get(field):
                field_changes[field] = value
        
        if field_changes:
            changes.append(WorkItemChange(
                id=current_data['id'],
                changes=field_changes
            ))
    
    return changes

def update_work_item(work_item_id: int, changes: Dict[str, any]) -> bool:
    """Update a work item in ADO with the given changes"""
    ado_client = ADOClient()
    headers = ado_client.get_headers('application/json-patch+json')
    url = f"https://dev.azure.com/{ado_client.organization}/{ado_client.project}/_apis/wit/workitems/{work_item_id}?api-version=7.0"
    
    # Convert changes to ADO patch format
    patch_doc = []
    for field, value in changes.items():
        patch_doc.append({
            "op": "add",
            "path": f"/fields/{field}",
            "value": value
        })
    
    try:
        response = requests.patch(url, headers=headers, json=patch_doc)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Error updating work item #{work_item_id}: {e}")
        return False

def main():
    print("Checking for work item changes...")
    
    # Detect changes
    changes = detect_changes()
    if not changes:
        print("No changes detected.")
        return
    
    # Show changes
    print(f"\nFound {len(changes)} work items with changes:")
    for change in changes:
        print(f"Work item #{change.id}:")
        for field, value in change.changes.items():
            print(f"  {field}:", end=" ")
            if value is None:
                print("None")
            else:
                print(value[:100] + "..." if len(str(value)) > 100 else value)
    
    # Prompt for update
    response = input("\nDo you want to update these items in ADO? (y/n):")
    if response.lower() != 'y':
        print("Update cancelled.")
        return
    
    # Update items
    success_count = 0
    for change in changes:
        print(f"Updating work item #{change.id}...")
        if update_work_item(change.id, change.changes):
            success_count += 1
    
    print(f"\nAll updates completed successfully!")
    
    # After successful update, refresh local copies
    print("Running ADO_Fetch.py to get latest changes...")
    import subprocess
    subprocess.run(['python', 'ADO_Fetch.py'])

if __name__ == "__main__":
    main()
