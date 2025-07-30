import os, io, uuid, json, pandas as pd, typing as t
from datetime import datetime
from pyspark.sql import SparkSession

def get_spark():
    spark = SparkSession.getActiveSession()
    if spark is None:
        spark = SparkSession.builder.getOrCreate()
    return spark

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def get_user_id() -> str:
    try:
        spark = get_spark()
        user = spark.sql("SELECT current_user()").first()[0]
        return user
    except Exception:
        return "unknown_user"

def user_volume_root(catalog: str, schema: str, volume: str, user_id: str) -> str:
    return f"/Volumes/{catalog}/{schema}/{volume}/{user_id}"

def save_file_to_volume(bytes_data: bytes, dest_path: str):
    ensure_dir(os.path.dirname(dest_path))
    with open(dest_path, "wb") as f:
        f.write(bytes_data)
    return dest_path

def ingest_to_delta(df: pd.DataFrame, table_full: str, mode: str = "append"):
    spark = get_spark()
    sdf = spark.createDataFrame(df)
    sdf.write.mode(mode).format("delta").saveAsTable(table_full)

def register_document(doc: dict, table_full: str):
    spark = get_spark()
    cols = list(doc.keys())
    sdf = spark.createDataFrame([tuple(doc[c] for c in cols)], schema=",".join([f"{c} string" for c in cols]))
    sdf.write.mode("append").saveAsTable(table_full)

def process_upload(file_name: str, bytes_data: bytes, catalog: str, schema: str, volume: str, tenant_id: str = "default") -> dict:
    user = get_user_id()
    root = user_volume_root(catalog, schema, volume, user)
    uploads_dir = os.path.join(root, "uploads")
    dest_path = os.path.join(uploads_dir, file_name)
    save_file_to_volume(bytes_data, dest_path)

    doc_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()
    documents_table = f"{catalog}.{schema}.documents"

    ext = (os.path.splitext(file_name)[1] or "").lower()
    total_rows = 0
    if ext in [".csv", ".tsv"]:
        sep = "," if ext == ".csv" else "\t"
        df = pd.read_csv(io.BytesIO(bytes_data), sep=sep)
        target_table = f"{catalog}.{schema}.u_{user.replace('@','_').replace('.','_')}_{doc_id.replace('-','_')}"
        ingest_to_delta(df, target_table, mode="overwrite")
        total_rows = len(df)
        register_document({
            "doc_id": doc_id,
            "user_id": user,
            "tenant_id": tenant_id,
            "source_type": "csv" if ext == ".csv" else "tsv",
            "uc_table": target_table,
            "file_path": dest_path,
            "sheet": "",
            "num_rows": str(total_rows),
            "created_at": created_at
        }, documents_table)
    elif ext in [".xlsx", ".xls"]:
        xls = pd.ExcelFile(io.BytesIO(bytes_data))
        for sheet in xls.sheet_names:
            df = xls.parse(sheet_name=sheet)
            target_table = f"{catalog}.{schema}.u_{user.replace('@','_').replace('.','_')}_{doc_id.replace('-','_')}_{sheet.replace(' ','_')}"
            ingest_to_delta(df, target_table, mode="overwrite")
            total_rows += len(df)
            register_document({
                "doc_id": doc_id,
                "user_id": user,
                "tenant_id": tenant_id,
                "source_type": "excel",
                "uc_table": target_table,
                "file_path": dest_path,
                "sheet": sheet,
                "num_rows": str(len(df)),
                "created_at": created_at
            }, documents_table)
    else:
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
        }, documents_table)

    return {"doc_id": doc_id, "file_path": dest_path, "rows": total_rows}
