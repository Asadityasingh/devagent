# # app/core/parsers/ast_parser.py (Fixed: No Conflicts + Python/C++ AST Parser)
# from tree_sitter import Language, Parser
# from tree_sitter_languages import get_language, get_parser  # Bundled grammars (Python, C++)
# import structlog
# from typing import Dict, List, Any
# import re

# logger = structlog.get_logger()

# class ASTParser:
#     """Tree-sitter parser for Python and C++ (precise line numbers and code structure)"""
    
#     def __init__(self):
#         self.parsers = {}
#         self.languages = {}
#         try:
#             # Load Python
#             PY_LANGUAGE = get_language('python')
#             self.languages['python'] = PY_LANGUAGE
#             parser_py = Parser()
#             parser_py.set_language(PY_LANGUAGE)
#             self.parsers['python'] = parser_py
            
#             # Load C++ (via 'cpp' in tree-sitter-languages)
#             CPP_LANGUAGE = get_language('cpp')
#             self.languages['cpp'] = CPP_LANGUAGE
#             parser_cpp = Parser()
#             parser_cpp.set_language(CPP_LANGUAGE)
#             self.parsers['cpp'] = parser_cpp
            
#             logger.info("ast_parser_initialized", languages=list(self.parsers.keys()))
#             print(f"🌳 AST Parser Ready: {list(self.parsers.keys())} languages")
#         except Exception as e:
#             logger.error("ast_parser_init_failed", error=str(e))
#             self.parsers = {}
    
#     def parse_file_content(self, code: str, language: str) -> Dict[str, Any]:
#         """
#         Parse code content to extract:
#         - Functions/classes with line ranges
#         - Variables/assignments (e.g., for secrets in Python; strings in C++)
#         - Exact line numbers for nodes
        
#         Supported: python, cpp
#         """
#         if language not in self.parsers:
#             logger.warning("unsupported_language_for_parsing", language=language)
#             return {'functions': [], 'variables': [], 'lines': len(code.splitlines())}
        
#         parser = self.parsers[language]
#         tree = parser.parse(bytes(code, "utf8"))
#         root_node = tree.root_node
        
#         functions = []  # {'name': str, 'start_line': int, 'end_line': int, 'body': str}
#         variables = []  # {'name': str, 'line': int, 'value': str}
        
#         def traverse(node, depth=0):
#             node_type = node.type
#             start_line = node.start_point[0] + 1  # 1-based
#             end_line = node.end_point[0] + 1
            
#             if language == 'python':
#                 if node_type == 'function_definition':
#                     name_node = node.named_children[0] if node.named_children else None
#                     func_name = name_node.text.decode('utf8').strip() if name_node and name_node.type == 'identifier' else 'anonymous'
#                     functions.append({
#                         'name': func_name,
#                         'start_line': start_line,
#                         'end_line': end_line,
#                         'params': [child.text.decode('utf8') for child in node.children if child.type == 'parameters'],
#                         'body_lines': (start_line, end_line)
#                     })
                
#                 elif node_type == 'assignment':
#                     left = node.child_by_field_name('left')
#                     right = node.child_by_field_name('right')
#                     if left and right:
#                         var_name = left.text.decode('utf8').strip()
#                         var_value = right.text.decode('utf8')[:50] + '...' if len(right.text) > 50 else right.text.decode('utf8')
#                         if '"' in var_value or "'" in var_value:  # String literal heuristic
#                             variables.append({
#                                 'name': var_name,
#                                 'line': start_line,
#                                 'value': var_value,
#                                 'type': 'potential_secret' if any(s in var_value.lower() for s in ['key', 'secret', 'pass']) else 'string_assignment'
#                             })
            
#             elif language == 'cpp':
#                 if node_type == 'function_definition':
#                     # C++: Find declarator for name
#                     declarator = node.child_by_field_name('declarator')
#                     if declarator:
#                         name_node = declarator.child_by_field_name('name') or declarator.named_children[0]
#                         func_name = name_node.text.decode('utf8').strip() if name_node else 'anonymous'
#                         functions.append({
#                             'name': func_name,
#                             'start_line': start_line,
#                             'end_line': end_line,
#                             'params': [],  # Parse params if needed
#                             'body_lines': (start_line, end_line)
#                         })
                
#                 elif node_type == 'assignment_expression':
#                     left = node.child_by_field_name('left')
#                     right = node.child_by_field_name('right')
#                     if left and right:
#                         var_name = left.text.decode('utf8').strip().split()[0] if left.text else ''
#                         var_value = right.text.decode('utf8')[:50] + '...' if len(right.text) > 50 else right.text.decode('utf8')
#                         if '"' in var_value:  # String literals in C++
#                             variables.append({
#                                 'name': var_name,
#                                 'line': start_line,
#                                 'value': var_value,
#                                 'type': 'potential_secret' if 'key' in var_value.lower() else 'string_assignment'
#                             })
            
#             # Recurse (limit depth to avoid stack overflow)
#             if depth < 10:
#                 for child in node.children:
#                     traverse(child, depth + 1)
        
#         traverse(root_node)
        
#         logger.info("ast_parsing_complete", language=language, functions_count=len(functions), variables_count=len(variables))
#         return {
#             'tree': tree,
#             'root_node': root_node,
#             'functions': functions,
#             'variables': variables,
#             'total_lines': root_node.end_point[0] + 1
#         }
    
#     def get_exact_line_for_issue(self, code: str, issue_type: str, approx_line: int, language: str = 'python') -> int:
#         """Map approximate issue line to exact via AST (e.g., SQL query or string concat)"""
#         lines = code.splitlines()
#         if approx_line > len(lines) or approx_line < 1:
#             return approx_line
        
#         # Language-specific heuristics
#         search_patterns = {
#             'sqli': [r'select.*from', r'query\s*=\s*["\'].*\+'],
#             'secret': [r'api_key|secret|password\s*=\s*["\'][^"\']+["\']'],
#             'mixed_type': [r'list\s*\[\s*mixed|append\s*\(\s*different\s*types']
#         }
        
#         patterns = search_patterns.get(issue_type.lower(), [r'.*'])  # Default any
#         start = max(0, approx_line - 5)
#         end = min(len(lines), approx_line + 5)
        
#         for i in range(start, end):
#             line = lines[i].lower()
#             if any(re.search(p, line) for p in patterns):
#                 return i + 1  # 1-based exact line
        
#         return approx_line  # Fallback


# # Global parser instance (singleton)
# parser = ASTParser()

# # Test function (Python + C++)
# def test_ast_parser():
#     """Test AST parsing for Python and C++"""
    
#     # Python test
#     py_code = """
# def get_user_data(user_input):
#     query = "SELECT * FROM users WHERE name = '" + user_input + "'"
#     return db.execute(query)

# api_key = "sk-1234567890abcdef"  # Hardcoded secret
# """
    
#     py_result = parser.parse_file_content(py_code, 'python')
#     print("\n=== Python AST Test ===")
#     print(f"Functions: {len(py_result['functions'])}")
#     for func in py_result['functions']:
#         print(f"  - {func['name']} (lines {func['start_line']}-{func['end_line']})")
    
#     print(f"Variables: {len(py_result['variables'])}")
#     for var in py_result['variables']:
#         print(f"  - {var['name']} at line {var['line']}: {var['value'][:20]}... ({var['type']})")
    
#     # C++ test
#     cpp_code = """
# #include <iostream>
# #include <string>

# std::string getUser(std::string userInput) {
#     std::string query = "SELECT * FROM users WHERE id = '" + userInput + "'";
#     return query;  // Simplified
# }

# const std::string API_KEY = "sk-1234567890abcdef";  // Hardcoded
# """
    
#     cpp_result = parser.parse_file_content(cpp_code, 'cpp')
#     print("\n=== C++ AST Test ===")
#     print(f"Functions: {len(cpp_result['functions'])}")
#     for func in cpp_result['functions']:
#         print(f"  - {func['name']} (lines {func['start_line']}-{func['end_line']})")
    
#     print(f"Variables: {len(cpp_result['variables'])}")
#     for var in cpp_result['variables']:
#         print(f"  - {var['name']} at line {var['line']}: {var['value'][:20]}... ({var['type']})")
    
#     # Exact line refinement
#     exact_py = parser.get_exact_line_for_issue(py_code, 'sqli', 3, 'python')
#     print(f"\nExact SQLi line (Python): {exact_py}")
    
#     exact_cpp = parser.get_exact_line_for_issue(cpp_code, 'secret', 9, 'cpp')
#     print(f"Exact Secret line (C++): {exact_cpp}")

# if __name__ == "__main__":
#     test_ast_parser()

# app/core/parsers/ast_parser.py (COMPLETE: Python/C++ AST Parser with Secret Detection)
from tree_sitter_languages import get_language, get_parser
import structlog
from typing import Dict, List, Any
import re

logger = structlog.get_logger()

class ASTParser:
    """Tree-sitter parser for Python and C++ (precise line numbers and code structure)"""
    
    def __init__(self):
        self.parsers = {}
        self.languages = {}
        try:
            # Python (bundled)
            self.languages['python'] = get_language('python')
            self.parsers['python'] = get_parser('python')
            
            # C++ (bundled as 'cpp')
            self.languages['cpp'] = get_language('cpp')
            self.parsers['cpp'] = get_parser('cpp')
            
            logger.info("ast_parser_initialized", languages=list(self.parsers.keys()))
            print(f"🌳 AST Parser Ready: {list(self.parsers.keys())} languages")
        except Exception as e:
            logger.error("ast_parser_init_failed", error=str(e))
            self.parsers = {}
    
    def parse_file_content(self, code: str, language: str) -> Dict[str, Any]:
        """
        Parse code content to extract:
        - Functions/classes with line ranges
        - Variables/assignments (secrets in Python/C++)
        - Exact line numbers for nodes
        """
        if language not in self.parsers:
            logger.warning("unsupported_language_for_parsing", language=language)
            return {'functions': [], 'variables': [], 'lines': len(code.splitlines())}
        
        parser = self.parsers[language]
        tree = parser.parse(bytes(code, "utf8"))
        root_node = tree.root_node
        
        functions = []
        variables = []
        
        def traverse(node, depth=0):
            if node is None:
                return
            node_type = node.type
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            
            if language == 'python':
                if node_type == 'function_definition':
                    name_node = None
                    for child in node.named_children:
                        if child.type == 'identifier':
                            name_node = child
                            break
                    func_name = name_node.text.decode('utf8') if name_node else 'anonymous'
                    functions.append({
                        'name': func_name,
                        'start_line': start_line,
                        'end_line': end_line,
                        'params': [],
                        'body_lines': (start_line, end_line)
                    })
                
                elif node_type == 'assignment':
                    left = node.child_by_field_name('left')
                    right = node.child_by_field_name('right')
                    if left and right:
                        var_name = left.text.decode('utf8').strip()
                        var_value = right.text.decode('utf8')[:50] + '...' if len(right.text) > 50 else right.text.decode('utf8')
                        if '"' in var_value or "'" in var_value:
                            var_type = 'potential_secret' if any(s in var_value.lower() for s in ['key', 'secret', 'pass', 'api', 'token']) else 'string_assignment'
                            variables.append({
                                'name': var_name,
                                'line': start_line,
                                'value': var_value,
                                'type': var_type
                            })
            
            elif language == 'cpp':
                if node_type == 'function_definition':
                    declarator = node.child_by_field_name('declarator')
                    if declarator:
                        name_node = None
                        for child in declarator.named_children:
                            if child.type == 'identifier':
                                name_node = child
                                break
                        func_name = name_node.text.decode('utf8') if name_node else 'anonymous'
                        functions.append({
                            'name': func_name,
                            'start_line': start_line,
                            'end_line': end_line,
                            'params': [],
                            'body_lines': (start_line, end_line)
                        })
                
                # FIXED: Handle C++ const/var initialization
                elif node_type == 'init_declarator':
                    # const std::string API_KEY = "value"
                    declarator = node.named_children[0] if node.named_children else None
                    initializer = node.child_by_field_name('value')
                    
                    if declarator and initializer:
                        var_name = 'unknown_var'
                        for child in declarator.named_children:
                            if child.type == 'identifier':
                                var_name = child.text.decode('utf8').strip()
                                break
                        
                        if initializer.type == 'string_literal' or '"' in initializer.text.decode('utf8'):
                            var_value = initializer.text.decode('utf8')[:50] + '...' if len(initializer.text) > 50 else initializer.text.decode('utf8')
                            if any(s in var_value.lower() for s in ['key', 'secret', 'pass', 'api', 'token']):
                                variables.append({
                                    'name': var_name,
                                    'line': start_line,
                                    'value': var_value,
                                    'type': 'potential_secret'
                                })
                
                # Also check standalone string_literal nodes
                elif node_type == 'string_literal':
                    var_value = node.text.decode('utf8')[:50] + '...' if len(node.text) > 50 else node.text.decode('utf8')
                    if any(s in var_value.lower() for s in ['key', 'secret', 'pass', 'api', 'token']):
                        var_name = 'literal_string'
                        if node.parent:
                            for sibling in node.parent.named_children:
                                if sibling.type == 'identifier' and sibling.end_byte < node.start_byte:
                                    var_name = sibling.text.decode('utf8').strip()
                                    break
                        variables.append({
                            'name': var_name,
                            'line': start_line,
                            'value': var_value,
                            'type': 'potential_secret'
                        })
            
            if depth < 8:
                for child in node.named_children:
                    traverse(child, depth + 1)
        
        traverse(root_node)
        
        logger.info("ast_parsing_complete", language=language, functions_count=len(functions), variables_count=len(variables))
        return {
            'tree': tree,
            'root_node': root_node,
            'functions': functions,
            'variables': variables,
            'total_lines': root_node.end_point[0] + 1
        }
    
    def get_exact_line_for_issue(self, code: str, issue_type: str, approx_line: int, language: str = 'python') -> int:
        """Refine issue line with pattern matching"""
        lines = code.splitlines()
        if approx_line > len(lines) or approx_line < 1:
            return approx_line
        
        patterns = {
            'sql injection': [r'select.*from', r'query\s*=\s*["\'].*[\+\,input]'],
            'hardcoded secret': [r'(api|secret|key|pass|token)\s*=\s*["\'][^"\']+["\']', r'const\s+\w+\s*=\s*["\'][^"\']+["\']'],
            'mixed_type': [r'list\s*\[\s*mixed', r'append\s*\(\s*(str|int)']
        }
        
        pats = patterns.get(issue_type.lower(), [r'.*'])
        start = max(0, approx_line - 5)
        end = min(len(lines), approx_line + 5)
        
        for i in range(start, end):
            line = lines[i].lower()
            if any(re.search(p, line) for p in pats):
                return i + 1
        
        return approx_line

# Global parser instance
parser = ASTParser()

# Test function
def test_ast_parser():
    py_code = '''def get_user_data(user_input):
    query = "SELECT * FROM users WHERE name = '" + user_input + "'"
    return db.execute(query)

api_key = "sk-1234567890abcdef"'''
    
    py_result = parser.parse_file_content(py_code, 'python')
    print("\n=== Python AST Test ===")
    print(f"Functions: {len(py_result['functions'])}")
    for func in py_result['functions']:
        print(f"  - {func['name']} (lines {func['start_line']}-{func['end_line']})")
    print(f"Variables: {len(py_result['variables'])}")
    for var in py_result['variables']:
        print(f"  - {var['name']} at line {var['line']}: {var['value'][:20]}... ({var['type']})")
    
    cpp_code = '''#include <string>

std::string getUser(std::string userInput) {
    std::string query = "SELECT * FROM users WHERE id = '" + userInput + "'";
    return query;
}

const std::string API_KEY = "sk-1234567890abcdef";'''
    
    cpp_result = parser.parse_file_content(cpp_code, 'cpp')
    print("\n=== C++ AST Test ===")
    print(f"Functions: {len(cpp_result['functions'])}")
    for func in cpp_result['functions']:
        print(f"  - {func['name']} (lines {func['start_line']}-{func['end_line']})")
    print(f"Variables: {len(cpp_result['variables'])}")
    for var in cpp_result['variables']:
        print(f"  - {var['name']} at line {var['line']}: {var['value'][:20]}... ({var['type']})")

if __name__ == "__main__":
    test_ast_parser()
