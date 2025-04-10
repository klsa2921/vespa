import os
from fastapi import FastAPI, File, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from vespa_index import ingest_text_data, ingest_csv,ingest_chunks
from vespa_search import search_api
import uvicorn
from fastapi import UploadFile, Form
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from properties.constants import docker,local

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

static_web_dic=docker.STATIC_WEB_DIRECTORY
upload_dir_path = docker.FILE_UPLOAD_DIRECTORY
# Mount the "web" folder to serve static files
# app.mount("/static", StaticFiles(directory="C:/Users/mmallikanti/Documents/GitHub/vespa/app/web/"), name="static")
app.mount("/static", StaticFiles(directory=static_web_dic), name="static")

options = ["similarity", "semantic", "hybrid"]


@app.get("/ranking_profiles")
async def get_options():
    # Return the options as a JSON response
    formatted_options = [{"value": opt, "label": opt.capitalize()} for opt in options]
    return formatted_options
    # return {"options": options}


@app.get("/")
async def root():
    # Serve the index.html file (React frontend)
    return FileResponse(os.path.join(static_web_dic, "index.html"))


@app.post("/search")
async def submit_data(data: Request):
    # Process the received data (FastAPI will automatically parse and validate the data)
    body = await data.json()
    ranking_profiles = body.get("ranking_profiles")
    query = body.get("query")
    username = body.get("username")
    search_results, totalHits = search_api(ranking_profiles, query, username)
    # print(f"Received ranking profiles: {ranking_profiles} and query: {query}")
    # print(f"Search results: {search_results}")

    # Return the response
    return {"message": "Data received successfully", "data": search_results, "totalHits": totalHits}

    # upload_dir = Path("C:/Users/mmallikanti/Documents/GitHub/vespa/app/uploads/")

@app.post("/uploadCSV")
async def upload_csv_file(file: UploadFile = File(...), username: str = Form(...)):
    upload_dir = Path(upload_dir_path)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / file.filename

    with file_path.open("wb") as f:
        f.write(await file.read())

    ingest_csv(file_path, username)

    return {"filename": file.filename, "message": "File uploaded and processed successfully"}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...), username: str = Form(...)):
    try:
        upload_dir = Path(upload_dir_path)
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / file.filename
        chunks = []  # Initialize chunks in case we need to process the file content
        with file_path.open("wb") as f:
            f.write(await file.read())

        if file.filename.endswith('.csv'):
            ingest_csv(file_path, username)
        else:
            chunks = ingest_text_data(file_path, username)
        if chunks:
            # If chunks were generated, return them in the response for confirmation
            return {"filename": file.filename, "message": "File uploaded and processed successfully", "chunks": chunks}
        return {"filename": file.filename, "message": "File uploaded and processed successfully"}
    except Exception as e:
        return {"error": str(e), "message": "An error occurred while processing the file"}


@app.post("/uploadChunks")
async def upload_chunks(chunks: list, username: str = Form(...)):
    try:
        ingest_chunks(chunks, username)
        return {"message": "Chunks uploaded and processed successfully"}
    except Exception as e:
        return {"error": str(e), "message": "An error occurred while processing the chunks"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
