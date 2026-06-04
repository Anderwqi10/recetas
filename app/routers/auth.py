from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.templating import render_template

from app.auth import (
    COOKIE_NAME,
    authenticate_user,
    create_access_token,
    get_current_user,
    get_current_user_optional,
    get_user_by_email,
    get_user_by_username,
    hash_password,
)
from app.database import get_db
from app.models import User
from app.schemas import Token, UserCreate, UserLogin, UserResponse

router = APIRouter()


def _set_auth_cookie(response: Response, email: str) -> None:
    token = create_access_token({"sub": email})
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=60 * 60 * 24,
        samesite="lax",
    )


# --- Páginas HTML ---


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, user: User | None = Depends(get_current_user_optional)):
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)


@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    user: User | None = Depends(get_current_user_optional),
):
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    response = render_template(
        "login.html",
        {"request": request, "error": None, "success": None},
    )
    if request.cookies.get("flash"):
        response.delete_cookie("flash")
    return response


@router.post("/login", response_class=HTMLResponse)
async def login_form(
    request: Request,
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, email, password)
    if not user:
        return render_template(
            "login.html",
            {
                "request": request,
                "error": "Correo o contraseña incorrectos",
                "success": None,
                "email": email,
            },
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    redirect = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    _set_auth_cookie(redirect, user.email)
    return redirect


@router.get("/register", response_class=HTMLResponse)
async def register_page(
    request: Request,
    user: User | None = Depends(get_current_user_optional),
):
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return render_template("register.html", {"request": request, "error": None})


@router.post("/register", response_class=HTMLResponse)
async def register_form(
    request: Request,
    email: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    db: Session = Depends(get_db),
):
    ctx = {"request": request, "error": None, "email": email, "username": username}

    if password != password_confirm:
        ctx["error"] = "Las contraseñas no coinciden"
        return render_template("register.html", ctx, status_code=400)

    if len(password) < 6:
        ctx["error"] = "La contraseña debe tener al menos 6 caracteres"
        return render_template("register.html", ctx, status_code=400)

    if len(username) < 3:
        ctx["error"] = "El usuario debe tener al menos 3 caracteres"
        return render_template("register.html", ctx, status_code=400)

    if get_user_by_email(db, email):
        ctx["error"] = "Ya existe una cuenta con ese correo"
        return render_template("register.html", ctx, status_code=400)

    if get_user_by_username(db, username):
        ctx["error"] = "Ese nombre de usuario ya está en uso"
        return render_template("register.html", ctx, status_code=400)

    user = User(
        email=email,
        username=username,
        hashed_password=hash_password(password),
    )
    db.add(user)
    db.commit()

    redirect = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    redirect.set_cookie("flash", "Cuenta creada. Ya puedes iniciar sesión.", max_age=30)
    return redirect


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user: User = Depends(get_current_user)):
    flash = request.cookies.get("flash")
    response = render_template(
        "dashboard.html",
        {"request": request, "user": user, "flash": flash},
    )
    if flash:
        response.delete_cookie("flash")
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(COOKIE_NAME)
    return response


# --- API JSON ---


@router.post("/api/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def api_register(data: UserCreate, db: Session = Depends(get_db)):
    if get_user_by_email(db, data.email):
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    if get_user_by_username(db, data.username):
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    user = User(
        email=data.email,
        username=data.username,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/api/login", response_model=Token)
def api_login(data: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, data.email, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )
    return Token(access_token=create_access_token({"sub": user.email}))


@router.get("/api/me", response_model=UserResponse)
def api_me(user: User = Depends(get_current_user)):
    return user
