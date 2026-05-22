import os
import datetime
import requests
from flask import Flask, request, redirect, render_template, make_response, url_for, flash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "temporary_secret_key_string")
TERMUX_API_BASE = os.environ.get("TERMUX_API_URL", "https://trycloudflare.com")

def get_image_upload_count():
    return int(request.cookies.get('img_upload_count', 0))

@app.route('/')
def index():
    return redirect('/c/1')

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
def create_form(cid):
    if cid != 1: return redirect('/')
    return render_template('board.html', v='create_form', cid=cid, login_user="名無しさん")
@app.route('/c/<int:cid>/new', methods=['POST'])
def new_t(cid):
    if cid != 1: return redirect('/')
    title, body = request.form.get('t'), request.form.get('b')
    if title and body:
        try:
            res = requests.post(f"{TERMUX_API_BASE}/api/threads", json={"class_id": cid, "title": title, "body": body, "n": "名無しさん", "d": datetime.datetime.now().strftime('%m/%d %H:%M')}, timeout=10).json()
            tid = res.get("tid")
            if tid:
                vlist = request.cookies.get('vlist', '').split(',')
                if str(tid) not in vlist: vlist.append(str(tid))
                resp = make_response(redirect(url_for('v_thread', cid=cid, tid=tid)))
                resp.set_cookie('vlist', ','.join(vlist), max_age=60*60*24*30)
                return resp
        except: flash("スレッド作成エラー")
    return redirect(url_for('v_class', cid=cid))

@app.route('/c/<int:cid>/t/<int:tid>')
def v_thread(cid, tid):
    if cid != 1: return redirect('/')
    try: res = requests.get(f"{TERMUX_API_BASE}/api/thread/{tid}", timeout=10).json()
    except: res = {}
    return render_template('board.html', v='thread', cid=cid, tid=tid, tname=res.get("thread", {}).get('title', '不明') if isinstance(res.get("thread"), dict) else "不明", items=res.get("posts", []), login_user="名無しさん", count=get_image_upload_count())

@app.route('/c/<int:cid>/t/<int:tid>/post_form')
def post_form(cid, tid):
    if cid != 1: return redirect('/')
    try: res = requests.get(f"{TERMUX_API_BASE}/api/thread/{tid}", timeout=10).json()
    except: res = {}
    tname = res.get("thread", {}).get("title", "不明") if isinstance(res.get("thread"), dict) else "不明"
    return render_template('board.html', v='post_form', cid=cid, tid=tid, tname=tname, login_user="名無しさん", count=get_image_upload_count())

@app.route('/c/<int:cid>/t/<int:tid>/p', methods=['POST'])
def post(cid, tid):
    if cid != 1: return redirect('/')
    name, message, file = request.form.get('name', '名無しさん'), request.form.get('b', ''), request.files.get('image')
    upload_count, img_uploaded = get_image_upload_count(), False
    if file and file.filename != '':
        if upload_count >= 5:
            flash("画像のアップロードは1日合計5枚までです。")
            return redirect(url_for('v_thread', cid=cid, tid=tid))
        try:
            if requests.post(f"{TERMUX_API_BASE}/api/posts", data={'name': name, 'message': message, 'thread_id': tid, 'd': datetime.datetime.now().strftime('%m/%d %H:%M')}, files={'image': (file.filename, file.stream, file.content_type)}, timeout=30).json().get("success"): img_uploaded = True
        except: flash("画像転送エラー")
    else:
        try: requests.post(f"{TERMUX_API_BASE}/api/posts", json={'name': name, 'message': message, 'thread_id': tid, 'd': datetime.datetime.now().strftime('%m/%d %H:%M')}, timeout=10)
        except: flash("投稿エラー")
    resp = make_response(redirect(url_for('v_thread', cid=cid, tid=tid)))
    if img_uploaded: resp.set_cookie('img_upload_count', str(upload_count + 1), expires=datetime.datetime.combine(datetime.datetime.now().date() + datetime.timedelta(days=1), datetime.time.min))
    return resp

@app.route('/del_t/<int:cid>/<int:tid>', methods=['POST'])
def del_t(cid, tid):
    try: requests.post(f"{TERMUX_API_BASE}/api/del_thread", json={"tid": tid}, timeout=10)
    except: flash("削除通信エラー")
    return redirect(url_for('v_class', cid=cid))

@app.route('/del_p/<int:cid>/<int:tid>/<int:pid>', methods=['POST'])
def del_p(cid, tid, pid):
    try: requests.post(f"{TERMUX_API_BASE}/api/del_post", json={"pid": pid}, timeout=10)
    except: flash("削除通信エラー")
    return redirect(url_for('v_thread', cid=cid, tid=tid))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))
