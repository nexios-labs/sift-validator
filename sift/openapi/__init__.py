"""
OpenAPI schema generation for Sift validators.
"""

# Direct import without renaming to avoid confusion
from sift.openapi.schema import (
    generate_schema,
    generate_full_openapi_schema,
    OpenAPIVersion,
    SchemaContext,
    get_schema_components
)

# Export with expected names
generate_openapi_schema = generate_schema
generate_openapi_components = get_schema_components

__all__ = [
    "generate_openapi_schema",
    "generate_schema",
    "generate_openapi_components",
    "get_schema_components",
    "generate_full_openapi_schema",
    "OpenAPIVersion",
    "SchemaContext"
]
