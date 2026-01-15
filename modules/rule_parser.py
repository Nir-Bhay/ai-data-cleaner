"""
Rule Parser Module
------------------
Converts natural language cleaning instructions into structured rules.
Uses Gemini AI when available, with pattern-based fallback.
"""
import re
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import GEMINI_API_KEY, GEMINI_MODEL, USE_AI_PARSING


# ============================================================================
# RULE STRUCTURE
# ============================================================================
"""
Rules are structured as a list of dictionaries with the following format:

{
    "action": "action_name",
    "params": { ... action-specific parameters ... }
}

Supported actions:
- remove_duplicates: Remove duplicate rows
- fill_missing: Fill missing values (mean, median, mode, drop, or value)
- standardize_columns: Normalize column names to lowercase with underscores
- filter_rows: Filter rows based on a condition
- convert_dtype: Convert column data type
- drop_columns: Remove specified columns
- rename_columns: Rename columns
"""


def parse_rules(prompt: str, columns: List[str]) -> Dict[str, Any]:
    """
    Main function to parse natural language prompt into cleaning rules.
    
    Tries AI parsing first, falls back to pattern-based if AI unavailable.
    
    Args:
        prompt: Natural language cleaning instructions
        columns: List of column names in the dataset
        
    Returns:
        Dictionary with parsed rules and metadata
    """
    result = {
        "original_prompt": prompt,
        "parser_used": None,
        "rules": [],
        "warnings": []
    }
    
    # Try Gemini AI parsing first (if enabled and configured)
    if USE_AI_PARSING and GEMINI_API_KEY:
        try:
            rules = parse_with_gemini(prompt, columns)
            result["parser_used"] = "gemini"
            result["rules"] = rules
            print("✓ Rules parsed using Gemini AI")
            return result
        except Exception as e:
            result["warnings"].append(f"AI parsing failed, using fallback: {str(e)}")
            print(f"⚠ AI parsing failed: {e}")
    
    # Fallback to pattern-based parsing
    rules = parse_with_patterns(prompt, columns)
    result["parser_used"] = "pattern"
    result["rules"] = rules
    print("✓ Rules parsed using pattern matching")
    
    return result


def parse_with_gemini(prompt: str, columns: List[str]) -> List[Dict[str, Any]]:
    """
    Use Gemini AI to parse natural language into cleaning rules.
    
    Args:
        prompt: Natural language cleaning instructions
        columns: List of column names in the dataset
        
    Returns:
        List of rule dictionaries
    """
    from google import genai
    
    # Initialize Gemini client
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # Create the system prompt
    system_prompt = f"""You are a data cleaning assistant. Parse the user's natural language instructions 
into structured cleaning rules.

The dataset has these columns: {columns}

Return ONLY a JSON array of rule objects. Each rule must have:
- "action": One of: remove_duplicates, fill_missing, standardize_columns, filter_rows, convert_dtype, drop_columns, rename_columns
- "params": Action-specific parameters

Examples:
- "Remove duplicates" -> [{{"action": "remove_duplicates", "params": {{"columns": "all"}}}}]
- "Fill missing age with mean" -> [{{"action": "fill_missing", "params": {{"columns": ["age"], "method": "mean"}}}}]
- "Remove rows where age < 18" -> [{{"action": "filter_rows", "params": {{"condition": "age >= 18"}}}}]
- "Convert date to datetime" -> [{{"action": "convert_dtype", "params": {{"column": "date", "dtype": "datetime"}}}}]
- "Standardize column names" -> [{{"action": "standardize_columns", "params": {{}}}}]
- "Drop email column" -> [{{"action": "drop_columns", "params": {{"columns": ["email"]}}}}]
- "Fill missing values with 0" -> [{{"action": "fill_missing", "params": {{"columns": "all", "method": "value", "value": 0}}}}]

For fill_missing methods: "mean", "median", "mode", "drop", "value", "ffill", "bfill"
For filter_rows: use pandas-compatible conditions
For convert_dtype: "int", "float", "str", "datetime", "bool"

Return ONLY the JSON array, no explanations."""

    # Call Gemini API
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=f"{system_prompt}\n\nUser instruction: {prompt}"
    )
    
    # Parse the response
    response_text = response.text.strip()
    
    # Extract JSON from response (handle potential markdown formatting)
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0].strip()
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0].strip()
    
    rules = json.loads(response_text)
    
    # Validate rules structure
    validated_rules = []
    for rule in rules:
        if "action" in rule:
            if "params" not in rule:
                rule["params"] = {}
            validated_rules.append(rule)
    
    return validated_rules


def parse_with_patterns(prompt: str, columns: List[str]) -> List[Dict[str, Any]]:
    """
    Pattern-based fallback parser using regex matching.
    
    Args:
        prompt: Natural language cleaning instructions
        columns: List of column names in the dataset
        
    Returns:
        List of rule dictionaries
    """
    rules = []
    prompt_lower = prompt.lower()
    
    # Normalize column names for matching
    columns_lower = [col.lower() for col in columns]
    
    # Helper to find column matches in text
    def find_columns(text: str) -> List[str]:
        found = []
        for i, col_lower in enumerate(columns_lower):
            if col_lower in text.lower():
                found.append(columns[i])
        return found if found else None
    
    # ========================================
    # PATTERN 1: Remove duplicates
    # ========================================
    if re.search(r'(remove|delete|drop|eliminate)\s*(duplicate|dup)s?', prompt_lower):
        cols = find_columns(prompt)
        rules.append({
            "action": "remove_duplicates",
            "params": {"columns": cols if cols else "all"}
        })
    
    # ========================================
    # PATTERN 2: Fill missing values
    # ========================================
    fill_patterns = [
        (r'fill\s*(missing|null|nan|empty)\s*(values?)?\s*(with|using)?\s*(mean|average)', "mean"),
        (r'(mean|average)\s*(of|for)?\s*(missing|null)', "mean"),
        (r'fill\s*(missing|null|nan|empty)\s*(values?)?\s*(with|using)?\s*median', "median"),
        (r'median\s*(of|for)?\s*(missing|null)', "median"),
        (r'fill\s*(missing|null|nan|empty)\s*(values?)?\s*(with|using)?\s*mode', "mode"),
        (r'mode\s*(of|for)?\s*(missing|null)', "mode"),
        (r'(drop|remove|delete)\s*(rows?)?\s*(with)?\s*(missing|null|nan|empty)', "drop"),
        (r'fill\s*(missing|null|nan|empty)\s*(values?)?\s*(with|using)?\s*(\d+\.?\d*)', "value"),
        (r'(forward\s*fill|ffill)', "ffill"),
        (r'(backward\s*fill|bfill)', "bfill"),
    ]
    
    for pattern, method in fill_patterns:
        match = re.search(pattern, prompt_lower)
        if match:
            cols = find_columns(prompt)
            rule = {
                "action": "fill_missing",
                "params": {
                    "columns": cols if cols else "all",
                    "method": method
                }
            }
            # Extract value if method is "value"
            if method == "value":
                value_match = re.search(r'(\d+\.?\d*)', match.group())
                if value_match:
                    val = value_match.group(1)
                    rule["params"]["value"] = float(val) if '.' in val else int(val)
            rules.append(rule)
            break
    
    # ========================================
    # PATTERN 3: Standardize column names
    # ========================================
    if re.search(r'(standardize|normalize|clean|format)\s*(column|col)?\s*names?', prompt_lower):
        rules.append({
            "action": "standardize_columns",
            "params": {}
        })
    
    # ========================================
    # PATTERN 4: Filter rows
    # ========================================
    filter_patterns = [
        r'(remove|delete|filter|drop)\s*(rows?)?\s*(where|when|if|with)?\s*(.+?)(?:\s*$|\s*and\s|,)',
        r'(keep|retain)\s*(only)?\s*(rows?)?\s*(where|when|if|with)?\s*(.+?)(?:\s*$|\s*and\s|,)',
    ]
    
    for pattern in filter_patterns:
        match = re.search(pattern, prompt_lower)
        if match:
            condition_part = match.groups()[-1].strip()
            
            # Parse simple conditions
            # e.g., "age < 18", "status = active"
            cond_match = re.search(r'(\w+)\s*([<>=!]+|is|equals?)\s*["\']?(\w+)["\']?', condition_part)
            if cond_match:
                col, op, val = cond_match.groups()
                
                # Find actual column name
                actual_col = None
                for c in columns:
                    if c.lower() == col.lower():
                        actual_col = c
                        break
                
                if actual_col:
                    # Convert operator
                    op_map = {'is': '==', 'equals': '==', 'equal': '=='}
                    op = op_map.get(op, op)
                    
                    # Invert condition for "remove" vs "keep"
                    if 'remove' in match.group(1) or 'delete' in match.group(1) or 'drop' in match.group(1):
                        # Invert the condition
                        invert_map = {'<': '>=', '>': '<=', '<=': '>', '>=': '<', '==': '!=', '!=': '=='}
                        op = invert_map.get(op, op)
                    
                    # Try to parse value as number
                    try:
                        val = float(val) if '.' in val else int(val)
                        condition = f"{actual_col} {op} {val}"
                    except ValueError:
                        condition = f"{actual_col} {op} '{val}'"
                    
                    rules.append({
                        "action": "filter_rows",
                        "params": {"condition": condition}
                    })
                    break
    
    # ========================================
    # PATTERN 5: Convert data types
    # ========================================
    dtype_patterns = [
        (r'convert\s+(\w+)\s*(column)?\s*(to|as)\s*(int|integer)', "int"),
        (r'convert\s+(\w+)\s*(column)?\s*(to|as)\s*(float|decimal|number)', "float"),
        (r'convert\s+(\w+)\s*(column)?\s*(to|as)\s*(str|string|text)', "str"),
        (r'convert\s+(\w+)\s*(column)?\s*(to|as)\s*(date|datetime)', "datetime"),
        (r'convert\s+(\w+)\s*(column)?\s*(to|as)\s*(bool|boolean)', "bool"),
        (r'(\w+)\s*(column)?\s*(should\s*be|must\s*be|as)\s*(int|integer)', "int"),
    ]
    
    for pattern, dtype in dtype_patterns:
        match = re.search(pattern, prompt_lower)
        if match:
            col_name = match.group(1)
            actual_col = None
            for c in columns:
                if c.lower() == col_name.lower():
                    actual_col = c
                    break
            
            if actual_col:
                rules.append({
                    "action": "convert_dtype",
                    "params": {"column": actual_col, "dtype": dtype}
                })
    
    # ========================================
    # PATTERN 6: Drop columns
    # ========================================
    drop_col_patterns = [
        r'(drop|remove|delete)\s*(the)?\s*(\w+)\s*(column)',
        r'(drop|remove|delete)\s*(column)s?\s*[:\-]?\s*(.+)',
    ]
    
    for pattern in drop_col_patterns:
        match = re.search(pattern, prompt_lower)
        if match:
            cols_to_drop = find_columns(match.group())
            if cols_to_drop:
                rules.append({
                    "action": "drop_columns",
                    "params": {"columns": cols_to_drop}
                })
                break
    
    return rules


def print_rules(rules_result: Dict[str, Any]) -> None:
    """
    Pretty print the parsed rules.
    
    Args:
        rules_result: Result from parse_rules function
    """
    print("\n" + "=" * 60)
    print("PARSED CLEANING RULES")
    print("=" * 60)
    print(f"Parser used: {rules_result['parser_used']}")
    print(f"Original prompt: {rules_result['original_prompt'][:100]}...")
    
    if rules_result['warnings']:
        print("\nWarnings:")
        for w in rules_result['warnings']:
            print(f"  ⚠ {w}")
    
    print(f"\nRules ({len(rules_result['rules'])} found):")
    print("-" * 60)
    
    for i, rule in enumerate(rules_result['rules'], 1):
        print(f"\n{i}. Action: {rule['action']}")
        if rule.get('params'):
            for key, value in rule['params'].items():
                print(f"   - {key}: {value}")
    
    print("\n" + "=" * 60)


# Example usage
if __name__ == "__main__":
    # Test with sample prompts
    test_columns = ["name", "age", "email", "created_at", "status"]
    
    test_prompts = [
        "Remove duplicate rows",
        "Fill missing age values with the mean",
        "Remove rows where age less than 18",
        "Standardize column names",
        "Convert created_at to datetime",
    ]
    
    print("Testing Rule Parser")
    print("=" * 60)
    
    for prompt in test_prompts:
        print(f"\nPrompt: '{prompt}'")
        result = parse_rules(prompt, test_columns)
        print(f"Rules: {json.dumps(result['rules'], indent=2)}")
