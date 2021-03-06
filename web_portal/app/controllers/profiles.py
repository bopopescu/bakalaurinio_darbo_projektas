from flask import flash, jsonify
from flask_login import current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.forms import ProfileForm
from app.view_models import ProfilesView
from app import db
from app.models import Users

def save_user_profile(form):
    session = db.session.session_factory()  
    user = session.query(Users).filter_by(id=current_user.id).first()
    anyChanges = False

    try:        
        if (check_password_hash(user.password, form.password.data)):
            if (form.new_password.data):
                if (not check_password_hash(user.password, form.new_password.data)):
                    user.password = generate_password_hash(form.new_password.data, 'sha256')
                    anyChanges = True
                else:
                    flash('Naujas slaptažodis sutampa su senuoju! Įveskite naują slaptažodį!','danger')
                    return -1
                
            if(form.user_name.data == user.name):
                flash('Naujas naudotojo vardas sutampa su esamuoju!','danger')   
                return -1
            elif(form.user_name.data):
                user.name = form.user_name.data
                anyChanges = True            

            if(form.email.data == user.email):
                flash('Naujas naudotojo el. paštas sutampa su esamuoju!','danger')
                return -1
            elif(form.email.data):
                userWithEmail = session.query(Users).filter_by(email=form.email.data).first()

                if (userWithEmail):
                    if (userWithEmail.id != user.id):
                        user.email = form.email.data
                        anyChanges = True
                    else:
                        flash('Toks el. pašto adresas jau egzistuoja!','danger')
                        return -1
                else:
                    user.email = form.email.data
                    anyChanges = True
            

            if (anyChanges):
                session.commit()
                flash ('Pakeitimai išsaugoti!','success')
            else:
                flash ('Niekas nepakeista!','success')
        else:
            flash('Klaidingas dabartinis naudotojo slaptažodis! Įveskite slaptažodi dar kartą!','danger')
            return -1
    except Exception as ex:
        Logger.log_error(ex.args[0])
        flash('Klaidos: ' + ex.args[0],'danger')
    finally:
        session.close()

def load_user_profile():
    session = db.session.session_factory()  
    user = session.query(Users).filter_by(id=current_user.id).first()
    
    profile = ProfilesView(
            id = user.id,
            email = user.email,
            name = user.name,
            device_count = user.assigned_devices.__len__(),
            uuid = user.uuid
        )   

    session.close()    

    return profile