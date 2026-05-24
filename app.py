import os, datetime, requests, uuid
from flask import Flask, request, redirect, render_template, make_response, url_for, flash, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "temporary_secret_key_string")
TERMUX_API_BASE = os.environ.get("TERMUX_API_URL", "https://trycloudflare.com")

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if not os.path.exists(UPLOAD_FOLDER): os.makedirs(UPLOAD_FOLDER)

TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "chunks_tmp")
if not os.path.exists(TEMP_DIR): os.makedirs(TEMP_DIR)

get_image_upload_count = lambda: int(request.cookies.get('img_upload_count', 0))

# 🛠️ クッキーから保存された名前を読み出すヘルパー関数（なければデフォルトは「名無しさん」）
get_login_user = lambda: request.cookies.get('login_user', '名無しさん')

@app.route('/')
def index():
    try: res = requests.get(f"{TERMUX_API_BASE}/api/classes", timeout=10).json()
    except: res = {}
    return render_template('menu.html', items=res.get("classes", []), login_user=get_login_user())

# 🛠️ 【追加機能】入力された新しい名前をCookieに30日間保存するルート
@app.route('/change_name', methods=['POST'])
def change_name():
    new_name = request.form.get('username', '名無しさん')
    resp = make_response(redirect('/'))
    resp.set_cookie('login_user', new_name, max_age=60*60*24*30)
    return resp

@app.route('/c/new_class', methods=['POST'])
def new_class():
    name = request.form.get('cname')
    if name:
        try: requests.post(f"{TERMUX_API_BASE}/api/classes", json={"name": name}, timeout=10)
        except: flash("クラス追加エラー")
    return redirect('/')

@app.route('/c/<int:cid>/delete', methods=['POST'])
def del_class(cid):
    try: requests.post(f"{TERMUX_API_BASE}/api/del_class", json={"cid": cid}, timeout=10)
    except: flash("クラス削除エラー")
    return redirect('/')

@app.route('/c/jump_by_id', methods=['POST'])
def jump_by_id():
    raw_id = request.form.get('five_id', '')
    try:
        cid = int(raw_id)
        return redirect(f'/c/{cid}')
    except:
        flash("正しいIDを入力してください")
        return redirect('/')

@app.route('/view_image')
def view_image():
    fname = request.args.get('f', '')
    return render_template('img.html', img_path=f"/static/{fname}")
@app.route('/c/<int:cid>')
def v_class(cid):
    try: res = requests.get(f"{TERMUX_API_BASE}/api/class/{cid}", timeout=10).json()
    except: res = {}
    if not res.get("success"):
        flash("指定されたクラス（板）が見つかりません。")
        return redirect('/')
    c_info = res.get("class", {})
    cname = c_info.get("name", "名称不明") if isinstance(c_info, list) and len(c_info) > 0 else c_info.get("name", "名称不明")
    return render_template('board.html', v='class', cid=cid, cname=cname, items=res.get("threads", []), vlist=request.cookies.get('vlist', '').split(','), login_user=get_login_user())

@app.route('/c/<int:cid>/create_form')
def create_form(cid): return render_template('board.html', v='create_form', cid=cid, login_user=get_login_user())

@app.route('/c/<int:cid>/new', methods=['POST'])
def new_t(cid):
    t, b = request.form.get('t'), request.form.get('b')
    if t and b:
        try:
            res = requests.post(f"{TERMUX_API_BASE}/api/threads", json={"class_id": cid, "title": t, "body": b, "n": get_login_user(), "d": datetime.datetime.now().strftime('%m/%d %H:%M')}, timeout=10).json()
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
    try: res = requests.get(f"{TERMUX_API_BASE}/api/thread/{tid}", timeout=10).json()
    except: res = {}
    th = res.get("thread", [])
    tname = "不明"
    if isinstance(th, list) and len(th) > 0:
        first_item = th
        if isinstance(first_item, dict): tname = first_item.get('title', '不明')
    elif isinstance(th, dict): tname = th.get('title', '不明')
    return render_template('board.html', v='thread', cid=cid, tid=tid, tname=tname, items=res.get("posts", []), login_user=get_login_user(), count=get_image_upload_count())

@app.route('/c/<int:cid>/t/<int:tid>/post_form')
def post_form(cid, tid):
    try: res = requests.get(f"{TERMUX_API_BASE}/api/thread/{tid}", timeout=10).json()
    except: res = {}
    th = res.get("thread", [])
    tname = "不明"
    if isinstance(th, list) and len(th) > 0:
        first_item = th
        if isinstance(first_item, dict): tname = first_item.get('title', '不明')
    elif isinstance(th, dict): tname = th.get('title', '不明')
    return render_template('board.html', v='post_form', cid=cid, tid=tid, tname=tname, login_user=get_login_user(), count=get_image_upload_count())

@app.route('/c/<int:cid>/t/<int:tid>/p', methods=['POST'])
def post(cid, tid):
    try: requests.post(f"{TERMUX_API_BASE}/api/posts", json={'name': request.form.get('name', get_login_user()), 'message': request.form.get('b', ''), 'thread_id': tid, 'd': datetime.datetime.now().strftime('%m/%d %H:%M')}, timeout=10)
    except: flash("投稿エラー")
    return redirect(url_for('v_thread', cid=cid, tid=tid))

@app.route('/c/<int:cid>/t/<int:tid>/p_chunk', methods=['POST'])
def post_chunk(cid, tid):
    cnt = get_image_upload_count()
    if cnt >= 5: return "本日の画像アップロード上限（5回）に達しました。", 400
    f = request.files.get('image_chunk')
    if not f: return "No chunk file", 400
    dt = {'upload_id': request.form.get('upload_id'), 'chunk_index': request.form.get('chunk_index'), 'total_chunks': request.form.get('total_chunks'), 'filename': request.form.get('filename'), 'content_type': request.form.get('content_type'), 'thread_id': tid, 'd': datetime.datetime.now().strftime('%m/%d %H:%M'), 'name': request.form.get('name', get_login_user()), 'message': request.form.get('message', '')}
    try:
        ctype = f.content_type if hasattr(f, 'content_type') else 'image/jpeg'
        api_res = requests.post(f"{TERMUX_API_BASE}/api/posts_chunk", data=dt, files={'image_chunk': (f.filename, f.stream, ctype)}, timeout=30).json()
    except Exception as e: return f"データベースサーバーへの通信エラー: {str(e)}", 502
    if not api_res.get("success"): return "データベースサーバー側での保存に失敗しました。", 500
    resp = make_response(jsonify({"success": True}))
    if str(request.form.get('chunk_index')) == "9" and api_res.get("complete"):
        resp.set_cookie('img_upload_count', str(cnt + 1), max_age=60*60*24)
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
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
