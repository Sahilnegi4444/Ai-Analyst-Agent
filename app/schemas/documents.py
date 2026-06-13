from pydantic import BaseModel, Field
from typing import List

class DocumentMetadata(BaseModel):
    """
    Pydantic schema representing document metadata.
    """
    filename: str = Field(..., description="The name of the PDF file.")
    title: str = Field(..., description="Descriptive title of the document.")
    chunks_count: int = Field(..., description="Number of text chunks generated and stored.")

class DocumentListResponse(BaseModel):
    """
    Pydantic schema representing the document collection catalog.
    """
    documents: List[DocumentMetadata] = Field(..., description="List of all uploaded and parsed documents.")

class DocumentUploadResponse(BaseModel):
    """
    Pydantic schema representing a document upload response.
    """
    filename: str = Field(..., description="Name of the uploaded PDF file.")
    chunks_count: int = Field(..., description="Number of chunks created and embedded.")
    status: str = Field("success", description="Status of the operation (e.g. success).")
