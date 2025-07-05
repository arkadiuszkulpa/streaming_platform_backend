import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass

# Reuse directory paths from ADO_Fetch
from ADO_Fetch import download_dir

@dataclass
class WorkItem:
    id: int
    type: str
    title: str
    description: str
    acceptance_criteria: str
    parent_id: Optional[int]
    children: List['WorkItem']

def load_work_items() -> Dict[int, WorkItem]:
    """Load all work items from the download directory"""
    items = {}
    
    for filename in os.listdir(download_dir):
        if not filename.endswith('.json'):
            continue
            
        filepath = os.path.join(download_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        fields = data.get('fields', {})
        item = WorkItem(
            id=data['id'],
            type=fields.get('System.WorkItemType', ''),
            title=fields.get('System.Title', ''),
            description=fields.get('System.Description', '') or '',
            acceptance_criteria=fields.get('Microsoft.VSTS.Common.AcceptanceCriteria', '') or '',
            parent_id=fields.get('System.Parent'),
            children=[]
        )
        items[item.id] = item
    
    return items

def build_hierarchy(items: Dict[int, WorkItem]) -> List[WorkItem]:
    """Build parent-child hierarchy from flat work items"""
    roots = []
    
    # First pass: populate children lists
    for item in items.values():
        if item.parent_id:
            if parent := items.get(item.parent_id):
                parent.children.append(item)
        else:
            roots.append(item)
    
    # Sort roots by ID
    roots.sort(key=lambda x: x.id)
    
    # Sort children by type and ID
    type_order = {'Feature': 1, 'User Story': 2, 'Task': 3}
    for item in items.values():
        item.children.sort(key=lambda x: (type_order.get(x.type, 99), x.id))
    
    return roots

def clean_html(text: str) -> str:
    """Remove HTML tags, entities, and normalize whitespace"""
    if not text:
        return ""
    
    # Remove HTML tags with attributes
    import re
    text = re.sub(r'<[^>]+>', '', text)
    
    # Convert common HTML entities
    entities = {
        '&nbsp;': ' ',
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&quot;': '"',
        '&#39;': "'",
    }
    for entity, char in entities.items():
        text = text.replace(entity, char)
    
    # Convert other numeric entities
    text = re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))), text)
    
    # Fix newlines and whitespace
    # First split by double newlines to preserve paragraphs
    paragraphs = text.split('\n\n')
    cleaned_paragraphs = []
    for para in paragraphs:
        # Then clean up each paragraph
        lines = [line.strip() for line in para.splitlines()]
        lines = [line for line in lines if line]
        if lines:
            cleaned_paragraphs.append(' '.join(lines))
    return '\n\n'.join(cleaned_paragraphs)

def clean_markdown_headers(text: str) -> str:
    """Clean up markdown headers and format documentation sections"""
    if not text:
        return ""
    
    import re
    
    # First pass: convert documentation-style sections to regular text
    lines = []
    for line in text.splitlines():
        # Strip excess whitespace
        line = line.strip()
        if not line:
            continue
            
        # Convert heading markers to section titles
        if re.match(r'^#{1,6}\s+', line):
            # Remove # markers and make bold
            clean_line = re.sub(r'^#{1,6}\s+', '', line)
            lines.append(f"**Section: {clean_line}**")
        # Convert horizontal rules to separators
        elif line == '---':
            lines.append("---")
        # Handle bullet points
        elif line.startswith('- '):
            lines.append(line)
        # Regular text
        else:
            lines.append(line)
    
    # Join lines back together
    return '\n'.join(lines)

def format_section_content(content: str, indent: str) -> list[str]:
    """Format a section of content with proper indentation and markdown cleanup"""
    if not content:
        return []
    
    content = clean_markdown_headers(content)
    lines = []
    
    # Split into paragraphs
    paragraphs = content.split('\n\n')
    for para in paragraphs:
        # Clean up the paragraph
        para = para.strip()
        if not para:
            continue
        
        # Handle bullet points
        if para.startswith('- ') or para.startswith('* '):
            for line in para.splitlines():
                lines.append(f"{indent}{line}")
            lines.append("")  # Empty line after bullet points
        else:
            # Wrap non-bullet text in blockquote
            para_lines = para.splitlines()
            for line in para_lines:
                line = line.strip()
                if line:
                    lines.append(f"{indent}> {line}")
            lines.append("")  # Empty line after paragraph
    
    return lines

def format_work_item(item: WorkItem, level: int = 0) -> str:
    """Format a work item and its children as markdown"""
    indent = "  " * level
    md = []
    
    # Header
    md.append(f"{indent}{'#' * (level + 1)} {item.title}")
    md.append(f"{indent}*{item.type} #{item.id}*")
    md.append("")  # Empty line after header
    
    # Description
    if desc := clean_html(item.description):
        md.extend(format_section_content(desc, indent))
    
    # Acceptance Criteria
    if ac := clean_html(item.acceptance_criteria):
        md.append(f"{indent}**Acceptance Criteria:**")
        formatted_criteria = []
        # Split criteria into scenarios
        for scenario in ac.split('\n\n'):
            lines = [line.strip() for line in scenario.splitlines() if line.strip()]
            if lines:
                # Format as a proper bulleted list with continuation indentation
                formatted_criteria.append(f"{indent}- {lines[0]}")
                for line in lines[1:]:
                    formatted_criteria.append(f"{indent}  {line}")
        md.extend(formatted_criteria)
        md.append("")  # Empty line after criteria
    
    # Children
    for child in item.children:
        md.append(format_work_item(child, level + 1))
    
    return '\n'.join(md)

def generate_documentation():
    """Generate markdown documentation from work items"""
    output_path = os.path.join(os.path.dirname(download_dir), "Requirements.md")
    
    print("Loading work items...")
    items = load_work_items()
    
    print("Building hierarchy...")
    roots = build_hierarchy(items)
    
    print("Generating documentation...")
    doc = [
        "# Project Requirements",
        "Generated from Azure DevOps work items",
        ""  # Empty line after header
    ]
    
    for root in roots:
        doc.append(format_work_item(root))
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(doc))  # Changed from \\n to \n
    
    print(f"Documentation saved to {output_path}")

if __name__ == "__main__":
    generate_documentation()
