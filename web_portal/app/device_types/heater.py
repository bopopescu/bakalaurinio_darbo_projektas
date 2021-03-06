from app import db
from sqlalchemy.sql.schema import MetaData
from _datetime import datetime
from sqlalchemy.dialects.mysql import BINARY
import app.helpers.enums as enums
import app.helpers.code_decode as code_decode
from app.helpers.user_base import *
from flask import jsonify
from app.forms import DeviceConfigBaseForm
from flask_wtf import FlaskForm
from wtforms import *
from app.models import DeviceConfigBase, DeviceDataBase
import uuid as uuid
from sqlalchemy import func
from math import ceil, floor

#Kaitintuvo duomenys ir config lenta
#models
class HeaterData(DeviceDataBase):
    __tablename__ = "heater_data"
    
    temp = db.Column(db.Numeric(8,2), nullable=False)
    actuator1_state = db.Column(db.Boolean, nullable=True)
    actuator2_state = db.Column(db.Boolean, nullable=True)
    actuator3_state = db.Column(db.Boolean, nullable=True) 

    def __init__(self, device_id, temp, actuator1_state, actuator2_state, actuator3_state):
        self.temp = temp
        self.actuator1_state = actuator1_state
        self.actuator2_state = actuator2_state
        self.actuator3_state = actuator3_state
        self.device_id = device_id
        
class HeaterConfig(DeviceConfigBase):
    __tablename__ = "heater_config"
      
    temp_treshold = db.Column(db.Numeric(8,2), nullable=True)
    actuator1_state = db.Column(db.Boolean, nullable=False)
    actuator2_state = db.Column(db.Boolean, nullable=False)
    actuator3_state = db.Column(db.Boolean, nullable=False)
    
    def __init__(self, device_id, temp_treshold, actuator1_state, actuator2_state, actuator3_state, name, is_active, weekdays, start_time, duration):
        self.temp_treshold = temp_treshold
        self.actuator1_state = actuator1_state
        self.actuator2_state = actuator2_state
        self.actuator3_state = actuator3_state
        self.name = name        
        self.device_id = device_id
        self.start_time = start_time
        self.duration = duration
        self.weekdays = weekdays
        self.is_active = is_active
        self.uuid = str(uuid.uuid4())

#view models
class HeaterDataView():
    def __init__(self, id, temp, date, ch1, ch2, ch3):
        self.id = id
        self.temp = temp
        self.date = date
        self.ch1 = ch1
        self.ch2 = ch2
        self.ch3 = ch3

    @property
    def serialize(self):
        return {
            'id': self.id,
            'temp': self.temp,
            'date': self.date,
            'ch1': self.ch1,
            'ch2': self.ch2,
            'ch3': self.ch3
        }

class HeaterConfigView():
    def __init__(self, uuid, name, is_active, temp, channels, weekdays, start_time, duration, creation_date):
        self.uuid = uuid
        self.name = name
        self.is_active = is_active
        self.temp = temp
        self.channels = channels
        self.weekdays = weekdays
        self.start_time = start_time
        self.duration = duration
        self.creation_date = creation_date
        
    @property
    def serialize(self):
        return {
            'uuid': self.uuid,
            'name': self.name,
            'is_active': self.is_active,
            'temp': self.temp,
            'channels': self.channels,
            'weekdays' : self.weekdays,
            'start_time': self.start_time,
            'duration': self.duration,
            'creation_date': self.creation_date
        }

#formos, paveldim bazine klase
class HeaterConfigForm(DeviceConfigBaseForm):    
    temp_treshold = DecimalField('Maksimali temperatūra')
    channel1 = BooleanField('Pirmas kanalas')
    channel2 = BooleanField('Antras kanalas')
    channel3 = BooleanField('Trečias kanalas')

def get_config_form():
    return HeaterConfigForm()

#METODAI
def create_tables(session):
    if not table_exists("heater_config"):                 
        HeaterConfig.__table__.create(session.bind)

    if not table_exists("heater_data"):                 
        HeaterData.__table__.create(session.bind)

    if not table_exists("heater_config"):                 
        HeaterConfig.__table__.create(session.bind)

#devaisu duomenys
def get_data(session,device_id):
    data_list = session.query(HeaterData).filter_by(device_id=device_id).all() 

    data_object_list = []
    for data in data_list:
        data_object = HeaterDataView(
            id=data.id,
            ch1=str(data.actuator1_state),
            ch2=str(data.actuator2_state),
            ch3=str(data.actuator3_state),
            temp=str(data.temp) + " C°",
            date=str(data.date)
        )
        data_object_list.append(data_object)

    return jsonify({
            'data': [result.serialize for result in data_object_list]
        })

#devaisu duomenys
def get_deffered_data(session,device_id,values):
    rows_to_skip = int(values['start']) 
    rows_to_take = int(values['length']) 
    
    data_list = session.query(HeaterData).filter_by(device_id=device_id).order_by(HeaterData.id.desc()).limit(rows_to_take).offset(rows_to_skip)

    data_object_list = []
    for data in data_list:
        data_object = HeaterDataView(
            id=data.id,
            ch1=str(data.actuator1_state),
            ch2=str(data.actuator2_state),
            ch3=str(data.actuator3_state),
            temp=str(data.temp) + " C°",
            date=str(data.date)
        )
        data_object_list.append(data_object)

    row_count = get_data_count(session, device_id)
    draw = int(values['draw']) 

    return jsonify({
            'data': [result.serialize for result in data_object_list],
            'draw': draw,
            'recordsTotal': row_count,
            'recordsFiltered': row_count
        })

def get_data_range(session, device_id, date_from, date_to, resolution):
    row_count = session.query(func.count(HeaterData.id)).filter(HeaterData.date > date_from, HeaterData.date < date_to).filter_by(device_id=device_id).scalar()    
    all_data = session.query(HeaterData).filter(HeaterData.date > date_from, HeaterData.date < date_to).filter_by(device_id=device_id).all()

    data_list = []
    if (row_count > resolution):        
        skip_rows = floor(row_count/resolution)
        counter = 0
        data_sum = 0
        for item in all_data:
            counter+=1
            data_sum+=item.temp
            if (counter == skip_rows):                
                avg_item=item
                avg_item.temp=round(data_sum/counter,2)
                data_list.append(avg_item)

                counter=0
                data_sum=0
    else:
        data_list = all_data

    data_object_list = []
    for data in data_list:
        data_object = HeaterDataView(
            id=data.id,
            temp=str(data.temp),
            ch1= 1 if data.actuator1_state else 0,
            ch2= 1 if data.actuator2_state else 0,
            ch3= 1 if data.actuator3_state else 0,            
            date=str(data.date)
        )
        data_object_list.append(data_object)

    return jsonify({
            'data': [result.serialize for result in data_object_list]
        })

def get_last_data(session,device_id):
    return session.query(HeaterData).filter_by(device_id=device_id).order_by(HeaterData.date.desc()).first()

def get_data_count(session,device_id):
    return session.query(func.count(HeaterData.id)).filter_by(device_id=device_id).scalar()

#Konfigūracijos
def get_configuration_view_list(session, device_id):
    config_objects_list = []
    config_list = session.query(HeaterConfig).filter_by(device_id=device_id).all()   
    
    for config in config_list:     
        config_object = HeaterConfigView(
            uuid=config.uuid,
            name=config.name,
            is_active=enums.ConfigState(config.is_active).name if config.job_state != enums.ConfigJobState.Running.value else enums.ConfigJobState(config.job_state).name,
            temp = str(config.temp_treshold),
            channels = enums.ConfigState(config.actuator1_state).name + ' ' + enums.ConfigState(config.actuator2_state).name + ' ' + enums.ConfigState(config.actuator3_state).name,
            weekdays = code_decode.decode_weekdays(config.weekdays),
            start_time = str(config.start_time),
            duration = str(config.duration),
            creation_date = str(config.create_date)
        )
        config_objects_list.append(config_object)

    return config_objects_list

def save_configuration(session, form, device_id, config_uuid):    
    #nauja prietaiso konfiguracija
    if (config_uuid is None):
        return HeaterConfig(
            temp_treshold=form.temp_treshold.data,
            actuator1_state=form.channel1.data,
            actuator2_state=form.channel2.data,
            actuator3_state=form.channel3.data,
            name=form.config_name.data,
            is_active=form.is_active.data,
            weekdays=code_decode.code_weekdays(form),
            start_time=form.start_time.data,
            duration=form.duration.data,
            device_id=device_id
        )
    #egzistuojanti konfiguracija
    else:
        config = session.query(HeaterConfig).filter_by(uuid=config_uuid).first()

        config.temp_treshold=form.temp_treshold.data
        config.actuator1_state=form.channel1.data
        config.actuator2_state=form.channel2.data
        config.actuator3_state=form.channel3.data
        config.name=form.config_name.data
        config.is_active=form.is_active.data
        config.weekdays=code_decode.code_weekdays(form)
        config.start_time=form.start_time.data
        config.duration=form.duration.data
        config.device_id=device_id

        return config

def append_to_config_form(config, form):
    form.config_name.data = config.name
    form.temp_treshold.data = config.temp_treshold
    form.channel1.data = config.actuator1_state
    form.channel2.data = config.actuator2_state
    form.channel3.data = config.actuator3_state
    form.start_time.data = config.start_time
    form.duration.data = config.duration
    form.is_active.data = config.is_active
    form.monday.data = "0" in config.weekdays
    form.tuesday.data = "1" in config.weekdays
    form.wednesday.data = "2" in config.weekdays
    form.thursday.data = "3" in config.weekdays
    form.friday.data = "4" in config.weekdays
    form.saturday.data = "5" in config.weekdays
    form.sunday.data = "6" in config.weekdays

    return form

def get_device_config(session, device_id):
    return session.query(HeaterConfig).filter_by(device_id=device_id,is_active=True).order_by(HeaterConfig.start_time).first()

def get_device_config_uuid(session, uuid):
    return session.query(HeaterConfig).filter_by(uuid=uuid).first()

#valdymas
def form_mqtt_payload(command):    
    
    if (command == 'CH1OFF'):
        return "ACT1 OFF"
    elif (command == 'CH1ON'):
        return "ACT1 ON"
    elif (command == 'CH2OFF'):
        return "ACT2 OFF"
    elif (command == 'CH2ON'):
        return "ACT2 ON"
    elif (command == 'CH3OFF'):
        return "ACT3 OFF"
    elif (command == 'CH3ON'):
        return "ACT3 ON"
    
    if (command == 'ALLCHON'):
        return "ACT ALL ON"
    elif (command == 'ALLCHOFF'):
        return "ACT ALL OFF"

    if (command == 'STOP JOB'):
        return "ACT ALL OFF"

    return "NO ACT"


        