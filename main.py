import logging_config  # Initialize logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models.base import Base
from routes import (
    ai_consultations,
    auth,
    consultant_messages,
    consultants,
    emergency_contacts,
    messages,
    posts,
    resources,
    sos_logs,
)
from database import engine
import uvicorn

# Create the FastAPI app
app = FastAPI(
    title="FemCare API",
    description="Backend API for the FemCare application",
    version="1.0.0",
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(posts.router, prefix="/posts", tags=["Posts"])
app.include_router(messages.router, prefix="/messages", tags=["Messages"])
app.include_router(
    ai_consultations.router, prefix="/ai-consultations", tags=["AI Consultations"]
)
app.include_router(resources.router, prefix="/resources", tags=["Resources"])
app.include_router(consultants.router, prefix="/consultants", tags=["Consultants"])
app.include_router(
    consultant_messages.router,
    prefix="/consultant-messages",
    tags=["Consultant Messages"],
)
app.include_router(
    emergency_contacts.router, prefix="/emergency-contacts", tags=["Emergency Contacts"]
)
app.include_router(sos_logs.router, prefix="/sos", tags=["SOS Logs"])

# Create database tables
Base.metadata.create_all(engine)

# Run the application with uvicorn when this file is executed
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8100, reload=False)
