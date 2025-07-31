from fastapi import Request
from fastapi.responses import RedirectResponse

def get_current_admin(request: Request):
    if request.cookies.get("admin_logged") != "true":
        return RedirectResponse(url="/login", status_code=302)
    return True
