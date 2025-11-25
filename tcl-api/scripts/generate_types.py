import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tcl_api.main import app


def generate_openapi_spec():
    openapi_schema = app.openapi()

    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    output_dir = project_root.parent / "tcl-web" / "src" / "types"

    output_dir.mkdir(parents=True, exist_ok=True)

    openapi_file = output_dir / "openapi.json"
    with open(openapi_file, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2, ensure_ascii=False)

    print(f"Generated OpenAPI schema at: {openapi_file}")
    print("\nTo generate TypeScript types, run:")
    print("  cd tcl-web")
    print("  npm install -D openapi-typescript")
    print("  npx openapi-typescript src/types/openapi.json -o src/types/api.d.ts")

    return openapi_file


if __name__ == "__main__":
    try:
        generate_openapi_spec()
    except Exception as e:
        print(f"Error generating OpenAPI spec: {e}")
        sys.exit(1)
