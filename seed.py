from main import SessionLocal, User, Vacancy, Announcement, hash_pw

db=SessionLocal()
try:
    if not db.query(User).filter_by(email='admin@jobtrack.local').first():
        db.add(User(name='JobTrack Administrator',email='admin@jobtrack.local',password_hash=hash_pw('Admin123!'),role='admin'))
    if not db.query(User).filter_by(email='personnel@jobtrack.local').first():
        db.add(User(name='JO Personnel Demo',email='personnel@jobtrack.local',password_hash=hash_pw('Personnel123!'),role='jo_personnel'))
    if not db.query(User).filter_by(email='applicant@jobtrack.local').first():
        db.add(User(name='Applicant Demo',email='applicant@jobtrack.local',password_hash=hash_pw('Applicant123!'),role='applicant'))
    if db.query(Vacancy).count()==0:
        db.add_all([
            Vacancy(title='Administrative Assistant',office='City Government Office',description='Assist with administrative tasks and office coordination.',requirements='Relevant experience; basic computer skills.',status='Open'),
            Vacancy(title='Records Support Staff',office='Records Management Office',description='Assist in organizing and maintaining records.',requirements='Attention to detail; basic computer skills.',status='Open'),
            Vacancy(title='Community Support Personnel',office='Community Services',description='Support community-facing office activities.',requirements='Good communication skills.',status='Open')])
    if db.query(Announcement).count()==0:
        db.add(Announcement(title='Welcome to JobTrack',body='Demo announcement: check the portal for vacancy and assignment updates.'))
    db.commit()
finally: db.close()
print('Demo data ready. Use demo accounts shown in README.')
