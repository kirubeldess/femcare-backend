# main.py
import logging_config  # Initialize logging
import logging

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from models.base import Base
from routes import (
    ai_consultations,
    admin,
    auth,
    consultant_messages,
    consultants,
    emergency_contacts,
    messages,
    posts,
    resources,
    sos_logs,
    sync,  # Add the new sync route
    reactions,  # Added reactions router
    community_content,  # Added community_content router
    admin_moderation,  # Added admin_moderation router
    admin_notifications,  # Added admin_notifications router
    appointments,  # Added appointments router
    notifications,  # Added user notifications router
)
from database import engine
import uvicorn
from utils.auth import get_current_user
from services.scheduler import reminder_scheduler

# Get logger
logger = logging.getLogger(__name__)

# Create the FastAPI app
app = FastAPI(
    title="FemCare API",
    description="Backend API for the FemCare application - Supporting Women's Health and Safety",
    version="1.0.0",
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


# Middleware for logging requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Log the request path and method
    logger.info(f"Request: {request.method} {request.url.path}")

    # Process the request
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )


# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(admin.router, tags=["Admin"])  # Admin routes with built-in prefix
app.include_router(posts.router, prefix="/posts", tags=["Vent Posts"])
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
app.include_router(
    sync.router, prefix="/sync", tags=["Offline Sync"]
)  # Add the sync router
app.include_router(
    reactions.router, prefix="/reactions", tags=["Reactions"]
)  # Added reactions router
app.include_router(
    community_content.router, prefix="/community-content", tags=["Community Content"]
)  # Added community_content router
app.include_router(
    admin_moderation.router
)  # Added admin_moderation router (prefix is in the router itself)
app.include_router(
    admin_notifications.router,
    prefix="/admin/notifications",
    tags=["Admin Notifications"],
)  # Added admin_notifications router
app.include_router(
    appointments.router, prefix="/appointments", tags=["Appointments"]
)  # Added appointments router
app.include_router(
    notifications.router, prefix="/notifications", tags=["Notifications"]
)  # Added user notifications router


# Root endpoint to provide API info
@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to FemCare API",
        "version": "1.0.0",
        "description": "Supporting Women's Health and Safety in Ethiopia",
        "documentation": "/docs",
    }


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}


# Authenticated test endpoint
@app.get("/protected", tags=["Test"])
async def protected_route(current_user=Depends(get_current_user)):
    return {
        "message": "This is a protected route",
        "user_id": current_user.id,
        "name": current_user.name,
        "role": current_user.role,
    }


# Create database tables
Base.metadata.create_all(engine)

# Start the appointment reminder scheduler
reminder_scheduler.start()

# Run the application with uvicorn when this file is executed
if __name__ == "__main__":
    # Use production settings
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=False)
