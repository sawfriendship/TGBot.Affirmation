import telegram
from flask import Flask, escape, request, jsonify
import os, locale, re, requests, urllib3, json
import datetime as dt
import sqlalchemy as sql
import sqlalchemy.types as sql_type
import sqlalchemy.orm as sql_orm
from pprint import pprint
from models import *

Base = sql_orm.declarative_base()
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

# ------------------------------------------------------------------

app = Flask(__name__)

@app.route('/')
async def index():
    return 'ok'

@app.route('/', methods=['GET','POST'])
async def webhook():
    if request.method.upper() != 'POST': return 'ok'
    secret = request.headers.get('X-Telegram-Bot-Api-Secret-Token','')
    if secret != SECRET: return jsonify({'error':'Incorrect Token'}), 403
    if not (j := request.get_json(force=True)) or not (isinstance(j,dict)) or not (message := j.get('message')): return 'BadJSON'
    pprint(j)
    bot = telegram.Bot(token=TOKEN)

    request_text = message.get('text','').lower()

    # kb = telegram.ReplyKeyboardMarkup([['Yes','No','HZ'],['Settings']], one_time_keyboard=True, resize_keyboard=True)
    
    message_id = message['message_id']
    chat_id = message['chat']['id']
    user_id = message['from']['id']
    is_bot = message['from']['is_bot']
    username = message['from']['username']
    first_name = message['from']['first_name']
    last_name = message['from']['last_name']

    webhook_info = await bot.get_webhook_info()
    pprint(webhook_info)
    responce_param = dict(text='null',chat_id=chat_id)
    with sql_orm.Session(bind=DB_ENGINE) as session:
        if request_text:
            session.begin()
            user = session.query(User).filter(User.id==user_id).first()
            if not user:
                user = User(id=user_id,username=username,is_bot=is_bot,first_name=first_name,last_name=last_name)
                session.add(user)
                session.commit()
            new_request = Request(username=username,chat_id=chat_id,message_id=message_id,text=request_text)
            session.add(new_request)
                
            if request_text in ['настроить']:
                kb = telegram.ReplyKeyboardMarkup([['Я мужчина','Я женищина'],['Я взрослый(ая)','Я не взрослый(ая)'],['Я приличный(ая)','Я неприличный(ая)'],['Назад']], one_time_keyboard=False, resize_keyboard=True)
                responce_param.update({'text':'Настройка','reply_markup':kb})
            elif request_text in ['я мужчина','я женищина','я взрослый(ая)','я не взрослый(ая)','я неприличный','я неприличный(ая)']:
                if request_text in ['я мужчина','я женищина']:
                    user.sex = {'я мужчина':True,'я женищина':False}[request_text]
                elif request_text in ['я взрослый(ая)','я не взрослый(ая)']:
                    user.adult = {'я взрослый(ая)':True,'я не взрослый(ая)':False}[request_text]
                elif request_text in ['я приличный(ая)','я неприличный(ая)']:
                    user.obscene = {'я приличный(ая)':False,'я неприличный(ая)':True}[request_text]
                kb = telegram.ReplyKeyboardMarkup([['Я плачу','Настроить']], one_time_keyboard=False, resize_keyboard=True)
                responce_param.update({'text':'Ok','reply_markup':kb})
                session.merge(user)
            elif  request_text == 'назад':
                kb = telegram.ReplyKeyboardMarkup([['Я плачу','Настроить']], one_time_keyboard=False, resize_keyboard=True)
                responce_param.update({'text':'Не плачь, жми на кнопку','reply_markup':kb})
            elif request_text == 'я плачу':
                kb = telegram.ReplyKeyboardMarkup([['Я плачу','Настроить']], one_time_keyboard=False, resize_keyboard=True)
                # responce_log = session.query(Responce).all()
                # top_affirmations = session.query(Affirmation.id,sql.func.count(Responce.id)).outerjoin(Responce,Affirmation.id==Responce.affirmation_id,full=True).filter(sql.and_(Responce.user_id==user_id,Affirmation.sex==user.sex,Affirmation.adult==user.adult,Affirmation.obscene==user.obscene)).group_by(Affirmation.id).order_by(sql.func.count(Responce.id).asc()).all()
                top_affirmations = session.query(Affirmation.id,sql.func.count(Responce.id)).outerjoin(Responce,Affirmation.id==Responce.affirmation_id,full=True).filter(sql.and_(Responce.user_id==user_id)).group_by(Affirmation.id).order_by(sql.func.count(Responce.id).asc()).all()
                if top_affirmations:
                    top_affirmation = top_affirmations[0][0]
                else:
                    top_affirmation = session.query(Affirmation.id).filter(sql.and_(Affirmation.sex==user.sex)).first()[0]
                    # top_affirmation = session.query(Affirmation.id).filter(sql.and_(Affirmation.sex==user.sex,Affirmation.adult==user.adult,Affirmation.obscene==user.obscene)).first()[0]
                affirmation = session.query(Affirmation).filter(Affirmation.id==top_affirmation).first()
                responce = Responce(user_id=user_id,chat_id=chat_id,affirmation_id=affirmation.id)
                session.add(responce)
                responce_param.update({'text':affirmation.text,'reply_markup':kb})
            session.commit()
        else:
            kb = telegram.ReplyKeyboardMarkup([['Я плачу','Настроить']], one_time_keyboard=False, resize_keyboard=True)
            responce_param.update({'text':'Я тоже так умею, но ты давай-ка по клаве лучше клацай','reply_markup':kb})
        

    await bot.send_message(**responce_param)

    return 'ok'

@app.get('/getWebhook')
@app.get('/getWebhookInfo')
async def getWebhookInfo():
    bot = telegram.Bot(token=TOKEN)
    r = await bot.get_webhook_info()
    return jsonify(r.to_dict())

@app.get('/setWebhook')
async def setWebhook():
    kwargs = dict(request.args)
    bot = telegram.Bot(token=TOKEN)
    r = await bot.set_webhook(**kwargs, url=WEBHOOK, secret_token=SECRET, certificate='cert.pem')
    return jsonify({'success':r})
