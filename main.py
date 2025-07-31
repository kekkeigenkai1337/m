from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from backend.app.database import Base, engine
from backend.app.models import Product, ProductImage, AdminUser
from backend.app.routes import contacts, products, events, admin


app = FastAPI()
templates = Jinja2Templates(directory="frontend/templates")
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

@app.get('/')
async def homePage(request: Request):
        return templates.TemplateResponse('homepage.html', {'request': request})

app.include_router(products.router)
app.include_router(contacts.router)
app.include_router(events.router)
app.include_router(admin.router)

Base.metadata.create_all(bind=engine)
