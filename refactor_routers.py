"""
Script to refactor router files - Add error handler decorator and remove try/except blocks
"""

import re
import sys
from pathlib import Path


def refactor_router_file(file_path: Path) -> None:
    """
    Refactor a router file to use the error handler decorator.
    
    1. Add import for handle_service_errors
    2. Add decorator to each async def function
    3. Remove try/except blocks
    """
    print(f"Processing {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Check if import already exists
    if 'from src.modules.fermentation.src.api.error_handlers import handle_service_errors' not in content:
        # Find the last import line from src.modules
        last_import_match = None
        for match in re.finditer(r'^from src\.modules\.fermentation\.src\..+$', content, re.MULTILINE):
            last_import_match = match
        
        if last_import_match:
            insert_pos = last_import_match.end()
            content = (content[:insert_pos] + 
                      '\nfrom src.modules.fermentation.src.api.error_handlers import handle_service_errors' + 
                      content[insert_pos:])
            print("✅ Added import for handle_service_errors")
    
    # Pattern to find async def functions (router endpoints)
    # Match from @router decorator to the end of the function
    endpoint_pattern = re.compile(
        r'(@router\.(get|post|patch|put|delete)\([^)]+?\)(?:\s*\n[^)]*?\))?)\s*\n'  # Router decorator
        r'(async def \w+\([^)]+\)(?:\s*->\s*[^:]+)?:)\s*\n'  # Function signature
        r'((?:    """[\s\S]*?"""\s*\n)?)'  # Optional docstring
        r'((?:    .*\n)*?)'  # Function body
        r'(?=\n\n@router|\n\n# |$)',  # Stop at next endpoint or end
        re.MULTILINE
    )
    
    def add_decorator_if_missing(match):
        """Add @handle_service_errors decorator if not present"""
        decorator = match.group(1)
        func_sig = match.group(3)
        docstring = match.group(4)
        body = match.group(5)
        
        # Check if decorator already present
        if '@handle_service_errors' in decorator:
            return match.group(0)  # Already has decorator
        
        # Add decorator between router decorator and function
        result = f"{decorator}\n@handle_service_errors\n{func_sig}\n{docstring}{body}"
        return result
    
    content = endpoint_pattern.sub(add_decorator_if_missing, content)
    
    # Now remove try/except blocks
    # Pattern to match entire try/except blocks
    try_except_pattern = re.compile(
        r'(    )try:\s*\n'  # Capture indentation
        r'((?:        .*\n)+?)'  # try block content (indented 8 spaces)
        r'(?:    except HTTPException:\s*\n'  # except HTTPException
        r'(?:        .*\n)*?'
        r')?'
        r'(?:    except [^:]+:\s*\n'  # Other except blocks
        r'(?:        .*\n)*?'
        r')*'
        r'(?:    except Exception as [^:]+:\s*\n'  # Generic except
        r'(?:        .*\n)*?'
        r')?',
        re.MULTILINE
    )
    
    def unwrap_try_block(match):
        """Remove try/except wrapper, keep only the try block content"""
        indent = match.group(1)
        try_body = match.group(2)
        
        # Dedent the try body by 4 spaces (from 8 to 4)
        dedented = '\n'.join(
            line[4:] if line.startswith('        ') else line
            for line in try_body.split('\n')
        )
        
        return dedented
    
    content = try_except_pattern.sub(unwrap_try_block, content)
    
    # Write back
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Refactored {file_path}")
        return True
    else:
        print(f"ℹ️  No changes needed for {file_path}")
        return False


if __name__ == '__main__':
    # Get file path from command line or use default
    if len(sys.argv) > 1:
        file_path = Path(sys.argv[1])
    else:
        # Default to fermentation_router.py
        file_path = Path(r'c:\dev\wine-fermentation-system\src\modules\fermentation\src\api\routers\fermentation_router.py')
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        sys.exit(1)
    
    try:
        changed = refactor_router_file(file_path)
        print("\n✅ Refactoring complete!")
        sys.exit(0 if changed else 0)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
