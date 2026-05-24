import os, datetime, requests, uuid
from flask import Flask, request, redirect, render_template, make_response, url_for, flash, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "temporary_secret_key_string")
TERMUX_API_BASE = os.environ.get("TERMUX_API_URL", "https://trycloudflare.com")

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if not os.path.exists(UPLOAD_FOLDER): os.makedirs(UPLOAD_FOLDER)
TEMP_DIR = os.path.join(UPLOAD_FOLDER, "chunks_tmp")
if not os.path.exists(TEMP_DIR): os.makedirs(TEMP_DIR)

get_image_upload_count = lambda: int(request.cookies.get('img_upload_count', 0))
get_login_user = lambda: request.cookies.get('login_user', '名無しさん')

@app.route('/')
def index():
    try: res = requests.get(f"{TERMUX_API_BASE}/api/classes", timeout=10).json()
    except: res = {}
    return render_template('menu.html', items=res.get("classes", []), login_user=get_login_user())

@app.route('/change_name', methods=['POST'])
def change_name():
    resp = make_response(redirect('/'))
    resp.set_cookie('login_user', request.form.get('username', '名無しさん'), max_age=60*60*24*30)
    return resp

@app.route('/c/new_class', methods=['POST'])
def new_class():
    if request.form.get('cname'):
        try: requests.post(f"{TERMUX_API_BASE}/api/classes", json={"name": request.form.get('cname')}, timeout=10)
        except: flash("クラス追加エラー")
    return redirect('/')

# 🛠️ 文字列型のクラスIDに対応
@app.route('/c/<string:cid>/delete', methods=['POST'])
def del_class(cid):
    try: requests.post(f"{TERMUX_API_BASE}/api/del_class", json={"cid": str(cid)}, timeout=10)
    except: flash("クラス削除エラー")
    return redirect('/')

# 🛠️ 5桁の英数字IDをそのままの形で読み込んでクラスへリダイレクト
@app.route('/c/jump_by_id', methods=['POST'])
def jump_by_id():
    target_id = request.form.get("five_id", "").strip()
    if target_id == "00001": target_id = "1"
    if target_id: return redirect(f'/c/{target_id}')
    flash("正しいIDを入力してください"); return redirect('/')

@app.route('/view_image')
def view_image(): return render_template('img.html', img_path=f"/static/{request.args.get('f', '')}")

# 🛠️ ルーティングの引数を <string:cid> へ変更し英数字クラスIDに対応
@app.route('/c/<string:cid>')
def v_class(cid):
    try: res = requests.get(f"{TERMUX_API_BASE}/api/class/{cid}", timeout=10).json()
    except: res = {}
    if not res.get("success"): flash("指定されたクラスが見つかりません。"); return redirect('/')
    
    c_info = res.get("class", {})
    cname = c_info.get("name", "名称不明")
    return render_template('board.html', v='class', cid=cid, cname=cname, items=res.get("threads", []), vlist=request.cookies.get('vlist', '').split(','), login_user=get_login_user())

@app.route('/c/<string:cid>/create_form')
def create_form(cid): return render_template('board.html', v='create_form', cid=cid, login_user=get_login_user())

@app.route('/c/<string:cid>/new', methods=['POST'])
def new_t(cid):
    t, b = request.form.get('t'), request.form.get('b')
    if t and b:
        try:
            res = requests.post(f"{TERMUX_API_BASE}/api/threads", json={"class_id": str(cid), "title": t, "body": b, "n": get_login_user(), "d": datetime.datetime.now().strftime('%m/%d %H:%M')}, timeout=10).json()
            tid = res.get("tid")
            if tid:
                vlist = request.cookies.get('vlist', '').split(',')
                if str(tid) not in vlist: vlist.append(str(tid))
                resp = make_response(redirect(url_for('v_thread', cid=cid, tid=tid)))
                resp.set_cookie('vlist', ','.join(vlist), max_age=60*60*24*30)
                return resp
        except: flash("スレッド作成エラー")
    return redirect(url_for('v_class', cid=cid))

@app.route('/c/<string:cid>/t/<int:tid>')
def v_thread(cid, tid):
    try: res = requests.get(f"{TERMUX_API_BASE}/api/thread/{tid}", timeout=10).json()
    except: res = {}
    th_info = res.get("thread", {})
    return render_template('board.html', v='thread', cid=cid, tid=tid, tname=th_info.get('title', '不明'), items=res.get("posts", []), login_user=get_login_user(), count=get_image_upload_count())

@app.route('/c/<string:cid>/t/<int:tid>/post_form')
def post_form(cid, tid):
    try: res = requests.get(f"{TERMUX_API_BASE}/api/thread/{tid}", timeout=10).json()
    except: res = {}
    th_info = res.get("thread", {})
    return render_template('board.html', v='post_form', cid=cid, tid=tid, tname=th_info.get('title', '不明'), login_user=get_login_user(), count=get_image_upload_count())

@app.route('/c/<string:cid>/t/<int:tid>/p', methods=['POST'])
def post(cid, tid):
    try: requests.post(f"{TERMUX_API_BASE}/api/posts", json={'name': request.form.get('name', get_login_user()), 'message': request.form.get('b', ''), 'thread_id': tid, 'd': datetime.datetime.now().strftime('%m/%d %H:%M')}, timeout=10)
    except: flash("投稿エラー")
    return redirect(url_for('v_thread', cid=cid, tid=tid))

@app.route('/c/<string:cid>/t/<int:tid>/p_chunk', methods=['POST'])
def post_chunk(cid, tid):
    cnt = get_image_upload_count()
    if cnt >= 5: return "本日の画像アップロード上限（5回）に達しました。", 400
    f = request.files.get('image_chunk')
    if not f: return "No chunk file", 400
    upload_id, chunk_index, total_chunks = request.form.get('upload_id'), int(request.form.get('chunk_index', 0)), int(request.form.get('total_chunks', 10))
    f.save(os.path.join(TEMP_DIR, f"{upload_id}_{chunk_index}.part"))
    if chunk_index == total_chunks - 1:
        final_filename = f"{uuid.uuid4()}{os.path.splitext(request.form.get('filename', 'image.jpg')) or '.jpg'}"
        try:
            with open(os.path.join(UPLOAD_FOLDER, final_filename), 'wb') as outfile:
                for i in range(total_chunks):
                    part_path = os.path.join(TEMP_DIR, f"{upload_id}_{i}.part")
                    with open(part_path, 'rb') as infile: outfile.write(infile.read())
                    os.remove(part_path)
            requests.post(f"{TERMUX_API_BASE}/api/posts", json={'name': request.form.get('name', get_login_user()), 'message': request.form.get('message', ''), 'thread_id': tid, 'd': datetime.datetime.now().strftime('%m/%d %H:%M'), 'img': f"/static/{final_filename}"}, timeout=10)
        except: return "保存または通信に失敗しました。", 500
    resp = make_response(jsonify({"success": True}))
    if chunk_index == 9: resp.set_cookie('img_upload_count', str(cnt + 1), max_age=60*60*24)
    return resp

@app.route('/del_t/<string:cid>/<int:tid>', methods=['POST'])
def del_t(cid, tid):
    try: requests.post(f"{TERMUX_API_BASE}/api/del_thread", json={"tid": tid}, timeout=10)
    except: flash("削除通信エラー")
    return redirect(url_for('v_class', cid=cid))

@app.route('/del_p/<string:cid>/<int:tid>/<int:pid>', methods=['POST'])
def del_p(cid, tid, pid):
    try: requests.post(f"{TERMUX_API_BASE}/api/del_post", json={"pid": pid}, timeout=10)
    except: flash("削除通信エラー")
    return redirect(url_for('v_thread', cid=cid, tid=tid))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
