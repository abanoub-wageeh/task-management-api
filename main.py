from fastapi import FastAPI
import models
from routes import auth, tasks
app = FastAPI()

models.SQLModel.metadata.create_all(models.engine)

app.include_router(auth.router)
app.include_router(tasks.router)

@app.get("/")
def root():
    return {"message": "Hello to my task managment app"}