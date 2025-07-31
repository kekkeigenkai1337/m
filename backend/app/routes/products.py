from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from ..database import get_db
from ..models import Product
from sqlalchemy.orm import Session


router = APIRouter()
templates = Jinja2Templates(directory='frontend/templates')

@router.get("/products", response_class=HTMLResponse)
def product_list(request: Request, db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return templates.TemplateResponse("product.html", {"request": request, "products": products})

@router.get("/products/{product_id}", response_class=HTMLResponse)
def product_detail(product_id: int, request: Request, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return HTMLResponse(status_code=404, content="Товар не найден")
    return templates.TemplateResponse("product_detail.html", {"request": request, "product": product})
