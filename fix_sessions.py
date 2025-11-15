#!/usr/bin/env python3
"""
Script to add session context managers to sample_repository.py methods.
"""

import re

def add_session_wrapper(method_body: str, first_code_indent: int) -> str:
    """Add session wrapper and re-indent the body."""
    indent_str = ' ' * first_code_indent
    session_lines = [
        f"{indent_str}session_cm = await self.get_session()\n",
        f"{indent_str}async with session_cm as session:\n"
    ]
    
    # Re-indent all lines in method body
    reindented_lines = []
    for line in method_body.split('\n'):
        if line.strip():  # Non-empty line
            reindented_lines.append('    ' + line + '\n')
        else:
            reindented_lines.append('\n')
    
    return ''.join(session_lines) + ''.join(reindented_lines)

# Read file
with open('src/modules/fermentation/src/repository_component/repositories/sample_repository.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Methods that need fixing (already have session references but no wrapper)
methods_needing_fix = [
    'get_samples_in_timerange',
    'get_latest_sample',
    'get_fermentation_start_date',
    'get_latest_sample_by_type',
    'check_duplicate_timestamp',
    'soft_delete_sample'
]

# For each method, find it and add session wrapper
for method_name in methods_needing_fix:
    # Pattern to match the method
    pattern = rf'(    async def {method_name}\([^)]+\)[^:]*:.*?""".*?""")\n(        .*?)(\n    async def |\n    def |\Z)'
    
    def replacer(match):
        method_header_and_doc = match.group(1)
        method_body = match.group(2)
        next_section = match.group(3)
        
        # Add session wrapper
        wrapped_body = add_session_wrapper(method_body, 8)
        
        return method_header_and_doc + '\n' + wrapped_body + next_section
    
    content = re.sub(pattern, replacer, content, flags=re.DOTALL)

# Write back
with open('src/modules/fermentation/src/repository_component/repositories/sample_repository.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Fixed {len(methods_needing_fix)} methods")
