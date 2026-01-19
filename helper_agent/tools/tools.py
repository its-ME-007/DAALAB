"""LangChain Tools for Code Analysis.

Modern tools using LangChain's Tool interface for code analysis tasks.
"""

import ast
import re
import os
from typing import List, Dict, Any
from langchain_classic.tools import Tool
from pydantic import BaseModel, Field


class CodeAnalysisInput(BaseModel):
    """Input schema for code analysis tools."""
    code: str = Field(description="The code to analyze")
    language: str = Field(default="python", description="Programming language")


def analyze_code_structure(code: str, language: str = "python") -> str:
    """Analyze the structure of code (functions, classes, imports)."""
    try:
        if language.lower() == "python":
            tree = ast.parse(code)
            
            functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend([alias.name for alias in node.names])
                elif isinstance(node, ast.ImportFrom):
                    imports.append(node.module or "")
            
            result = f"""Code Structure Analysis:

Functions ({len(functions)}): {', '.join(functions) if functions else 'None'}
Classes ({len(classes)}): {', '.join(classes) if classes else 'None'}
Imports ({len(imports)}): {', '.join(set(imports)) if imports else 'None'}
Lines of code: {len(code.split(chr(10)))}
"""
            return result
        else:
            return f"Structure analysis for {language} is not yet implemented. Analyzing as text...\n\nLines of code: {len(code.split(chr(10)))}"
    
    except SyntaxError as e:
        return f"Syntax error in code: {str(e)}"
    except Exception as e:
        return f"Error analyzing code structure: {str(e)}"


def detect_code_issues(code: str, language: str = "python") -> str:
    """Detect common issues and anti-patterns in code."""
    issues = []
    
    try:
        if language.lower() == "python":
            # Check for common issues
            if "eval(" in code:
                issues.append("[WARNING] Security: Use of eval() detected - security risk")
            
            if "exec(" in code:
                issues.append("[WARNING] Security: Use of exec() detected - security risk")
            
            # Check for bare excepts
            if re.search(r'except:\s*$', code, re.MULTILINE):
                issues.append("[WARNING] Best Practice: Bare except clause found - catch specific exceptions")
            
            # Check for mutable default arguments
            if re.search(r'def\s+\w+\([^)]*=\s*\[', code):
                issues.append("[WARNING] Bug Risk: Mutable default argument (list) detected")
            
            if re.search(r'def\s+\w+\([^)]*=\s*\{', code):
                issues.append("[WARNING] Bug Risk: Mutable default argument (dict) detected")
            
            # Check for global variables
            if re.search(r'^\s*global\s+', code, re.MULTILINE):
                issues.append("[INFO] Code Smell: Global variables used - consider refactoring")
            
            # Check line length
            long_lines = [i+1 for i, line in enumerate(code.split('\n')) if len(line) > 100]
            if long_lines:
                issues.append(f"[STYLE] Lines exceeding 100 characters: {long_lines[:5]}")
            
            # Try parsing for syntax errors
            try:
                ast.parse(code)
            except SyntaxError as e:
                issues.append(f"[ERROR] Syntax Error: Line {e.lineno}: {e.msg}")
        
        if not issues:
            return "[OK] No major issues detected! Code looks good."
        
        return "Issues Found:\n\n" + "\n".join(issues)
    
    except Exception as e:
        return f"Error during issue detection: {str(e)}"


def suggest_improvements(code: str, language: str = "python") -> str:
    """Suggest improvements and optimizations for the code."""
    suggestions = []
    
    try:
        if language.lower() == "python":
            # Check for docstrings
            if 'def ' in code and '"""' not in code and "'''" not in code:
                suggestions.append("[DOC] Add docstrings to functions for better documentation")
            
            # Check for type hints
            if 'def ' in code and '->' not in code:
                suggestions.append("[TIP] Consider adding type hints for better code clarity")
            
            # Check for list comprehensions
            if re.search(r'for\s+\w+\s+in.*:\s*\w+\.append\(', code):
                suggestions.append("TIP: Consider using list comprehensions for more Pythonic code")
            
            # Check for context managers
            if 'open(' in code and 'with ' not in code:
                suggestions.append("[BEST] Use context managers (with statement) for file operations")
            
            # Check for string formatting
            if '% ' in code or '+ ' in code and '"' in code:
                suggestions.append("[TIP] Consider using f-strings for cleaner string formatting")
            
            # Performance suggestions
            if 'range(len(' in code:
                suggestions.append("[PERF] Consider using enumerate() instead of range(len())")
        
        if not suggestions:
            return "[OK] Code looks well-optimized! No immediate suggestions."
        
        return "Improvement Suggestions:\n\n" + "\n".join(suggestions)
    
    except Exception as e:
        return f"Error generating suggestions: {str(e)}"


def calculate_complexity(code: str, language: str = "python") -> str:
    """Calculate code complexity metrics."""
    try:
        if language.lower() == "python":
            tree = ast.parse(code)
            
            # Count different node types
            if_count = sum(1 for _ in ast.walk(tree) if isinstance(_, ast.If))
            loop_count = sum(1 for _ in ast.walk(tree) if isinstance(_, (ast.For, ast.While)))
            function_count = sum(1 for _ in ast.walk(tree) if isinstance(_, ast.FunctionDef))
            class_count = sum(1 for _ in ast.walk(tree) if isinstance(_, ast.ClassDef))
            
            # Cyclomatic complexity estimate (simplified)
            complexity = if_count + loop_count + function_count + 1
            
            result = f"""Code Complexity Metrics:

Cyclomatic Complexity (estimated): {complexity}
Conditional Statements: {if_count}
Loops: {loop_count}
Functions: {function_count}
Classes: {class_count}

Complexity Assessment:
{get_complexity_assessment(complexity)}
"""
            return result
        else:
            return f"Complexity analysis for {language} not yet implemented."
    
    except Exception as e:
        return f"Error calculating complexity: {str(e)}"


def read_user_code(filename: str = "") -> str:
    """Read the user's code file from the AI service's temp directory."""
    try:
        # Strip quotes if present
        filename = filename.strip().strip("'").strip('"')
        
        # Get the temp_files directory: DAALAB/code_assist/temp_files/
        # __file__ is in helper_agent/tools/tools.py
        # Go up 3 levels to DAALAB, then to code_assist/temp_files
        root_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "code_assist", "temp_files")
        
        # Debug: Print the resolved path
        print(f"DEBUG: Looking for files in: {root_dir}")
        print(f"DEBUG: Directory exists: {os.path.exists(root_dir)}")
        if os.path.exists(root_dir):
            print(f"DEBUG: Files in directory: {os.listdir(root_dir)}")
        
        # If no filename provided, auto-detect code.py or user.cpp
        if not filename:
            code_py_path = os.path.join(root_dir, "code.py")
            user_cpp_path = os.path.join(root_dir, "user.cpp")
            print(f"DEBUG: Checking code.py at: {code_py_path}, exists: {os.path.exists(code_py_path)}")
            print(f"DEBUG: Checking user.cpp at: {user_cpp_path}, exists: {os.path.exists(user_cpp_path)}")
            
            if os.path.exists(code_py_path):
                filename = "code.py"
            elif os.path.exists(user_cpp_path):
                filename = "user.cpp"
            else:
                return f"[ERROR] No code.py or user.cpp found in {root_dir}. Please create one of these files."
        
        file_path = os.path.join(root_dir, filename)
        
        if not os.path.exists(file_path):
            return f"[ERROR] File '{filename}' not found at {file_path}."
        
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        lines = len(code.split('\n'))
        
        # Return code with summary for the agent to use
        return f"File: {filename} ({lines} lines)\n\n{code}"
    
    except Exception as e:
        return f"Error reading file: {str(e)}"


def list_uploaded_files(input_text: str = "") -> str:
    """List all files in the temp directory."""
    try:
        root_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "code_assist", "temp_files")
        
        if not os.path.exists(root_dir):
            return "[ERROR] Temp directory not found."
        
        files = os.listdir(root_dir)
        
        if not files:
            return "[INFO] No files uploaded yet."
        
        result = f"[FILES] Files in temp directory ({len(files)} total):\n\n"
        
        for filename in files:
            file_path = os.path.join(root_dir, filename)
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path)
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = len(f.readlines())
                result += f"  • {filename} - {lines} lines, {size} bytes\n"
        
        return result
    
    except Exception as e:
        return f"Error listing files: {str(e)}"


def get_complexity_assessment(complexity: int) -> str:
    """Get assessment based on complexity score."""
    if complexity <= 5:
        return "[OK] Low - Code is simple and easy to maintain"
    elif complexity <= 10:
        return "[WARNING] Moderate - Consider breaking into smaller functions"
    elif complexity <= 20:
        return "[HIGH] High - Refactoring recommended"
    else:
        return "[CRITICAL] Very High - Immediate refactoring needed"


def create_code_analysis_tools() -> List[Tool]:
    """Create and return a list of LangChain tools for code analysis."""
    
    tools = [
        Tool(
            name="list_uploaded_files",
            func=list_uploaded_files,
            description="Lists all files currently uploaded in the temp directory. Use this to see what files are available before reading. No input required."
        ),
        Tool(
            name="read_user_code",
            func=read_user_code,
            description="Reads a specific code file from the workspace. Input should be empty string (to auto-detect code.py/user.cpp) or provide filename like: code.py, main.py, etc."
        ),
        Tool(
            name="analyze_code_structure",
            func=lambda x: analyze_code_structure(x, "python"),
            description="Analyzes the structure of code including functions, classes, and imports. Input should be the code as a string."
        ),
        Tool(
            name="detect_code_issues",
            func=lambda x: detect_code_issues(x, "python"),
            description="Detects common issues, bugs, and anti-patterns in code. Input should be the code as a string."
        ),
        Tool(
            name="suggest_improvements",
            func=lambda x: suggest_improvements(x, "python"),
            description="Suggests improvements and optimizations for code. Input should be the code as a string."
        ),
        Tool(
            name="calculate_complexity",
            func=lambda x: calculate_complexity(x, "python"),
            description="Calculates complexity metrics for code. Input should be the code as a string."
        ),
    ]
    
    return tools