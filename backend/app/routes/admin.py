from fastapi import APIRouter, Request, Form, Depends, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from passlib.hash import bcrypt
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import AdminUser, Product, ProductImage
from ..dependencies.auth import get_current_admin
import os, uuid, shutil
from typing import List



router = APIRouter()
templates = Jinja2Templates(directory="frontend/templates")
UPLOAD_DIR = "frontend/static/uploads"

@router.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(AdminUser).filter_by(username=username).first()

    if not user or not bcrypt.verify(password, user.hash_password):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Неверные данные"})

    response = RedirectResponse(url="/admin", status_code=302)
    response.set_cookie("admin_logged", "true", httponly=True)
    return response

@router.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request, user=Depends(get_current_admin)):
    if isinstance(user, RedirectResponse):
        return user  # Если get_current_admin вернул редирект — отдадим его

    return templates.TemplateResponse("admin_products.html", {"request": request})

@router.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("admin_logged")
    return response


@router.get("/admin/products", response_class=HTMLResponse)
def admin_products(request: Request, db: Session = Depends(get_db), user=Depends(get_current_admin)):
    products = db.query(Product).all()
    return templates.TemplateResponse("admin_products.html", {"request": request, "products": products})


@router.get("/admin/add-product", response_class=HTMLResponse)
def add_product_form(request: Request, user=Depends(get_current_admin)):
    return templates.TemplateResponse("admin_add_product.html", {"request": request})

@router.post("/admin/add-product")
def add_product_post(
    request: Request,
    name: str = Form(...),
    description: str = Form(...),
    images: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    user = Depends(get_current_admin)
):
    product = Product(name=name, description=description)
    db.add(product)
    db.commit()
    db.refresh(product)

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    if images:
        # Устанавливаем первую картинку как main_image
        ext = images[0].filename.split('.')[-1]
        main_filename = f"{uuid.uuid4()}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, main_filename)
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(images[0].file, buffer)

        product.main_image = f"/static/uploads/{main_filename}"
        db.add(ProductImage(product_id=product.id, url=product.main_image))

        # Остальные изображения
        for image in images[1:]:
            ext = image.filename.split('.')[-1]
            filename = f"{uuid.uuid4()}.{ext}"
            filepath = os.path.join(UPLOAD_DIR, filename)
            with open(filepath, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)

            image_record = ProductImage(product_id=product.id, url=f"/static/uploads/{filename}")
            db.add(image_record)

    db.commit()
    return RedirectResponse("/admin/products", status_code=303)

@router.get("/admin/edit-product/{product_id}", response_class=HTMLResponse)
def edit_product_get(product_id: int, request: Request, db: Session = Depends(get_db), user=Depends(get_current_admin)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return templates.TemplateResponse("edit_product.html", {"request": request, "product": product})


@router.post("/admin/edit-product/{product_id}")
def edit_product(
    product_id: int,
    name: str = Form(...),
    description: str = Form(...),
    delete_images: List[int] = Form(default=[]),
    new_images: List[UploadFile] = File(default=[]),
    db: Session = Depends(get_db)
):
    product = db.query(Product).get(product_id)

    # Удаляем отмеченные изображения
    for image in product.images:
        if image.id in delete_images:
            try:
                os.remove("frontend" + image.url)
            except FileNotFoundError:
                pass
            db.delete(image)

    # Добавляем новые изображения
    for img in new_images:
        filename = f"{uuid.uuid4().hex}_{img.filename}"
        filepath = f"frontend/static/uploads/{filename}"
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(img.file, buffer)
        new_image = ProductImage(product_id=product.id, url="/static/uploads/" + filename)
        db.add(new_image)

    # Обновление текста
    product.name = name
    product.description = description

    db.commit()
    return RedirectResponse("/admin/products", status_code=302)

@router.post("/admin/delete-product/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db), user=Depends(get_current_admin)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Продукт не найден")

    # Удаление связанных изображений
    for image in product.images:
        relative_path = image.url.lstrip("/")  # '/static/uploads/...' → 'static/uploads/...'
        file_path = os.path.join(os.getcwd(), "frontend", relative_path)
        if os.path.exists(file_path):
            os.remove(file_path)

    # Удаление из базы
    db.delete(product)
    db.commit()

    return RedirectResponse(url="/admin/products", status_code=302)
