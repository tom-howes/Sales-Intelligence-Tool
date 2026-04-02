from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional
from pipeline import scrape_company, generate_brief, SCRAPE_PATHS, MAX_CHARS_PER_PAGE, MAX_CHARS_SELLER
import rag

app = FastAPI()


# --- Request/Response models ---

class ScrapeRequest(BaseModel):
    prospect_url: str
    seller_url: str


class ScrapeResponse(BaseModel):
    prospect_content: str
    seller_content: str


class GenerateRequest(BaseModel):
    prospect_url: str
    prospect_content: str
    seller_content: str
    stakeholder: str = "VP Engineering"
    selling_product: str = ""
    rag_context: Optional[list[str]] = None


class GenerateResponse(BaseModel):
    brief: str


class RetrieveRequest(BaseModel):
    query: str
    k: int = 3


class RetrieveResponse(BaseModel):
    chunks: list[str]


# --- Endpoints ---

@app.post("/scrape", response_model=ScrapeResponse)
def scrape(req: ScrapeRequest):
    prospect_content = scrape_company(req.prospect_url, SCRAPE_PATHS, MAX_CHARS_PER_PAGE)
    if not prospect_content:
        raise HTTPException(status_code=422, detail="Could not scrape the prospect URL.")

    seller_content = scrape_company(req.seller_url, ["", "/product"], MAX_CHARS_SELLER)
    if not seller_content:
        raise HTTPException(status_code=422, detail="Could not scrape the seller URL.")

    return ScrapeResponse(prospect_content=prospect_content, seller_content=seller_content)


@app.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest):
    brief = generate_brief(
        prospect_url=req.prospect_url,
        prospect_content=req.prospect_content,
        seller_content=req.seller_content,
        stakeholder=req.stakeholder,
        selling_product=req.selling_product,
        rag_context=req.rag_context,
    )
    return GenerateResponse(brief=brief)


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    filename = file.filename or ""
    if not (filename.lower().endswith(".pdf") or filename.lower().endswith(".txt")):
        raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported.")

    file_bytes = await file.read()
    try:
        chunk_count = rag.add_documents(file_bytes, filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"filename": filename, "chunk_count": chunk_count}


@app.post("/retrieve", response_model=RetrieveResponse)
def retrieve(req: RetrieveRequest):
    chunks = rag.retrieve(req.query, req.k)
    return RetrieveResponse(chunks=chunks)
