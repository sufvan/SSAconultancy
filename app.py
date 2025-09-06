
import os, re, datetime
import shutil
from pathlib import Path

from fastapi import FastAPI, Request, Form, Depends, HTTPException, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

# --- Paths & Config ---
BASE_DIR = Path(__file__).parent
SITE_DIR = BASE_DIR  # aapke current code ke mutabiq root hi site dir hai

SEED_DB = SITE_DIR / "assets" / "data" / "app.db"       # repo ke andar wali seed
RUNTIME_DB = Path("/tmp/app.db")                        # Vercel par writable

# Vercel/Server detect (simple): agar /tmp writable hai to runtime DB use karo
use_runtime = os.access("/tmp", os.W_OK)

if use_runtime:
    # first boot par /tmp/app.db na ho to seed copy kar do
    if SEED_DB.exists() and not RUNTIME_DB.exists():
        RUNTIME_DB.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SEED_DB, RUNTIME_DB)
    DB_PATH = RUNTIME_DB
else:
    # local dev ya normal server
    DB_DIR = SITE_DIR / "assets" / "data"
    DB_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH = DB_DIR / "app.db"

# print("== SITE_DIR:", SITE_DIR)
# print("== DB_PATH :", DB_PATH)
# --- App & DB ---
SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-secret-key")
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class Software(Base):
    __tablename__ = "software"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    slug = Column(String(200), nullable=True)
    category = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    price_one_time = Column(Integer, nullable=True)
    price_yearly = Column(Integer, nullable=True)
    is_free = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    download_url = Column(Text, nullable=True)
    payment_link_onetime = Column(Text, nullable=True)
    payment_link_yearly = Column(Text, nullable=True)
    image = Column(Text, nullable=True)  # public URL like /assets/uploads/..
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)


class ReleaseNote(Base):
    __tablename__ = "release_notes"
    id = Column(Integer, primary_key=True)
    title = Column(String(250), nullable=False)
    version = Column(String(50), nullable=True)
    software_id = Column(Integer, nullable=True)  # optional relation by id
    release_date = Column(DateTime, default=datetime.datetime.utcnow)
    content = Column(Text, nullable=True)  # markdown/plain
    is_published = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

class KnownIssue(Base):
    __tablename__ = "known_issues"
    id = Column(Integer, primary_key=True)
    title = Column(String(250), nullable=False)
    status = Column(String(50), default="Open")   # Open, In Progress, Fixed
    content = Column(Text, nullable=True)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)



class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    industry = Column(String(120), nullable=True)
    city = Column(String(120), nullable=True)
    website = Column(String(250), nullable=True)
    image = Column(Text, nullable=True)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

Base.metadata.create_all(bind=engine)

# Lightweight migration: ensure 'image' column exists
from sqlalchemy import text as _sqltext
with engine.connect() as conn:
    # ensure known_issues table exists
    conn.exec_driver_sql("""
    CREATE TABLE IF NOT EXISTS known_issues (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        status TEXT,
        content TEXT,
        sort_order INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        created_at TEXT,
        updated_at TEXT
    )
    """)

    cols = [r[1] for r in conn.exec_driver_sql("PRAGMA table_info('software')").fetchall()]
    if 'image' not in cols:
        conn.exec_driver_sql("ALTER TABLE software ADD COLUMN image TEXT")
    # ensure release_notes table exists
    conn.exec_driver_sql("""
    CREATE TABLE IF NOT EXISTS release_notes (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        version TEXT,
        software_id INTEGER,
        release_date TEXT,
        content TEXT,
        is_published INTEGER DEFAULT 1,
        created_at TEXT,
        updated_at TEXT
    )
    """)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def is_logged_in(request: Request) -> bool:
    return bool(request.session.get("admin_ok"))

# --- Helpers ---

def _to_int(val):
    try:
        if val is None: 
            return None
        s = str(val).strip()
        if s == "":
            return None
        return int(s)
    except Exception:
        return None

def _save_upload(file: UploadFile | None) -> str | None:
    if not file:
        return None
    name = (file.filename or "").lower()
    if not name:
        return None
    allowed = (".png", ".jpg", ".jpeg", ".webp", ".svg")
    ext = os.path.splitext(name)[1]
    if ext not in allowed:
        return None
    up_dir = os.path.join(SITE_DIR, "assets", "uploads")
    os.makedirs(up_dir, exist_ok=True)
    base = re.sub(r"[^a-z0-9_-]+", "-", os.path.splitext(os.path.basename(name))[0])
    fname = f"{base}-{int(datetime.datetime.utcnow().timestamp())}{ext}"
    path = os.path.join(up_dir, fname)
    with open(path, "wb") as out:
        out.write(file.file.read())
    return f"/assets/uploads/{fname}"

# --- Public API ---
@app.get("/api/releases.json")
def api_releases(db=Depends(get_db)):
    items = db.query(ReleaseNote).order_by(ReleaseNote.release_date.desc(), ReleaseNote.id.desc()).all()
    out = []
    for x in items:
        if not x.is_published:
            continue
        # optional software name
        name = None
        try:
            if x.software_id:
                s = db.query(Software).get(x.software_id)
                name = s.name if s else None
        except Exception:
            name = None
        out.append({
            "id": x.id,
            "title": x.title,
            "version": x.version,
            "software_id": x.software_id,
            "software_name": name,
            "release_date": x.release_date.isoformat() if isinstance(x.release_date, datetime.datetime) else str(x.release_date),
            "content": x.content,
        })
    return {"items": out}

@app.get("/api/software.json")
def api_software(db=Depends(get_db)):
    items = db.query(Software).order_by(Software.sort_order, Software.id).all()
    return {"items":[{
        "id":x.id, "name":x.name, "slug":x.slug, "category":x.category,
        "description":x.description, "price_one_time":x.price_one_time,
        "price_yearly":x.price_yearly, "is_free":x.is_free, "is_active":x.is_active,
        "download_url":x.download_url, "payment_link_onetime":x.payment_link_onetime,
        "payment_link_yearly":x.payment_link_yearly, "image": x.image, "sort_order":x.sort_order
    } for x in items]}

# --- Admin Auth ---

@app.get("/api/known_issues.json")
def api_known_issues(db=Depends(get_db)):
    items = db.query(KnownIssue).order_by(KnownIssue.sort_order, KnownIssue.id.desc()).all()
    out = []
    for x in items:
        if not x.is_active:
            continue
        out.append({
            "id": x.id,
            "title": x.title,
            "status": x.status or "Open",
            "content": x.content or ""
        })
    return {"items": out}
@app.get("/admin")
def admin_home(request: Request):
    if not is_logged_in(request):
        return RedirectResponse(url="/admin/login", status_code=303)
    return RedirectResponse(url="/admin/software", status_code=303)

@app.get("/admin/login")
def admin_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/admin/login")
def admin_login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USER and password == ADMIN_PASSWORD:
        request.session["admin_ok"] = True
        return RedirectResponse(url="/admin/software", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

@app.get("/admin/logout")
def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/admin/login", status_code=303)

# --- Admin CRUD ---
# --- Admin: Release Notes ---
@app.get("/admin/releases")
def releases_list(request: Request, db=Depends(get_db)):
    if not is_logged_in(request): return RedirectResponse(url="/admin/login", status_code=303)
    items = db.query(ReleaseNote).order_by(ReleaseNote.release_date.desc(), ReleaseNote.id.desc()).all()
    # load software map for display
    sitems = db.query(Software).order_by(Software.name).all()
    smap = {s.id: s.name for s in sitems}
    return templates.TemplateResponse("releases_list.html", {"request": request, "items": items, "smap": smap})

@app.get("/admin/releases/new")
def releases_new(request: Request, db=Depends(get_db)):
    if not is_logged_in(request): return RedirectResponse(url="/admin/login", status_code=303)
    sitems = db.query(Software).order_by(Software.name).all()
    return templates.TemplateResponse("releases_form.html", {"request": request, "item": None, "software_items": sitems})

@app.post("/admin/releases/new")
def releases_new_post(request: Request, 
        title: str = Form(...), version: str = Form(""),
        software_id: str = Form(""), release_date: str = Form(""),
        content: str = Form(""), is_published: bool = Form(True), db=Depends(get_db)):
    if not is_logged_in(request): return RedirectResponse(url="/admin/login", status_code=303)
    # parse date
    dt = None
    try:
        dt = datetime.datetime.fromisoformat(release_date) if release_date else datetime.datetime.utcnow()
    except Exception:
        dt = datetime.datetime.utcnow()
    sid = int(software_id) if str(software_id).strip().isdigit() else None
    item = ReleaseNote(title=title, version=(version or None), software_id=sid, release_date=dt,
                       content=(content or None), is_published=is_published)
    db.add(item); db.commit()
    return RedirectResponse(url="/admin/releases", status_code=303)

@app.get("/admin/releases/{rid}/edit")
def releases_edit(request: Request, rid: int, db=Depends(get_db)):
    if not is_logged_in(request): return RedirectResponse(url="/admin/login", status_code=303)
    item = db.query(ReleaseNote).get(rid)
    if not item: raise HTTPException(404)
    sitems = db.query(Software).order_by(Software.name).all()
    return templates.TemplateResponse("releases_form.html", {"request": request, "item": item, "software_items": sitems})

@app.post("/admin/releases/{rid}/edit")
def releases_edit_post(request: Request, rid: int,
        title: str = Form(...), version: str = Form(""),
        software_id: str = Form(""), release_date: str = Form(""),
        content: str = Form(""), is_published: bool = Form(True), db=Depends(get_db)):
    if not is_logged_in(request): return RedirectResponse(url="/admin/login", status_code=303)
    item = db.query(ReleaseNote).get(rid)
    if not item: raise HTTPException(404)
    try: dt = datetime.datetime.fromisoformat(release_date) if release_date else datetime.datetime.utcnow()
    except Exception: dt = datetime.datetime.utcnow()
    sid = int(software_id) if str(software_id).strip().isdigit() else None
    item.title=title; item.version=(version or None); item.software_id=sid
    item.release_date=dt; item.content=(content or None); item.is_published=is_published
    item.updated_at = datetime.datetime.utcnow()
    db.commit()
    return RedirectResponse(url="/admin/releases", status_code=303)

@app.post("/admin/releases/{rid}/delete")
def releases_delete(request: Request, rid: int, db=Depends(get_db)):
    if not is_logged_in(request): return RedirectResponse(url="/admin/login", status_code=303)
    item = db.query(ReleaseNote).get(rid)
    if item: db.delete(item); db.commit()
    return RedirectResponse(url="/admin/releases", status_code=303)

@app.get("/admin/software")
def software_list(request: Request, db=Depends(get_db)):
    if not is_logged_in(request):
        return RedirectResponse(url="/admin/login", status_code=303)
    items = db.query(Software).order_by(Software.sort_order, Software.id).all()
    return templates.TemplateResponse("software_list.html", {"request": request, "items": items})

@app.get("/admin/software/new")
def software_new(request: Request):
    if not is_logged_in(request):
        return RedirectResponse(url="/admin/login", status_code=303)
    return templates.TemplateResponse("software_form.html", {"request": request, "item": None})

@app.post("/admin/software/new")
def software_new_post(request: Request,
                      name: str = Form(...), slug: str = Form(""), category: str = Form(""),
                      description: str = Form(""), price_one_time: str = Form(""),
                      price_yearly: str = Form(""), is_free: bool = Form(False),
                      is_active: bool = Form(True), download_url: str = Form(""),
                      payment_link_onetime: str = Form(""), payment_link_yearly: str = Form(""),
                      sort_order: int = Form(0), image_file: UploadFile = File(None),
                      db=Depends(get_db)):
    if not is_logged_in(request):
        return RedirectResponse(url="/admin/login", status_code=303)
    image_url = _save_upload(image_file)
    p1 = None if is_free else _to_int(price_one_time)
    p2 = None if is_free else _to_int(price_yearly)
    item = Software(
        name=name, slug=slug or None, category=category or None,
        description=description or None, price_one_time=p1,
        price_yearly=p2, is_free=is_free, is_active=is_active,
        download_url=(download_url or None), payment_link_onetime=(payment_link_onetime or None),
        payment_link_yearly=(payment_link_yearly or None), image=image_url, sort_order=sort_order or 0
    )
    db.add(item); db.commit()
    return RedirectResponse(url="/admin/software", status_code=303)

@app.get("/admin/software/{item_id}/edit")
def software_edit(request: Request, item_id: int, db=Depends(get_db)):
    if not is_logged_in(request):
        return RedirectResponse(url="/admin/login", status_code=303)
    item = db.query(Software).get(item_id)
    if not item:
        raise HTTPException(404)
    return templates.TemplateResponse("software_form.html", {"request": request, "item": item})

@app.post("/admin/software/{item_id}/edit")
def software_edit_post(request: Request, item_id: int,
                      name: str = Form(...), slug: str = Form(""), category: str = Form(""),
                      description: str = Form(""), price_one_time: str = Form(""),
                      price_yearly: str = Form(""), is_free: bool = Form(False),
                      is_active: bool = Form(True), download_url: str = Form(""),
                      payment_link_onetime: str = Form(""), payment_link_yearly: str = Form(""),
                      sort_order: int = Form(0), remove_image: bool = Form(False),
                      image_file: UploadFile = File(None), db=Depends(get_db)):
    if not is_logged_in(request):
        return RedirectResponse(url="/admin/login", status_code=303)
    item = db.query(Software).get(item_id)
    if not item:
        raise HTTPException(404)
    item.name=name; item.slug=slug or None; item.category=category or None
    item.description=description or None;
    item.price_one_time = None if is_free else _to_int(price_one_time)
    item.price_yearly = None if is_free else _to_int(price_yearly);
    item.is_free=is_free; item.is_active=is_active
    item.download_url=download_url or None; item.payment_link_onetime=payment_link_onetime or None
    item.payment_link_yearly=payment_link_yearly or None; item.sort_order=sort_order or 0
    # handle image
    if remove_image:
        item.image = None
    else:
        new_url = _save_upload(image_file)
        if new_url:
            item.image = new_url
    item.updated_at = datetime.datetime.utcnow()
    db.commit()
    return RedirectResponse(url="/admin/software", status_code=303)

@app.post("/admin/software/{item_id}/delete")
def software_delete(request: Request, item_id: int, db=Depends(get_db)):
    if not is_logged_in(request):
        return RedirectResponse(url="/admin/login", status_code=303)
    item = db.query(Software).get(item_id)
    if item:
        db.delete(item); db.commit()
    return RedirectResponse(url="/admin/software", status_code=303)


# --- Admin: Known Issues ---
@app.get("/admin/issues")
def issues_list(request: Request, db=Depends(get_db)):
    if not is_logged_in(request): return RedirectResponse(url="/admin/login", status_code=303)
    items = db.query(KnownIssue).order_by(KnownIssue.sort_order, KnownIssue.id.desc()).all()
    return templates.TemplateResponse("issues_list.html", {"request": request, "items": items})

@app.get("/admin/issues/new")
def issues_new(request: Request):
    if not is_logged_in(request): return RedirectResponse(url="/admin/login", status_code=303)
    return templates.TemplateResponse("issues_form.html", {"request": request, "item": None})

@app.post("/admin/issues/new")
def issues_create(request: Request, title: str = Form(...), status: str = Form("Open"),
                  content: str = Form(""), sort_order: int = Form(0), is_active: bool = Form(True),
                  db=Depends(get_db)):
    if not is_logged_in(request): return RedirectResponse(url="/admin/login", status_code=303)
    x = KnownIssue(title=title, status=status, content=content, sort_order=sort_order or 0, is_active=bool(is_active))
    db.add(x); db.commit()
    return RedirectResponse(url="/admin/issues", status_code=303)

@app.get("/admin/issues/{iid}/edit")
def issues_edit(request: Request, iid: int, db=Depends(get_db)):
    if not is_logged_in(request): return RedirectResponse(url="/admin/login", status_code=303)
    item = db.query(KnownIssue).get(iid)
    return templates.TemplateResponse("issues_form.html", {"request": request, "item": item})

@app.post("/admin/issues/{iid}/edit")
def issues_update(request: Request, iid: int, title: str = Form(...), status: str = Form("Open"),
                  content: str = Form(""), sort_order: int = Form(0), is_active: bool = Form(True),
                  db=Depends(get_db)):
    if not is_logged_in(request): return RedirectResponse(url="/admin/login", status_code=303)
    item = db.query(KnownIssue).get(iid)
    if item:
        item.title = title
        item.status = status
        item.content = content
        item.sort_order = sort_order
        item.is_active = bool(is_active)
        item.updated_at = datetime.datetime.utcnow()
        db.commit()
    return RedirectResponse(url="/admin/issues", status_code=303)

@app.post("/admin/issues/{iid}/delete")
def issues_delete(request: Request, iid: int, db=Depends(get_db)):
    if not is_logged_in(request): return RedirectResponse(url="/admin/login", status_code=303)
    item = db.query(KnownIssue).get(iid)
    if item: db.delete(item); db.commit()
    return RedirectResponse(url="/admin/issues", status_code=303)
# --- Mount static site ---

@app.post("/admin/releases/quick")
def releases_quick_post(request: Request,
        software_id: str = Form(...),
        title: str = Form(...),
        version: str = Form(""),
        release_date: str = Form(""),
        content: str = Form(""),
        is_published: bool = Form(True),
        db=Depends(get_db)):
    if not is_logged_in(request): 
        return RedirectResponse(url="/admin/login", status_code=303)
    sid = int(software_id) if str(software_id).strip().isdigit() else None
    try:
        dt = datetime.datetime.fromisoformat(release_date) if release_date else datetime.datetime.utcnow()
    except Exception:
        dt = datetime.datetime.utcnow()
    item = ReleaseNote(title=title, version=(version or None), software_id=sid,
                       release_date=dt, content=(content or None), is_published=is_published)
    db.add(item); db.commit()
    return RedirectResponse(url="/admin/software", status_code=303)



# --- Clients API ---
@app.get("/api/clients.json")
def api_clients(db=Depends(get_db)):
    items = db.query(Client).filter(Client.is_active==True).order_by(Client.sort_order.asc(), Client.id.desc()).all()
    return {"items":[{"id":x.id,"name":x.name,"industry":x.industry,"city":x.city,"website":x.website,"image":x.image,"sort_order":x.sort_order} for x in items]}

# --- Admin: Clients ---
@app.get("/admin/clients")
def clients_list(request: Request, db=Depends(get_db)):
    if not is_logged_in(request): return RedirectResponse(url="/admin/login", status_code=303)
    items = db.query(Client).order_by(Client.sort_order.asc(), Client.id.desc()).all()
    return templates.TemplateResponse("clients_list.html", {"request": request, "items": items})

@app.get("/admin/clients/new")
def clients_new(request: Request):
    if not is_logged_in(request): return RedirectResponse(url="/admin/login", status_code=303)
    return templates.TemplateResponse("clients_form.html", {"request": request, "item": None})

@app.post("/admin/clients/new")
def clients_new_post(request: Request,
                     name: str = Form(...),
                     industry: str = Form(None),
                     city: str = Form(None),
                     website: str = Form(None),
                     sort_order: int = Form(0),
                     is_active: bool = Form(False),
                     image: UploadFile = File(None),
                     db=Depends(get_db)):
    if not is_logged_in(request): return RedirectResponse(url="/admin/login", status_code=303)
    image_url = _save_upload(image)
    item = Client(name=name.strip(),
                  industry=(industry or None),
                  city=(city or None),
                  website=(website or None),
                  sort_order=sort_order or 0,
                  is_active=bool(is_active),
                  image=image_url)
    db.add(item); db.commit()
    return RedirectResponse(url="/admin/clients", status_code=303)

@app.get("/admin/clients/{item_id}/edit")
def clients_edit(request: Request, item_id: int, db=Depends(get_db)):
    if not is_logged_in(request): return RedirectResponse(url="/admin/login", status_code=303)
    item = db.query(Client).get(item_id)
    if not item: raise HTTPException(status_code=404)
    return templates.TemplateResponse("clients_form.html", {"request": request, "item": item})

@app.post("/admin/clients/{item_id}/edit")
def clients_edit_post(request: Request, item_id: int,
                      name: str = Form(...),
                      industry: str = Form(None),
                      city: str = Form(None),
                      website: str = Form(None),
                      sort_order: int = Form(0),
                      is_active: bool = Form(False),
                      image: UploadFile = File(None),
                      db=Depends(get_db)):
    if not is_logged_in(request): return RedirectResponse(url="/admin/login", status_code=303)
    item = db.query(Client).get(item_id)
    if not item: raise HTTPException(404)
    image_url = _save_upload(image) or item.image
    item.name = name.strip()
    item.industry = (industry or None)
    item.city = (city or None)
    item.website = (website or None)
    item.sort_order = sort_order or 0
    item.is_active = bool(is_active)
    item.image = image_url
    item.updated_at = datetime.datetime.utcnow()
    db.commit()
    return RedirectResponse(url="/admin/clients", status_code=303)

@app.post("/admin/clients/{item_id}/delete")
def clients_delete(request: Request, item_id: int, db=Depends(get_db)):
    if not is_logged_in(request): return RedirectResponse(url="/admin/login", status_code=303)
    item = db.query(Client).get(item_id)
    if item:
        db.delete(item); db.commit()
    return RedirectResponse(url="/admin/clients", status_code=303)
# --- Release Notes page (template) ---
@app.get("/releases.html")
@app.get("/releases")
def releases_page(request: Request):
    return templates.TemplateResponse("release_notes.html", {"request": request})

app.mount("/", StaticFiles(directory=SITE_DIR, html=True), name="site")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=int(os.environ.get("PORT", "8000")), reload=True)

# Seed Known Issues (only if empty)
# with engine.connect() as conn:
#     try:
#         c = conn.exec_driver_sql("SELECT COUNT(*) FROM known_issues").fetchone()[0]
#         if not c:
#             conn.exec_driver_sql("INSERT INTO known_issues (title,status,content,sort_order,is_active,created_at,updated_at) VALUES "
#                                  "('Windows 7 RDP sessions','Open','Use Windows Server or proper licensing.',0,1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),"
#                                  "('SQL 2000 restore exclusive access','Open','Close all connections and set SINGLE_USER before restore.',1,1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)")
#     except Exception as _e:
#         pass

