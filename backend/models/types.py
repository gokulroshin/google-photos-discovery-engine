from sqlalchemy import JSON, TypeDecorator, String, Text
from sqlalchemy.dialects.postgresql import JSONB, ARRAY as PG_ARRAY
import json

# Platform-agnostic JSON (uses JSONB on PostgreSQL, JSON on SQLite)
JSONType = JSON().with_variant(JSONB, "postgresql")


class ArrayType(TypeDecorator):
    """
    TypeDecorator that uses PostgreSQL ARRAY(String) on Postgres
    and JSON-serialized list on SQLite.
    """
    impl = Text
    cache_ok = True

    def __init__(self, item_type=String, *args, **kwargs):
        self.item_type = item_type
        super().__init__(*args, **kwargs)

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_ARRAY(self.item_type))
        else:
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return []
        if dialect.name == "postgresql":
            return list(value)
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return []
        return value


class VectorType(TypeDecorator):
    """
    TypeDecorator for pgvector vector(dim) on PostgreSQL
    and JSON-serialized float list on SQLite.
    """
    impl = Text
    cache_ok = True

    def __init__(self, dim=768, *args, **kwargs):
        self.dim = dim
        super().__init__(*args, **kwargs)

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.types import UserDefinedType

            class PGVector(UserDefinedType):
                def __init__(self, dimensions):
                    self.dimensions = dimensions

                def get_col_spec(self, **kw):
                    return f"vector({self.dimensions})"

            return dialect.type_descriptor(PGVector(self.dim))
        else:
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            if isinstance(value, (list, tuple)):
                return "[" + ",".join(str(x) for x in value) + "]"
            return str(value)
        if isinstance(value, (list, tuple)):
            return json.dumps(value)
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                if value.startswith("[") and value.endswith("]"):
                    return json.loads(value)
                return [float(x) for x in value.strip("[]").split(",") if x.strip()]
            except Exception:
                return None
        return value
