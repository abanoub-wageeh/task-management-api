from fastapi import FastAPI
import models

app = FastAPI()

models.SQLModel.metadata.create_all(models.engine)


@app.get("/")
def root():
    return {"message": "Hello to my task managment app"}