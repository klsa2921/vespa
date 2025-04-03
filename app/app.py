import os
from fastapi import FastAPI, File,Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from vespa_text_search import search_api
import uvicorn
from fastapi import UploadFile, Form
from pathlib import Path
from vespa import ingest_csv
app = FastAPI()

# Mount the "web" folder to serve static files
app.mount("/static", StaticFiles(directory="C:/Users/mmallikanti/Documents/GitHub/vespa/app/web/"), name="static")

options=["similarity","semantic","hybrid"]
@app.get("/ranking_profiles")
async def get_options():
    # Return the options as a JSON response
    formatted_options = [{"value": opt, "label": opt.capitalize()} for opt in options]
    return formatted_options
    # return {"options": options}

@app.get("/")
async def root():
    # Serve the index.html file (React frontend)
    return FileResponse("C:/Users/mmallikanti/Documents/GitHub/vespa/app/web/index.html")

@app.post("/submit")
async def submit_data(data: Request):
    # Process the received data (FastAPI will automatically parse and validate the data)
    body = await data.json()
    ranking_profiles = body.get("ranking_profiles")
    query = body.get("query")

    search_results,totalHits = search_api(ranking_profiles, query)  
    # print(f"Received ranking profiles: {ranking_profiles} and query: {query}")
    # print(f"Search results: {search_results}")

    # Return the response
    return {"message": "Data received successfully", "data": search_results,"totalHits":totalHits}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    upload_dir = Path("C:/Users/mmallikanti/Documents/GitHub/vespa/app/uploads/")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / file.filename
    
    with file_path.open("wb") as f:
        f.write(await file.read())
    
    ingest_csv(file_path)  
    
    return {"filename": file.filename, "message": "File uploaded and processed successfully"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
