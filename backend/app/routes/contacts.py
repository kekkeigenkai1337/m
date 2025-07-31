from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


router = APIRouter()
templates = Jinja2Templates(directory='frontend/templates')

@router.get('/contacts')
async def contact_page(request: Request):
    return templates.TemplateResponse('contact.html', {'request': request})
