import re
from typing import List, Dict, Any

def scan_for_secrets(code: str, filepath: str) -> List[Dict[str, Any]]:
    """
    Scans the provided code for hardcoded secrets.
    """
    patterns = [
        ('AWS access keys', r'AKIA[0-9A-Z]{16}', 'Hardcoded AWS access key detected'),
        ('AWS secret keys', r'(?i)aws_secret_access_key\s*=\s*["\'][A-Za-z0-9/+=]{40}["\']', 'Hardcoded AWS secret key detected'),
        ('GCP service account JSON', r'"type"\s*:\s*"service_account"', 'GCP service account JSON detected'),
        ('Generic API keys', r'(?i)(api_key|apikey|api_secret)\s*=\s*["\'][A-Za-z0-9_\-]{20,}["\']', 'Generic API key detected'),
        ('Generic passwords', r'(?i)(password|passwd|pwd)\s*=\s*["\'][^"\']{8,}["\']', 'Generic password detected'),
        ('Database URLs with credentials', r'(?i)(postgresql|mysql|mongodb)://[^:]+:[^@]+@', 'Database URL with credentials detected'),
        ('Private keys', r'-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----', 'Private key detected'),
        ('Generic tokens', r'(?i)(token|secret|bearer)\s*=\s*["\'][A-Za-z0-9_\-\.]{20,}["\']', 'Generic token detected'),
        ('Environment dumps', r'(?i)(os\.environ\b(?!\.get)|print\(.*os\.environ)', 'Environment dump detected'),
    ]

    findings = []
    lines = code.split('\n')
    
    # Normalize filepath to ensure consistent matching
    filepath_normalized = filepath.replace('\\', '/')
    is_test_file = 'tests/' in filepath_normalized

    for line_idx, line in enumerate(lines):
        line_num = line_idx + 1
        
        for pattern_name, regex, desc in patterns:
            for match in re.finditer(regex, line):
                matched_str = match.group(0)
                
                # Rule 4: Exclude patterns in test files (dummy test fixtures)
                if is_test_file and pattern_name in ['Generic passwords', 'Generic API keys', 'Generic tokens']:
                    lower_match = matched_str.lower()
                    if any(dummy in lower_match for dummy in ['test', 'dummy', 'mock', 'fake', 'example', '123']):
                        continue
                
                # Rule 4b: Exclude documentation-placeholder DB URLs (e.g. the
                # canonical SQLAlchemy example `postgresql://user:password@host`).
                # Only the password part decides: generic placeholder passwords and
                # template syntax (${VAR}, {var}, <password>) are not real secrets.
                # Real-looking passwords still block.
                if pattern_name == 'Database URLs with credentials':
                    cred = re.search(r'://[^:/@\s]+:([^@\s]+)@', matched_str)
                    if cred:
                        pwd = cred.group(1).lower()
                        placeholder_pwds = {
                            'password', 'pass', 'passwd', 'pwd',
                            'changeme', 'example', 'your_password', 'yourpassword',
                            'mypassword', 'xxx', 'xxxx', '****',
                        }
                        if pwd in placeholder_pwds or re.match(r'^[<{$%(]', pwd):
                            continue

                # Rule 5: Exclude patterns that read FROM environment
                if pattern_name == 'Environment dumps':
                    # Find where 'os.environ' ends in the match so we can check what follows it in the line
                    last_os_env = re.search(r'(?i)os\.environ', matched_str)
                    if last_os_env:
                        pos_after_environ = match.start() + last_os_env.end()
                        remainder_after = line[pos_after_environ:]
                        # If followed by dictionary access `[` or method `.get`, it's a safe read
                        if re.match(r'\s*\[', remainder_after) or re.match(r'\s*\.\s*get\b', remainder_after):
                            continue
                            
                findings.append({
                    'pattern_name': pattern_name,
                    'line': line_num,
                    'severity': 'block',
                    'match': matched_str,
                    'description': desc
                })

    return findings
