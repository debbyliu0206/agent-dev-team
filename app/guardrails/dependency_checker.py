import urllib.request
import urllib.error
import json
import re

SAFE_PACKAGES = {
    "fastapi", "uvicorn", "sqlalchemy", "alembic", "pydantic", "httpx", "pytest", "pytest-asyncio",
    "flask", "django", "requests", "python-dotenv", "pytz", "bcrypt", "passlib", "python-jose",
    "firebase-admin", "celery", "redis", "psycopg2-binary", "aiohttp", "jinja2", "python-multipart",
    "email-validator", "starlette", "click", "rich", "typer", "sqlmodel", "tortoise-orm", "motor",
    "beanie", "boto3", "gunicorn", "whitenoise", "pillow", "numpy", "pandas"
}

def _extract_package_name(line: str) -> str:
    """Extracts the package name from a requirements.txt line."""
    # Remove comments and whitespace
    line = line.split('#')[0].strip()
    if not line:
        return ""
    
    # Extract package name (stop at =, <, >, ~, @, [, or whitespace)
    # A valid Python package name consists of letters, numbers, ., -, and _
    match = re.match(r'^([a-zA-Z0-9_\-\.]+)', line)
    if match:
        return match.group(1).lower()
    return ""

def check_requirements(filepath: str) -> dict:
    """
    Parses a requirements.txt file and verifies each package against PyPI
    to prevent supply-chain attacks (like slopsquatting hallucinations).
    """
    result = {'safe': True, 'packages': []}
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        return {'safe': False, 'error': str(e), 'packages': []}
        
    for line in lines:
        name = _extract_package_name(line)
        if not name:
            continue
            
        if name in SAFE_PACKAGES:
            result['packages'].append({
                'name': name,
                'status': 'allowed',
                'downloads': None,
                'reason': 'Package is on the allowlist'
            })
            continue
            
        # Check against PyPI
        url = f"https://pypi.org/pypi/{name}/json"
        req = urllib.request.Request(url, headers={'User-Agent': 'DependencyChecker/1.0'})
        
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    # Note: PyPI JSON API doesn't include download stats directly anymore,
                    # so we set it to None as per requirements.
                    result['packages'].append({
                        'name': name,
                        'status': 'verified',
                        'downloads': None,
                        'reason': 'Package found on PyPI'
                    })
        except urllib.error.HTTPError as e:
            if e.code == 404:
                result['safe'] = False
                result['packages'].append({
                    'name': name,
                    'status': 'not_found',
                    'downloads': None,
                    'reason': 'Package not found on PyPI (possible hallucination - BLOCKED)'
                })
            else:
                result['safe'] = False
                result['packages'].append({
                    'name': name,
                    'status': 'suspicious',
                    'downloads': None,
                    'reason': f'HTTP Error {e.code} when checking PyPI'
                })
        except urllib.error.URLError as e:
            result['safe'] = False
            result['packages'].append({
                'name': name,
                'status': 'suspicious',
                'downloads': None,
                'reason': f'URL Error checking PyPI: {str(e.reason)}'
            })
        except Exception as e:
            result['safe'] = False
            result['packages'].append({
                'name': name,
                'status': 'suspicious',
                'downloads': None,
                'reason': f'Unexpected error checking PyPI: {str(e)}'
            })
            
    return result
