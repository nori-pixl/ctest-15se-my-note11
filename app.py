import os, datetime, requests, uuid, secrets, time
from flask import Flask, request, redirect, render_template, make_response, url_for, flash, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "temporary_secret_key_string")
TERMUX_API_BASE = os.environ.get("TERMUX_API_URL", "https://trycloudflare.com")

# 🛠️ 【管理者ログイン用】特定の名前とパスワード
GOD_NAME = "管理人"
GOD_PASS = "admin777"

START_TIME = time.time()

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if not os.path.exists(UPLOAD_FOLDER): os.makedirs(UPLOAD_FOLDER)
TEMP_DIR = os.path.join(UPLOAD_FOLDER, "chunks_tmp")
if not os.path.exists(TEMP_DIR): os.makedirs(TEMP_DIR)

get_image_upload_count = lambda: int(request.cookies.get('img_upload_count', 0))
get_login_user = lambda: request.cookies.get('login_user', '名無しさん')

def generate_random_hex():
    return ''.join(secrets.choice('0123456789abcdefABCDEF') for _ in range(20))

def safe_get_title(data, key_name='title'):
    if isinstance(data, list) and len(data) > 0:
        first_item = data
        if isinstance(first_item, dict): return first_item.get(key_name, '不明')
    if isinstance(data, dict): return data.get(key_name, '不明')
    return '不明'

def get_storage_size_mb():
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(UPLOAD_FOLDER):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp): total_size += os.path.getsize(fp)
    return f"{total_size / (1024 * 1024):.2f} MB"

@app.route('/')
def index():
    if not request.cookies.get('login_user'):
        return redirect('/login')
    try: res = requests.get(f"{TERMUX_API_BASE}/api/classes", timeout=10).json()
    except: res = {}
    return render_template('menu.html', items=res.get("classes", []), login_user=get_login_user())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if not username or not password:
            flash("名前とパスワードを入力してください")
            return redirect('/login')
        resp = make_response(redirect('/'))
        resp.set_cookie('login_user', username, max_age=60*60*24*30)
        if username == GOD_NAME and password == GOD_PASS:
            resp.set_cookie('hex_user_id', '00000000000000000000', max_age=60*60*24*365)
        else:
            resp.set_cookie('hex_user_id', generate_random_hex(), max_age=60*60*24*365)
        return resp
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if not username or not password:
            flash("すべての項目を入力してください")
            return redirect('/register')
        resp = make_response(redirect('/'))
        resp.set_cookie('login_user', username, max_age=60*60*24*30)
        if username == GOD_NAME and password == GOD_PASS:
            resp.set_cookie('hex_user_id', '00000000000000000000', max_age=60*60*24*365)
        else:
            resp.set_cookie('hex_user_id', generate_random_hex(), max_age=60*60*24*365)
        return resp
    return render_template('register.html')

@app.route('/logout')
def logout():
    resp = make_response(redirect('/login'))
    resp.set_cookie('login_user', '', max_age=0)
    resp.set_cookie('hex_user_id', '', max_age=0)
    return resp
# 🖥️ デベロッパー監視画面の処理（20桁16進数の神ID保持者以外は403で即座に弾く）
@app.route('/developer')
def developer_panel():
    current_hex = request.cookies.get('hex_user_id', '')
    if current_hex != "00000000000000000000":
        return render_template('403.html'), 403
        
    diff = int(time.time() - START_TIME)
    days, rem = divmod(diff, 86400)
    hours, rem = divmod(rem, 3600)
    mins, secs = divmod(rem, 60)
    uptime_str = f"{days}日 {hours}時間 {mins}分 {secs}秒"

    try: classes_res = requests.get(f"{TERMUX_API_BASE}/api/classes", timeout=10).json()
    except: classes_res = {}
    
    mock_schemas = [
        {"db_name": "board_db", "tables": ["classes", "threads", "posts"]},
        {"db_name": "information_schema", "tables": ["TABLES", "COLUMNS", "SCHEMATA"]}
    ]

    return render_template('dev.html', 
                           uptime=uptime_str,
                           storage_size=get_storage_size_mb(),
                           db_count=len(mock_schemas),
                           db_schemas=mock_schemas,
                           dev_id=current_hex,
                           classes_raw=classes_res.get("classes", []))

@app.route('/c/new_class', methods=['POST'])
def new_class():
    if request.form.get('cname'):
        try: requests.post(f"{TERMUX_API_BASE}/api/classes", json={"name": request.form.get('cname')}, timeout=10)
        except: flash("クラス追加エラー")
    return redirect('/')

@app.route('/c/<string:cid>/delete', methods=['POST'])
def del_class(cid):
    try: requests.post(f"{TERMUX_API_BASE}/api/del_class", json={"cid": str(cid)}, timeout=10)
    except: flash("クラス削除エラー")
    return redirect('/')

# 🛠️ 存在しないクラスIDが入力された際、404ではなく403画面を呼び出すように変更
@app.route('/c/jump_by_id', methods=['POST'])
def jump_by_id():
    target_id = request.form.get("five_id", "").strip()
    if target_id == "00001": target_id = "1"
    if target_id:
        try:
            # データベースサーバーにそのクラスが存在するか確認
            res = requests.get(f"{TERMUX_API_BASE}/api/class/{target_id}", timeout=10).json()
            if res.get("success") and res.get("class"):
                return redirect(f'/c/{target_id}')
        except:
            pass
    return render_template('403.html'), 403

@app.route('/view_image')
def view_image(): return render_template('img.html', img_path=f"/static/{request.args.get('f', '')}")

# 🛠️ URL直接入力などで、データベースに存在しないクラスを踏んだ場合も403画面を出す
@app.route('/c/<string:cid>')
def v_class(cid):
    try: res = requests.get(f"{TERMUX_API_BASE}/api/class/{cid}", timeout=10).json()
    except: res = {'success': False}
    
    # 未追加・存在しないクラスの場合は、404ではなく403エラー画面で弾く
    if not res.get("success") or not res.get("class"): 
        return render_template('403.html'), 403
        
    return render_template('board.html', v='class', cid=cid, cname=safe_get_title(res.get("class", {}), 'name'), items=res.get("threads", []), vlist=request.cookies.get('vlist', '').split(','), login_user=get_login_user())

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
        except: return render_template('404.html')
    return redirect(url_for('v_class', cid=cid))

@app.route('/c/<string:cid>/t/<int:tid>')
def v_thread(cid, tid):
    try: res = requests.get(f"{TERMUX_API_BASE}/api/thread/{tid}", timeout=10).json()
    except: res = {}
    return render_template('board.html', v='thread', cid=cid, tid=tid, tname=safe_get_title(res.get("thread", [])), items=res.get("posts", []), login_user=get_login_user(), count=get_image_upload_count())

@app.route('/c/<string:cid>/t/<int:tid>/post_form')
def post_form(cid, tid):
    try: res = requests.get(f"{TERMUX_API_BASE}/api/thread/{tid}", timeout=10).json()
    except: res = {}
    return render_template('board.html', v='post_form', cid=cid, tid=tid, tname=safe_get_title(res.get("thread", [])), login_user=get_login_user(), count=get_image_upload_count())

@app.route('/c/<string:cid>/t/<int:tid>/p', methods=['POST'])
def post(cid, tid):
    try: requests.post(f"{TERMUX_API_BASE}/api/posts", json={'name': request.form.get('name', get_login_user()), 'message': request.form.get('b', ''), 'thread_id': tid, 'd': datetime.datetime.now().strftime('%m/%d %H:%M')}, timeout=10)
    except: return render_template('404.html')
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
    except: return render_template('404.html')
    return redirect(url_for('v_class', cid=cid))

@app.route('/del_p/<string:cid>/<int:tid>/<int:pid>', methods=['POST'])
def del_p(cid, tid, pid):
    try: requests.post(f"{TERMUX_API_BASE}/api/del_post", json={"pid": pid}, timeout=10)
    except: return render_template('404.html')
    return redirect(url_for('v_thread', cid=cid, tid=tid))

@app.errorhandler(403)
def forbidden_error(e): return render_template('403.html'), 403

@app.errorhandler(404)
def page_not_found(e): return render_template('404.html'), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
