from fastapi import FastAPI, Request, Form, UploadFile, File, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
from datetime import datetime
from pathlib import Path
import hashlib, secrets, os

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
engine = create_engine(f"sqlite:///{BASE_DIR / 'jobtrack.db'}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    email = Column(String(160), unique=True, nullable=False)
    password_hash = Column(String(300), nullable=False)
    role = Column(String(30), default='applicant')

class Vacancy(Base):
    __tablename__ = 'vacancies'
    id = Column(Integer, primary_key=True)
    title = Column(String(160), nullable=False)
    office = Column(String(160), nullable=False)
    description = Column(Text, default='')
    requirements = Column(Text, default='')
    status = Column(String(30), default='Open')
    created_at = Column(DateTime, default=datetime.utcnow)

class Application(Base):
    __tablename__ = 'applications'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    vacancy_id = Column(Integer, ForeignKey('vacancies.id'), nullable=False)
    resume = Column(String(300), default='')
    status = Column(String(50), default='Submitted')
    notes = Column(Text, default='')
    submitted_at = Column(DateTime, default=datetime.utcnow)
    applicant = relationship('User')
    vacancy = relationship('Vacancy')

class Assignment(Base):
    __tablename__ = 'assignments'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    position = Column(String(160), default='')
    office = Column(String(160), default='')
    location = Column(String(300), default='')
    status = Column(String(50), default='Pending Assignment')
    details = Column(Text, default='')
    updated_at = Column(DateTime, default=datetime.utcnow)
    person = relationship('User')

class Announcement(Base):
    __tablename__ = 'announcements'
    id = Column(Integer, primary_key=True)
    title = Column(String(160), nullable=False)
    body = Column(Text, default='')
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)
app = FastAPI(title="JobTrack | Ormoc City JO Portal", description="Job Order vacancy, application and assignment information portal")
app.add_middleware(SessionMiddleware, secret_key=os.environ.get('JOBTRACK_SECRET', 'replace-this-development-secret-key'), same_site='lax')
app.mount('/static', StaticFiles(directory=BASE_DIR / 'static'), name='static')
app.mount('/uploads', StaticFiles(directory=UPLOAD_DIR), name='uploads')
templates = Jinja2Templates(directory=BASE_DIR / 'templates')


def db_dep():
    db = SessionLocal()
    try: yield db
    finally: db.close()

def hash_pw(password: str):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 150000).hex()
    return f"{salt}:{digest}"
def verify_pw(password: str, stored: str):
    try:
        salt, digest = stored.split(':', 1)
        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 150000).hex() == digest
    except Exception: return False

def current_user(request: Request, db: Session):
    uid = request.session.get('user_id')
    return db.get(User, uid) if uid else None

def render(request, page, **context):
    context['request'] = request
    context.setdefault('user', None)
    return templates.TemplateResponse(request=request, name=page, context=context)

def require_role(user, *roles):
    if not user or user.role not in roles:
        raise HTTPException(status_code=403, detail='You are not authorized to access this page.')

@app.get('/', response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(db_dep)):
    user = current_user(request, db)
    if user: return RedirectResponse('/dashboard', 303)
    return render(request, 'landing.html', user=None, vacancies=db.query(Vacancy).filter_by(status='Open').order_by(Vacancy.created_at.desc()).all())

@app.get('/register', response_class=HTMLResponse)
def register_page(request: Request): return render(request, 'register.html', user=None, error=None)

@app.post('/register')
def register(request: Request, name: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(db_dep)):
    email = email.strip().lower()
    if len(password) < 8: return render(request, 'register.html', user=None, error='Password must be at least 8 characters.')
    if db.query(User).filter_by(email=email).first(): return render(request, 'register.html', user=None, error='Email already registered.')
    u = User(name=name.strip(), email=email, password_hash=hash_pw(password), role='applicant')
    db.add(u); db.commit()
    request.session['user_id'] = u.id
    return RedirectResponse('/dashboard', 303)

@app.get('/login', response_class=HTMLResponse)
def login_page(request: Request): return render(request, 'login.html', user=None, error=None)

@app.post('/login')
def login(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(db_dep)):
    u = db.query(User).filter_by(email=email.strip().lower()).first()
    if not u or not verify_pw(password, u.password_hash): return render(request, 'login.html', user=None, error='Invalid email or password.')
    request.session['user_id'] = u.id
    return RedirectResponse('/dashboard', 303)

@app.get('/logout')
def logout(request: Request): request.session.clear(); return RedirectResponse('/', 303)

@app.get('/dashboard', response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(db_dep)):
    user = current_user(request, db)
    if not user: return RedirectResponse('/login', 303)
    if user.role == 'admin': return RedirectResponse('/admin', 303)
    if user.role == 'jo_personnel': return RedirectResponse('/personnel', 303)
    applications = db.query(Application).filter_by(user_id=user.id).order_by(Application.submitted_at.desc()).all()
    vacancies = db.query(Vacancy).filter_by(status='Open').order_by(Vacancy.created_at.desc()).all()
    announcements = db.query(Announcement).order_by(Announcement.created_at.desc()).limit(5).all()
    return render(request, 'applicant_dashboard.html', user=user, applications=applications, vacancies=vacancies, announcements=announcements)

@app.get('/vacancies', response_class=HTMLResponse)
def vacancies_page(request: Request, db: Session = Depends(db_dep)):
    user=current_user(request,db)
    vacancies=db.query(Vacancy).filter_by(status='Open').order_by(Vacancy.created_at.desc()).all()
    return render(request,'vacancies.html',user=user,vacancies=vacancies)

@app.post('/apply/{vacancy_id}')
def apply(vacancy_id: int, request: Request, resume: UploadFile = File(None), db: Session = Depends(db_dep)):
    user=current_user(request,db)
    if not user: return RedirectResponse('/login',303)
    require_role(user,'applicant')
    vacancy=db.get(Vacancy,vacancy_id)
    if not vacancy or vacancy.status!='Open': raise HTTPException(404,'Vacancy not found or closed')
    if db.query(Application).filter_by(user_id=user.id,vacancy_id=vacancy_id).first(): return RedirectResponse('/dashboard',303)
    filename=''
    if resume and resume.filename:
        ext=Path(resume.filename).suffix.lower()
        if ext not in ['.pdf','.doc','.docx']: raise HTTPException(400,'Upload PDF or Word documents only.')
        filename=f"{user.id}_{vacancy_id}_{secrets.token_hex(6)}{ext}"
        data=resume.file.read(5*1024*1024+1)
        if len(data)>5*1024*1024: raise HTTPException(400,'File is larger than 5 MB.')
        (UPLOAD_DIR/filename).write_bytes(data)
    db.add(Application(user_id=user.id,vacancy_id=vacancy_id,resume=filename));db.commit()
    return RedirectResponse('/dashboard',303)

@app.get('/personnel', response_class=HTMLResponse)
def personnel_page(request: Request, db: Session = Depends(db_dep)):
    user=current_user(request,db)
    if not user: return RedirectResponse('/login',303)
    require_role(user,'jo_personnel')
    assignments=db.query(Assignment).filter_by(user_id=user.id).order_by(Assignment.updated_at.desc()).all()
    announcements=db.query(Announcement).order_by(Announcement.created_at.desc()).all()
    return render(request,'personnel_dashboard.html',user=user,assignments=assignments,announcements=announcements)

@app.get('/admin', response_class=HTMLResponse)
def admin_page(request: Request, db: Session = Depends(db_dep)):
    user=current_user(request,db)
    if not user: return RedirectResponse('/login',303)
    require_role(user,'admin')
    vacancies=db.query(Vacancy).order_by(Vacancy.created_at.desc()).all()
    applications=db.query(Application).order_by(Application.submitted_at.desc()).all()
    personnel=db.query(User).filter_by(role='jo_personnel').all()
    assignments=db.query(Assignment).order_by(Assignment.updated_at.desc()).all()
    announcements=db.query(Announcement).order_by(Announcement.created_at.desc()).all()
    applicants=db.query(User).filter_by(role='applicant').all()
    return render(request,'admin_dashboard.html',user=user,vacancies=vacancies,applications=applications,personnel=personnel,assignments=assignments,announcements=announcements,applicants=applicants)

@app.post('/admin/vacancy')
def create_vacancy(request: Request, title: str=Form(...), office: str=Form(...), description: str=Form(''), requirements: str=Form(''), db: Session=Depends(db_dep)):
    user=current_user(request,db);require_role(user,'admin')
    db.add(Vacancy(title=title.strip(),office=office.strip(),description=description,requirements=requirements,status='Open'));db.commit()
    return RedirectResponse('/admin#vacancies',303)

@app.post('/admin/vacancy/{vid}/status')
def vacancy_status(vid:int,request:Request,status:str=Form(...),db:Session=Depends(db_dep)):
    user=current_user(request,db);require_role(user,'admin')
    v=db.get(Vacancy,vid)
    if v: v.status=status;db.commit()
    return RedirectResponse('/admin#vacancies',303)

@app.post('/admin/application/{aid}')
def update_application(aid:int,request:Request,status:str=Form(...),notes:str=Form(''),db:Session=Depends(db_dep)):
    user=current_user(request,db);require_role(user,'admin')
    a=db.get(Application,aid)
    if a: a.status=status;a.notes=notes;db.commit()
    return RedirectResponse('/admin#applications',303)

@app.post('/admin/assignment')
def create_assignment(request:Request,user_id:int=Form(...),position:str=Form(''),office:str=Form(''),location:str=Form(''),status:str=Form(''),details:str=Form(''),db:Session=Depends(db_dep)):
    user=current_user(request,db);require_role(user,'admin')
    target=db.get(User,user_id)
    if target and target.role in ('applicant','jo_personnel'):
        target.role='jo_personnel'
        db.add(Assignment(user_id=user_id,position=position,office=office,location=location,status=status or 'Assigned',details=details,updated_at=datetime.utcnow()))
        db.commit()
    return RedirectResponse('/admin#assignments',303)

@app.post('/admin/announcement')
def create_announcement(request:Request,title:str=Form(...),body:str=Form(...),db:Session=Depends(db_dep)):
    user=current_user(request,db);require_role(user,'admin')
    db.add(Announcement(title=title,body=body));db.commit()
    return RedirectResponse('/admin#announcements',303)

# JSON API endpoints, also visible and testable in Swagger UI.
@app.get('/api/vacancies')
def api_vacancies(db:Session=Depends(db_dep)):
    return [{'id':v.id,'title':v.title,'office':v.office,'description':v.description,'requirements':v.requirements,'status':v.status} for v in db.query(Vacancy).filter_by(status='Open').all()]
@app.get('/api/announcements')
def api_announcements(db:Session=Depends(db_dep)):
    return [{'id':a.id,'title':a.title,'body':a.body,'created_at':a.created_at.isoformat()} for a in db.query(Announcement).order_by(Announcement.created_at.desc()).all()]

# Optional initial demo data. Run `python seed.py` to create demo accounts and records.
