from fastapi import FastAPI
from .api.routes import messages

app = FastAPI()
app.include_router(messages.router)