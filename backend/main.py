import logging
import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .schemas import (
    GenerateContentRequest,
    GenerateContentResponse,
    GenerateImageRequest,
    AgenticContentResponse,
)
from .llm_service import generate_content
from .image_service import generate_images
from .agent_service import run_agentic_workflow

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

app = FastAPI(title="Lumina AI API")

# CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




@app.get("/")
def health():
    return {"status": "ok"}


@app.post("/generate-content", response_model=GenerateContentResponse)
def generate_content_endpoint(req: GenerateContentRequest):
    try:
        logger.info("Generating content for topic=%s grade=%s", req.topic, req.grade_level)
        content = generate_content(req.topic, req.grade_level)
        return content
    except Exception as e:
        logger.exception("Content generation failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-image")
def generate_image_endpoint(req: GenerateImageRequest):
    try:
        logger.info("Generating images for topic=%s grade=%s", req.topic, req.grade_level)
        images = generate_images(req.topic, req.grade_level)
        return images
    except Exception as e:
        logger.exception("Image generation failed")
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/generate-agentic", response_model=AgenticContentResponse)
def generate_agentic_endpoint(req: GenerateContentRequest):
    try:
        logger.info("Starting multi-agent research for topic=%s", req.topic)
        result = run_agentic_workflow(req.topic)
        return result
    except Exception as e:
        logger.exception("Agentic workflow failed")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
