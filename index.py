from fastapi import FastAPI
from controllers.mawaqitController import router as mawaqitRouter

app = FastAPI()
app.include_router(mawaqitRouter)
