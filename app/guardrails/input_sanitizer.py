import io
import tokenize
import re
from typing import List, Tuple

# Include a PATTERNS list at module level so it can be extended.
PATTERNS = [
    r"IGNORE ALL",
    r"IGNORE PREVIOUS",
    r"IGNORE ABOVE",
    r"DISREGARD",
    r"FORGET YOUR",
    r"SYSTEM PROMPT",
    r"NEW INSTRUCTIONS",
    r"YOU ARE NOW",
    r"ACT AS",
    r"OVERRIDE",
    r"BYPASS",
    r"JAILBREAK"
]

MULTI_LINE_PATTERNS = [
    r"(?s)^[rRuUfFbB]*[\"']{3}\s*You are",
    r"(?s)^[rRuUfFbB]*[\"']{3}\s*System:",
    r"(?s)^[rRuUfFbB]*[\"']{3}\s*Instructions:"
]

# Compile patterns for efficiency
COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in PATTERNS]
COMPILED_MULTILINE = [re.compile(p, re.IGNORECASE) for p in MULTI_LINE_PATTERNS]

def _check_injection(text: str) -> bool:
    for p in COMPILED_PATTERNS:
        if p.search(text):
            return True
    return False

def _check_multiline_injection(text: str) -> bool:
    if _check_injection(text):
        return True
    for p in COMPILED_MULTILINE:
        if p.match(text):
            return True
    return False

def is_suspicious(code: str) -> bool:
    """
    Returns True if any injection patterns were found in comments or strings.
    Useful for logging/alerting without modifying the code.
    """
    token_generator = tokenize.generate_tokens(io.StringIO(code).readline)
    while True:
        try:
            tok = next(token_generator)
            if tok.type == tokenize.COMMENT:
                if _check_injection(tok.string):
                    return True
            elif tok.type == tokenize.STRING:
                if _check_multiline_injection(tok.string):
                    return True
        except StopIteration:
            break
        except Exception:
            # Catch tokenization errors (e.g. unclosed strings, indentation issues)
            break
            
    return False

def sanitize_code_for_prompt(code: str) -> str:
    """
    Strips or neutralizes injection patterns in code comments and string literals.
    Does not modify actual code logic.
    """
    tokens = []
    token_generator = tokenize.generate_tokens(io.StringIO(code).readline)
    
    # Robustly gather tokens
    while True:
        try:
            tokens.append(next(token_generator))
        except StopIteration:
            break
        except Exception:
            # If we hit a syntax error we stop collecting tokens and 
            # sanitize what we've parsed so far.
            break

    lines = code.splitlines(keepends=True)
    if not lines:
        return code

    replacements = []
    
    for tok in tokens:
        tok_type = tok.type
        tok_string = tok.string
        start = tok.start
        end = tok.end
        
        s_row, s_col = start
        e_row, e_col = end
        
        if tok_type == tokenize.COMMENT:
            if _check_injection(tok_string):
                replacements.append((s_row, s_col, e_row, e_col, "# [sanitized - potential injection]"))
        elif tok_type == tokenize.STRING:
            if _check_multiline_injection(tok_string):
                # Replace the string content with '[sanitized]'
                # Preserve the string prefix and quotes
                m = re.match(r'^([rRuUfFbB]*)("""|"|\'\'\'|\')', tok_string)
                if m:
                    prefix = m.group(1)
                    quote_char = m.group(2)
                    sanitized_str = f"{prefix}{quote_char}[sanitized]{quote_char}"
                    replacements.append((s_row, s_col, e_row, e_col, sanitized_str))
                else:
                    # Fallback if somehow it doesn't match standard quotes
                    replacements.append((s_row, s_col, e_row, e_col, '"[sanitized]"'))

    # Sort replacements from bottom to top, right to left
    # This ensures applying a replacement doesn't invalidate subsequent coordinates
    replacements.sort(key=lambda x: (x[0], x[1]), reverse=True)
    
    for s_row, s_col, e_row, e_col, new_text in replacements:
        s_idx = s_row - 1
        e_idx = e_row - 1
        
        # In case the parser gives us out-of-bounds rows
        if s_idx >= len(lines) or e_idx >= len(lines):
            continue
            
        if s_idx == e_idx:
            line = lines[s_idx]
            lines[s_idx] = line[:s_col] + new_text + line[e_col:]
        else:
            first_line = lines[s_idx]
            last_line = lines[e_idx]
            
            lines[s_idx] = first_line[:s_col] + new_text + last_line[e_col:]
            
            # Delete intermediate lines from bottom up
            for i in range(e_idx, s_idx, -1):
                del lines[i]

    return "".join(lines)
