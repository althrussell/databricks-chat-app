import os, io, uuid, json, pandas as pd, typing as t
from datetime import datetime
from inference.rag import sql_exec, sql_fetch_all, get_current_user

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def user_volume_root(catalog: str, schema: str, volume: str, user_id: str) -> str:
    return f"/Volumes/{catalog}/{schema}/{volume}/{user_id}"

def save_file_to_volume(bytes_data: bytes, dest_path: str):
    ensure_dir(os.path.dirname(dest_path))
    with open(dest_path, "wb") as f:
        f.write(bytes_data)
    return dest_path

def register_document(doc: dict, catalog: str, schema: str):
    cols = ",".join(doc.keys())
    vals = ", ".join([f"'{str(v).replace("'","''")}'" for v in doc.values()])
    sql_exec(f"INSERT INTO {catalog}.{schema}.documents ({cols}) VALUES ({vals})", catalog, schema)

def create_csv_external_table(catalog: str, schema: str, table_name: str, csv_path: str, header: bool = True):
    hdr = "true" if header else "false"
    stmt = f"""
    CREATE TABLE IF NOT EXISTS {catalog}.{schema}.{table_name}
    USING CSV OPTIONS (header {hdr})
    LOCATION '{csv_path}'
    """
    sql_exec(stmt, catalog, schema)

def process_upload(file_name: str, bytes_data: bytes, catalog: str, schema: str, volume: str, tenant_id: str = "default") -> dict:
    user = get_current_user(catalog, schema)
    root = user_volume_root(catalog, schema, volume, user)
    uploads_dir = os.path.join(root, "uploads")
    extracted_dir = os.path.join(root, "extracted")

    dest_path = os.path.join(uploads_dir, file_name)
    save_file_to_volume(bytes_data, dest_path)

    doc_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()
    ext = (os.path.splitext(file_name)[1] or "").lower()
    total_rows = 0
    created_tables = []

    if ext in [".csv", ".tsv"]:
        # We do NOT parse to pandas; we register as an external CSV table
        table_name = f"u_{user.replace('@','_').replace('.','_')}_{doc_id.replace('-','_')}"
        create_csv_external_table(catalog, schema, table_name, dest_path, header=True)
        created_tables.append(table_name)
        register_document({
            "doc_id": doc_id,
            "user_id": user,
            "tenant_id": tenant_id,
            "source_type": "csv" if ext == ".csv" else "tsv",
            "uc_table": f"{catalog}.{schema}.{table_name}",
            "file_path": dest_path,
            "sheet": "",
            "num_rows": "0",
            "created_at": created_at
        }, catalog, schema)

    elif ext in [".xlsx", ".xls"]:
        # Convert each sheet to CSV under extracted/, register each as an external CSV table
        xls = pd.ExcelFile(io.BytesIO(bytes_data))
        for sheet in xls.sheet_names:
            df = xls.parse(sheet_name=sheet)
            # Save to CSV
            ensure_dir(extracted_dir)
            csv_path = os.path.join(extracted_dir, f"{os.path.splitext(file_name)[0]}_{sheet}.csv")
            df.to_csv(csv_path, index=False)
            table_name = f"u_{user.replace('@','_').replace('.','_')}_{doc_id.replace('-','_')}_{sheet.replace(' ','_')}"
            create_csv_external_table(catalog, schema, table_name, csv_path, header=True)
            created_tables.append(table_name)
            register_document({
                "doc_id": doc_id,
                "user_id": user,
                "tenant_id": tenant_id,
                "source_type": "excel",
                "uc_table": f"{catalog}.{schema}.{table_name}",
                "file_path": csv_path,
                "sheet": sheet,
                "num_rows": "0",
                "created_at": created_at
            }, catalog, schema)

    else:
        # Non-tabular: just register the file in documents
        register_document({
            "doc_id": doc_id,
            "user_id": user,
            "tenant_id": tenant_id,
            "source_type": ext.replace('.',''),
            "uc_table": "",
            "file_path": dest_path,
            "sheet": "",
            "num_rows": "0",
            "created_at": created_at
        }, catalog, schema)

    return {"doc_id": doc_id, "file_path": dest_path, "rows": total_rows, "tables": created_tables}
