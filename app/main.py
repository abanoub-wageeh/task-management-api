from fastapi import FastAPI
from app.routes import auth, tasks, comments, projects
app = FastAPI()

app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(comments.router)
app.include_router(projects.router)

@app.get("/")
def root():
    return {"message": "Hello to my task managment app"}