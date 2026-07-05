import sys
import json
import inspect
from pathlib import Path

# Add backend dir to python path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

from app.models.base import Base
import app.models.__init__  # load all models
from app.api.router import api_router
from fastapi.routing import APIRoute
from sqlalchemy import inspect as sqla_inspect

def dump_db_models():
    models_data = []
    for cls in Base.__subclasses__():
        mapper = sqla_inspect(cls)
        columns = []
        for col in mapper.columns:
            columns.append({
                "name": col.name,
                "type": str(col.type),
                "primary_key": col.primary_key,
                "nullable": col.nullable,
                "foreign_keys": [fk.target_fullname for fk in col.foreign_keys]
            })
        
        relationships = []
        for rel in mapper.relationships:
            relationships.append({
                "name": rel.key,
                "target": rel.mapper.class_.__name__,
                "direction": str(rel.direction.name)
            })

        models_data.append({
            "table_name": mapper.local_table.name,
            "class_name": cls.__name__,
            "columns": columns,
            "relationships": relationships
        })
    return models_data

def dump_api_routes():
    routes_data = []
    for route in api_router.routes:
        if isinstance(route, APIRoute):
            # Try to figure out permissions if any
            deps = [dep.dependency.__name__ if hasattr(dep.dependency, '__name__') else str(dep.dependency) for dep in route.dependencies]
            routes_data.append({
                "path": route.path,
                "methods": list(route.methods),
                "name": route.name,
                "endpoint": route.endpoint.__name__,
                "dependencies": deps,
                "tags": route.tags
            })
    return routes_data

if __name__ == "__main__":
    data = {
        "models": dump_db_models(),
        "routes": dump_api_routes()
    }
    with open(backend_dir / "docs_metadata.json", "w") as f:
        json.dump(data, f, indent=2)
    print("Introspection complete. Metadata saved to docs_metadata.json")
