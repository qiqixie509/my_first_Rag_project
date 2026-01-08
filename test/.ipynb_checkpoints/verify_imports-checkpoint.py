import sys
from pathlib import Path

# Simulate notebook logic
current_dir = Path.cwd()
if current_dir.name == "test":
    project_root = current_dir.parent
    sys.path.append(str(project_root))
    print(f"Added {project_root} to path")

try:
    from src.services.arxiv.factory import make_arxiv_client
    print("✓ Successfully imported src.services.arxiv.factory")
    
    client = make_arxiv_client()
    print(f"✓ Client created: {client.base_url}")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Other error: {e}")
    sys.exit(1)
