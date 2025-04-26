from fastapi import FastAPI
from models.base import Base
from routes import auth, posts, messages, ai_consultations, resources, consultants, consultant_messages, emergency_contacts, sos_logs
from database import engine


app = FastAPI()

app.include_router(auth.router, prefix='/auth')
app.include_router(posts.router, prefix='/posts')
app.include_router(messages.router, prefix='/messages')
app.include_router(ai_consultations.router, prefix='/ai-consultations')
app.include_router(resources.router, prefix='/resources')
app.include_router(consultants.router, prefix='/consultants')
app.include_router(consultant_messages.router, prefix='/consultant-messages')
app.include_router(emergency_contacts.router, prefix='/emergency-contacts')
app.include_router(sos_logs.router, prefix='/sos')



# Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)