from fastapi import FastAPI, UploadFile, File, Header, HTTPException
from fastapi.responses import FileResponse
import os
import shutil

app = FastAPI()

SHARED_DIR = "/data/shared"
# avoid hardcoding the token in the code
WRITE_TOKEN = os.getenv("WRITE_TOKEN")
# WRITE_TOKEN = "s3cr3t-token"  # Only those who have this token can write or delete

# 1. Read-only: list files
@app.get("/list")
async def list_files():
    return os.listdir(SHARED_DIR)

# 2. Read-only: download a file
@app.get("/read/{filename}")
async def read_file(filename: str):
    filepath = os.path.join(SHARED_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(404, "File not found")
    return FileResponse(filepath)

# 3. Secure: upload a new file (only if token is provided)
@app.post("/upload")
async def upload_file(file: UploadFile = File(...), token: str = Header(None)):
    if token != WRITE_TOKEN:
        raise HTTPException(403, "Not authorized to upload")
    
    filepath = os.path.join(SHARED_DIR, file.filename)
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"status": "uploaded", "filename": file.filename}

# 4. Secure: overwrite a file (only if token is provided)
@app.put("/overwrite/{filename}")
async def overwrite_file(filename: str, file: UploadFile = File(...), token: str = Header(None)):
    if token != WRITE_TOKEN:
        raise HTTPException(403, "Not authorized to overwrite")
    filepath = os.path.join(SHARED_DIR, filename)
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"status": "overwritten", "filename": filename}

# 5. Secure: delete a file (only if token is provided)
@app.delete("/delete/{filename}")
async def delete_file(filename: str, token: str = Header(None)):
    if token != WRITE_TOKEN:
        raise HTTPException(403, "Not authorized to delete")

    filepath = os.path.join(SHARED_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(404, "File not found")
    
    os.remove(filepath)
    return {"status": "deleted", "filename": filename}
