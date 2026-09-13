from models import Base

# table to model mapping
TABLE_TO_MODEL_MAPPING = {
    m.__tablename__: m
    for m in Base.registry._class_registry.values()
    if hasattr(m, '__tablename__')
}