import asyncio
from sqlalchemy import create_engine, MetaData

DATABASE_URL = "mysql+pymysql://root:Ayush%262003@127.0.0.1:3306/campus_active"
engine = create_engine(DATABASE_URL)
metadata = MetaData()
metadata.reflect(bind=engine)

for table_name in ['lms_apply_details', 'lms_apply_limit', 'lms_assign_faculty', 'lms_staff_record']:
    if table_name in metadata.tables:
        table = metadata.tables[table_name]
        print(f"Table: {table_name}")
        for column in table.columns:
            print(f"  - {column.name}: {column.type} (PK: {column.primary_key}, Nullable: {column.nullable})")
    else:
        print(f"Table {table_name} not found")
