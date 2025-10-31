# app/core/parsers/tree_sitter.py (Tree-sitter AST Parser for Precise Analysis)
import tree_sitter
from tree_sitter import Language, Parser
from tree_sitter_python import language as python_language  # For Python grammar
import os
from typing import Dict, List, Tuple, Any
import structlog

logger = structlog.get_logger()

class TreeSitterParser:
    """Tree-sitter parser for precise line numbers and code structure analysis"""
    
    def __init__(self):
        # Load languages (Python for now; extend for C++, Go, etc.)
        self.parsers = {}
        try:
            PY_LANGUAGE = Language(python_language(), 'python')
            self.parsers['python'] = Parser()
            self.parsers['python'].set_language(PY_LANGUAGE)
            logger.info("tree_sitter_initialized", languages=list(self.parsers.keys()))
        except Exception as e:
            logger.error("tree_sitter_init_failed", error=str(e))
            self.parsers = {}
    
    def parse_file_content(self, code: str, language: str = 'python') -> Dict[str, Any]:
        """
        Parse code content to extract:
        - Functions/classes with line ranges
        - Variables/assignments (e.g., for secrets)
        - Exact line numbers for nodes
        """
        if language not in self.parsers:
            logger.warning("unsupported_language_for_parsing", language=language)
            return {'functions': [], 'variables': [], 'lines': len(code.splitlines())}
        
        parser = self.parsers[language]
        tree = parser.parse(bytes(code, "utf8"))
        root_node = tree.root_node
        
        functions = []  # List of {'name': str, 'start_line': int, 'end_line': int, 'body': str}
        variables = []  # List of {'name': str, 'line': int, 'value': str} (e.g., assignments)
        
        def traverse(node, depth=0):
            if node.type == 'function_definition':
                # Function: name, params, body lines
                name_node = node.child_by_field_name('name')
                func_name = name_node.text.decode('utf8') if name_node else 'anonymous'
                start_line = node.start_point[0] + 1  # 1-based lines
                end_line = node.end_point[0] + 1
                functions.append({
                    'name': func_name,
                    'start_line': start_line,
                    'end_line': end_line,
                    'params': [c.text.decode('utf8') for c in node.children if c.type == 'parameters'],
                    'body_lines': (start_line, end_line)
                })
            
            elif node.type == 'assignment':
                # Variable assignment (e.g., api_key = "secret")
                left = node.child_by_field_name('left')
                right = node.child_by_field_name('right')
                if left and right:
                    var_name = left.text.decode('utf8')
                    var_value = right.text.decode('utf8')[:50] + '...' if len(right.text) > 50 else right.text.decode('utf8')
                    var_line = node.start_point[0] + 1
                    if 'secret' in var_value.lower() or '"' in var_value:  # Heuristic for hardcoded
                        variables.append({
                            'name': var_name,
                            'line': var_line,
                            'value': var_value,
                            'type': 'potential_secret' if 'secret' in var_value.lower() else 'assignment'
                        })
            
            # Recurse on children
            for child in node.children:
                traverse(child)
        
        traverse(root_node)
        
        logger.info("ast_parsing_complete", functions_count=len(functions), variables_count=len(variables))
        return {
            'tree': tree,
            'root_node': root_node,
            'functions': functions,
            'variables': variables,
            'total_lines': root_node.end_point[0] + 1
        }
    
    def get_exact_line_for_issue(self, code: str, issue_type: str, approx_line: int) -> int:
        """Map approximate issue line to exact via AST (e.g., find SQL query node)"""
        # Simplified: For SQLi, search for string concat in queries around approx_line
        lines = code.splitlines()
        if approx_line > len(lines):
            return approx_line
        
        # Heuristic: Look ±3 lines for 'SELECT' or concat
        start = max(0, approx_line - 3)
        end = min(len(lines), approx_line + 3)
        for i in range(start, end):
            line = lines[i].lower()
            if ('select' in line or '+' in line or 'f"' in line) and 'from' in line:
                return i + 1  # 1-based
        
        return approx_line  # Fallback


# Global parser instance (singleton)
parser = TreeSitterParser()

# Test function
def test_tree_sitter():
    """Test AST parsing"""
    test_code = """
def get_user_data(user_input):
    query = "SELECT * FROM users WHERE name = '" + user_input + "'"
    return db.execute(query)

api_key = "sk-1234567890abcdef"  # Hardcoded
"""
    
    result = parser.parse_file_content(test_code, 'python')
    print("✅ Tree-sitter Test:")
    print(f"Functions: {len(result['functions'])}")
    for func in result['functions']:
        print(f"  - {func['name']} (lines {func['start_line']}-{func['end_line']})")
    
    print(f"Variables: {len(result['variables'])}")
    for var in result['variables']:
        print(f"  - {var['name']} at line {var['line']}: {var['value'][:20]}...")
    
    # Exact line for SQLi (approx 3 → exact 3)
    exact = parser.get_exact_line_for_issue(test_code, 'sqli', 3)
    print(f"Exact SQLi line: {exact}")

if __name__ == "__main__":
    test_tree_sitter()
