import telegram
from flask import Flask, escape, request, jsonify
import os, locale, re, requests, urllib3, json
import datetime as dt
import sqlalchemy as sql
import sqlalchemy.types as sql_type
import sqlalchemy.orm as sql_orm
from pprint import pprint

with open('conf.json','r') as f:
    CONFIG = json.load(f)

TOKEN = CONFIG.get('TOKEN')
SECRET = CONFIG.get('SECRET')
WEBHOOK = CONFIG.get('WEBHOOK')
API_URL = f"https://api.telegram.org/bot{TOKEN}"
LOCALE = CONFIG.get('LOCALE')
DB = CONFIG.get('DB')
DB_ENGINE = sql.create_engine(DB)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
locale.setlocale(locale.LC_ALL, LOCALE)
Base = sql_orm.declarative_base()

app = Flask(__name__)

class Request(Base):
    __tablename__ = '_request'
    id = sql.Column(sql.BigInteger, nullable=False, unique=True, primary_key=True, autoincrement=True)
    ts = sql.Column(sql.DateTime, default=dt.datetime.now, nullable=False)
    username = sql.Column(sql.String(32), nullable=True)
    chat_id = sql.Column(sql.BigInteger, nullable=False)
    message_id = sql.Column(sql.BigInteger, nullable=False)
    text = sql.Column(sql.Text, nullable=True)

    def __repr__(self):
        result = {
            'model':__class__.__name__,
            'id': self.id,
            'username': self.username,
            'text': self.text,
        }
        return str(result)
    
    def as_dict(self):
        result = {
            'id': self.id,
            'ts': self.ts.isoformat(),
            'username': self.username,
            'chat_id': self.chat_id,
            'message_id': self.message_id,
            'text': self.text,
        }
        return result

@app.route('/')
async def index():
    return 'ok'

@app.route('/', methods=['GET','POST'])
async def webhook():
    if request.method.upper() != 'POST': return 'ok'
    SECRET_HEADER = request.headers.get('X-Telegram-Bot-Api-Secret-Token','')
    if SECRET_HEADER != SECRET: return jsonify({'error':'Incorrect Token'}), 403
    if not (j := request.get_json(force=True)) or not (isinstance(j,dict)) or not (message := j.get('message')): return 'BadJSON'
    pprint(j)
    bot = telegram.Bot(token=TOKEN)

    request_text = message.get('text','').lower()

    kb = telegram.ReplyKeyboardMarkup([['Yes','No','HZ']], one_time_keyboard=True, resize_keyboard=True)

    chat_id = message['chat']['id']
    username = message['chat']['username']
    message_id = message['message_id']

    responce_param = dict(chat_id=chat_id)

    if request_text:
        new_request = Request(username=username,chat_id=chat_id,message_id=message_id,text=request_text)
        
        with sql_orm.Session(bind=DB_ENGINE) as session:
            session.begin()
            session.add(new_request)
            session.commit()
            
        if request_text not in ['yes','no','hz']:
            responce_param.update({'text':'Попутал?','reply_markup':kb})
        else:
            responces = {'yes':'Как скажешь','no':'Ну нет, так нет','hz':'Я тоже не знаю'}
            responce_param.update({'text':responces[request_text]})
    else:
        responce_param.update({'text':'Я тоже так умею, но ты давай-ка по клаве лучше клацай','reply_markup':kb})

    await bot.send_message(**responce_param)

    return 'ok'

@app.get('/getWebhook')
@app.get('/getWebhookInfo')
async def getWebhookInfo():
    try:
        responce = requests.get(url=f"{API_URL}/getWebhookInfo")
    except Exception as e:
        return jsonify({'error':str(e)})
    else:
        if responce.status_code != 200:
            return jsonify({'error':f"status_code: {responce.status_code}"})
        else:
            return jsonify(responce.json())

@app.get('/setWebhook')
async def setWebhook():
    pending_update_count = int(request.args.get('pending_update_count','0'))
    try:
        with open('cert.pem','rb') as f: cert_file_bytes = f.read()
    except Exception as e:
        return jsonify({'error':str(e)})
    else:
        try:
            data = dict(
                url = WEBHOOK,
                pending_update_count = pending_update_count,
                secret_token = SECRET
            )
            responce = requests.post(url=f"{API_URL}/setWebhook",data=data, files={'certificate': cert_file_bytes})
        except Exception as e:
            return jsonify({'error':str(e)})
        else:
            if responce.status_code != 200:
                return jsonify({'status_code':responce.status_code})
            else:
                return jsonify(responce.json())

