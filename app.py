import os, datetime, requests
from flask import Flask, request, redirect, render_template, make_response, url_for, flash, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "temporary_secret_key_string")
TERMUX_API_BASE = os.environ.get("TERMUX_API_URL", "https://trycloudflare.com")

get_image_upload_count = lambda: int(request.cookies.get('img_upload_count', 0))

@app.route('/')
def index(): return redirect('/c/1')

@app.route('/remove_from_list/<int:tid>', methods=['POST'])
def remove_from_list(tid):
    vlist = request.cookies.get('vlist', '').split(',')
    if str(tid) in vlist: vlist.remove(str(tid))
    resp = make_response(redirect('/c/1'))
    resp.set_cookie('vlist', ','.join(vlist), max_age=60*60*24*30)
    return resp

@app.route('/c/<int:cid>')
def v_class(cid):
    if cid != 1: return redirect('/')
    try: res = requests.get(f"{TERMUX_API_BASE}/api/class/{cid}", timeout=10).json()
    except: res = {}
    return render_template('board.html', v='class', cid=cid, cname=res.get("class", {}).get("name", "一般クラス"), items=res.get("threads", []), vlist=request.cookies.get('vlist', '').split(','), login_user="名無しさん")

@app.route('/c/<int:cid>/create_form')
def create_form(cid): return render_template('board.html', v='create_form', cid=cid, login_user="名無しさん")
