import os
from fastapi import FastAPI, File, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from chunking_mechanism import TextChunkingManager
from vespa_index import ingest_text_data, ingest_csv,ingest_chunks,get_chunks,ingest_chunk_array,read_file
from vespa_search import search_api
import uvicorn
from fastapi import UploadFile, Form
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from properties.constants import env

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

static_web_dic=env.STATIC_WEB_DIRECTORY
upload_dir_path = env.FILE_UPLOAD_DIRECTORY
# Mount the "web" folder to serve static files
# app.mount("/static", StaticFiles(directory="C:/Users/mmallikanti/Documents/GitHub/vespa/app/web/"), name="static")
app.mount("/static", StaticFiles(directory=static_web_dic), name="static")

options = ["similarity", "semantic", "hybrid"]
chunkingOptions = ["sentence", "paragraph", "document","regex","semantic"]

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

@app.post("/uploadFile")
async def upload_file_endpoint(file: UploadFile = File(...)):
    try:
        upload_dir = Path(upload_dir_path)
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / file.filename

        with file_path.open("wb") as f:
            f.write(await file.read())

        return {"filename": file.filename, "message": "File uploaded successfully"}
    except Exception as e:
        return {"error": str(e), "message": "An error occurred while uploading the file"}

@app.post("/getChunks")
async def sendChunks(file: UploadFile = File(...),chunkingMechanism: str = Form(...)):
    try:
        print(f"Received file: {file.filename}")
        upload_dir = Path(upload_dir_path)
        print(f"Upload directory: {upload_dir}")
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / file.filename
        print(f"File path: {file_path}")
        chunks = []
        with file_path.open("wb") as f:
            f.write(await file.read())

        chunks = get_chunks(file_path)
        return {"chunks": chunks}
    except Exception as e:
        return {"error": str(e), "message": "An error occurred while processing the file"}

@app.post("/getChunks1")
async def sendChunks1(data: Request):
    try:
        body = await data.json()
        file_path = body.get("file_path")
        chunkingMechanism = body.get("chunkingMechanism")
        if chunkingMechanism not in chunkingOptions:
            return {"error": "Invalid chunkingMechanism", "message": "chunkingMechanism must be one of the following: " + ", ".join(chunkingOptions)}
        
        if not file_path:
            return {"error": "file_path is required", "message": "Missing file_path in the request"}

        upload_dir = Path(upload_dir_path)
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / file_path

        chunks = get_chunks(file_path)
        return {"chunks": chunks, "chunkingMechanism": chunkingMechanism}
    except Exception as e:
        return {"error": str(e), "message": "An error occurred while processing the file"}


@app.post("/getChunksWithMechanism")
async def sendChunksWithMechanism(data: Request):
    try:
        body = await data.json()
        print(f"Received body: {body}")
        file_path = body.get("file_path")
        chunkingMechanism = body.get("chunkingMechanism")
        if chunkingMechanism not in chunkingOptions:
            return {"error": "Invalid chunkingMechanism", "message": "chunkingMechanism must be one of the following: " + ", ".join(chunkingOptions)}
        
        if not file_path:
            return {"error": "file_path is required", "message": "Missing file_path in the request"}
        
        manager = TextChunkingManager()
        upload_dir = Path(upload_dir_path)
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / file_path
        content = read_file(file_path)
        parameters = body.get("parameters")
        parameters["file_content"] = content
        # print(f"Parameters: {parameters}")
        chunks=manager.chunk_text(chunkingMechanism,parameters)
        print(f"Chunks: {chunks}")
        if not chunks:
            return {"error": "No chunks generated", "message": "No chunks were generated from the file content"}
        return {"chunks": chunks, "chunkingMechanism": chunkingMechanism}
    except Exception as e:
        return {"error": str(e), "message": "An error occurred while processing the file"}


@app.post("/uploadChunks")
async def upload_chunks(data:Request):
    try:
        print(f"Received data: {data}")
        data=await data.json()
        chunks=data.get("chunks")
        username=data.get("username")
        ingest_chunk_array(chunks, username)
        return {"message": "Chunks uploaded and processed successfully"}
    except Exception as e:
        return {"error": str(e), "message": "An error occurred while processing the chunks"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
