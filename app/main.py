import os
from fastapi import FastAPI, File, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from vespa_index2 import ingest_text_data_with_index_name,ingest_qa_data,read_file
from vespa_search import search_api
import uvicorn
from fastapi import UploadFile, Form
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from properties.constants import env
from chunking.text_chunking_manager import TextChunkingManager as tcm
import json

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

allChunkingOptions=["regex","semantic","langchain_chars","langchain_rec","langchain_tokens","langchain_md","llama_rec","llama_tokens","llama_words"]

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

#using the api to search
@app.post("/search")
async def submit_data(data: Request):
    # Process the received data (FastAPI will automatically parse and validate the data)
    body = await data.json()
    search_results, totalHits = search_api(body)

    # Return the response
    return {"message": "Data received successfully", "data": search_results, "totalHits": totalHits}



    
#Using the api to upload file
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



#Present using api with all chunking mechanisms
@app.post("/getChunksWithMechanismWithAll")
async def sendChunksWithMechanismWithAll(data: Request):
    try:
        body = await data.json()
        # print(f"Received body: {body}")
        file_path = body.get("file_path")
        # file_content= body.get("file_content")  
        chunkingMechanism = body.get("chunkingMechanism")
        if chunkingMechanism not in allChunkingOptions:
            return {"error": "Invalid chunkingMechanism", "message": "chunkingMechanism must be one of the following: " + ", ".join(chunkingOptions)}
        
        if not file_path:
            return {"error": "file_path is required", "message": "Missing file_path in the request"}
        
        upload_dir = Path(upload_dir_path)
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / file_path
        file_content = read_file(file_path)
        parameters = body.get("parameters")
        # parameters["file_content"] = content
        parameters["file_content"] = file_content

        # print(f"Parameters: {parameters}")
        chunks= tcm().chunk_text(chunkingMechanism, file_content, **parameters)
        # print(f"Chunks: {chunks}")
        if not chunks:
            return {"error": "No chunks generated", "message": "No chunks were generated from the file content"}
        return {"chunks": chunks, "chunkingMechanism": chunkingMechanism}
    except Exception as e:
        return {"error": str(e), "message": "An error occurred while processing the file"}

    

#present using api tp upload chunks into particular index
@app.post("/uploadChunksIntoParticularIndex")
async def uploadChunksIntoParticularIndex(data:Request):
    try:
        data=await data.json()
        # print(f"Received data: {data}")
        if not data.get("chunks"):
            return {"error": "chunks is required", "message": "Missing chunks in the request"}
        try:
            ingest_text_data_with_index_name(data)
        except Exception as e:
            return {"error": str(e), "message": "An error occurred while processing the chunks and ingesting into Vespa"}
        
        try:
            qa_data=ingest_qa_data(data)
            if not qa_data:
                return {"error": "An error occurred while processing the chunks and ingesting qa recomendation into Vespa", "message": "Missing qa_data in the request"}
            response={
                "message": "Chunks ingested successfully",
                "qa_data": qa_data,
            }
            return response
        except Exception as e:
            return {"error": str(e), "message": "An error occurred while processing the chunks and ingesting qa recomendation into Vespa"}
        
    except Exception as e:
        return {"error": str(e), "message": "An error occurred while processing the chunks"}

@app.get("/indexProperties")
def indexProperties():
    try:
        file_path = os.path.join(static_web_dic, "properties/properties.json")
        if not os.path.exists(file_path):
            return {"error": "File not found", "message": "index_properties.json file not found"}
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: File {file_path} not found")
        return None
    except json.JSONDecodeError:
        print("Error: Invalid JSON format")
        return None

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
