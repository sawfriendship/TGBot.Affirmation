from flask import Flask, escape, request, jsonify
import os, requests, json
import datetime as dt

with open('json.conf','r') as f:
    CONFIG = json.load(f)

TOKEN = CONFIG.get('TOKEN')

app = Flask(__name__)

@app.get('/')
def index():
    return 'TEST 1'

