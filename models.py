import os, locale, re, requests, urllib3, json
import datetime as dt
import sqlalchemy as sql
import sqlalchemy.types as sql_type
import sqlalchemy.orm as sql_orm

with open('conf.json','r') as f:
    CONFIG = json.load(f)

TOKEN = CONFIG.get('TOKEN')
SECRET = CONFIG.get('SECRET')
WEBHOOK = CONFIG.get('WEBHOOK')
API_URL = f"https://api.telegram.org/bot{TOKEN}"
LOCALE = CONFIG.get('LOCALE')
DB = CONFIG.get('DB')
DB_ENGINE = sql.create_engine(DB)

Base = sql_orm.declarative_base()

class User(Base):
    __tablename__ = '_user'
    id = sql.Column(sql.BigInteger, nullable=False, unique=True, primary_key=True, autoincrement=False)
    username = sql.Column(sql.String(32), nullable=True)
    first_name = sql.Column(sql.String(32), nullable=True)
    last_name = sql.Column(sql.String(32), nullable=True)
    is_bot = sql.Column(sql.Boolean, nullable=False)
    sex = sql.Column(sql.Boolean, nullable=True)
    adult = sql.Column(sql.Boolean, nullable=True)
    obscene = sql.Column(sql.Boolean, nullable=True)

    def __repr__(self):
        return str({
            'model':__class__.__name__,
            'id': self.id,
            'username': self.username,
            'is_bot': self.is_bot,
        })

    def as_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'is_bot': self.is_bot,
            'sex': self.sex,
            'adult': self.adult,
            'obscene': self.obscene,
        }

class Affirmation(Base):
    __tablename__ = '_affirmation'
    id = sql.Column(sql.BigInteger, nullable=False, unique=True, primary_key=True, autoincrement=False)
    sex = sql.Column(sql.Boolean, nullable=True)
    adult = sql.Column(sql.Boolean, nullable=True)
    obscene = sql.Column(sql.Boolean, nullable=True)
    text = sql.Column(sql.Text, nullable=False)

    def __repr__(self):
        return str({
            'model':__class__.__name__,
            'id': self.id,
            'sex': self.sex,
            'adult': self.adult,
            'obscene': self.adult,
            'text': self.text[:20]+'...',
        })

    def as_dict(self):
        return {
            'id': self.id,
            'sex': self.sex,
            'adult': self.adult,
            'obscene': self.adult,
            'text': self.text,
        }

class Request(Base):
    __tablename__ = '_request'
    id = sql.Column(sql.BigInteger, nullable=False, unique=True, primary_key=True, autoincrement=True)
    ts = sql.Column(sql.DateTime, default=dt.datetime.now, nullable=False)
    username = sql.Column(sql.String(32), nullable=True)
    chat_id = sql.Column(sql.BigInteger, nullable=False)
    message_id = sql.Column(sql.BigInteger, nullable=False)
    text = sql.Column(sql.Text, nullable=True)

    def __repr__(self):
        return str({
            'model':__class__.__name__,
            'id': self.id,
            'username': self.username,
            'text': self.text,
        })

    def as_dict(self):
        return {
            'id': self.id,
            'ts': self.ts.isoformat(),
            'username': self.username,
            'chat_id': self.chat_id,
            'message_id': self.message_id,
            'text': self.text,
        }

class Responce(Base):
    __tablename__ = '_responce'
    id = sql.Column(sql.BigInteger, nullable=False, unique=True, primary_key=True, autoincrement=True)
    ts = sql.Column(sql.DateTime, default=dt.datetime.now, nullable=False)
    user_id = sql.Column(sql.BigInteger, nullable=False)
    chat_id = sql.Column(sql.BigInteger, nullable=False)
    affirmation_id = sql.Column(sql.BigInteger, nullable=True)

    def __repr__(self):
        return str({
            'model':__class__.__name__,
            'id': self.id,
            'ts': self.ts.isoformat(),
            'user_id': self.user_id,
            'affirmation_id': self.affirmation_id,
        })

    def as_dict(self):
        return {
            'id': self.id,
            'ts': self.ts.isoformat(),
            'user_id': self.user_id,
            'chat_id': self.chat_id,
            'affirmation_id': self.affirmation_id,
        }

Base.metadata.create_all(DB_ENGINE, checkfirst=True)
