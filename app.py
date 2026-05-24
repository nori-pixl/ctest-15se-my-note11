import os, datetime, requests, uuid
from flask import Flask, request, redirect, render_template, make_response, url_for, flash, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "temporary_secret_key_string")
TERMUX_API_BASE = os.environ.get("TERMUX_API_URL", "https://trycloudflare.com")

# 🛠️ Render内部に画像を物理保存するためのフォルダ（static）を自動作成
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if not os.path.exists(UPLOAD_FOLDER): os.makedirs(UPLOAD_FOLDER)

# 10等分のパーツを一時的に溜めておくためのゴミ箱フォルダ
TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "chunks_tmp")
if not os.path.exists(TEMP_DIR): os.makedirs(TEMP_DIR)

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

@app.route('/view_image')
def view_image():
    fname = request.args.get('f', '')
    return render_template('img.html', img_path=f"/static/{fname}")
@app.route('/c/<int:cid>/new', methods=['POST'])
def new_t(cid):
    if cid != 1: return redirect('/')
    t, b = request.form.get('t'), request.form.get('b')
    if t and b:
        try:
            res = requests.post(f"{TERMUX_API_BASE}/api/threads", json={"class_id": cid, "title": t, "body": b, "n": "名無しさん", "d": datetime.datetime.now().strftime('%m/%d %H:%M')}, timeout=10).json()
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
    th = res.get("thread", [])
    tname = "不明"
    if isinstance(th, list) and len(th) > 0:
        first_item = th[0]
        if isinstance(first_item, dict): tname = first_item.get('title', '不明')
    elif isinstance(th, dict): tname = th.get('title', '不明')
    return render_template('board.html', v='thread', cid=cid, tid=tid, tname=tname, items=res.get("posts", []), login_user="名無しさん", count=get_image_upload_count())

@app.route('/c/<int:cid>/t/<int:tid>/post_form')
def post_form(cid, tid):
    if cid != 1: return redirect('/')
    try: res = requests.get(f"{TERMUX_API_BASE}/api/thread/{tid}", timeout=10).json()
    except: res = {}
    th = res.get("thread", [])
    tname = "不明"
    if isinstance(th, list) and len(th) > 0:
        first_item = th[0]
        if isinstance(first_item, dict): tname = first_item.get('title', '不明')
    elif isinstance(th, dict): tname = th.get('title', '不明')
    return render_template('board.html', v='post_form', cid=cid, tid=tid, tname=tname, login_user="名無しさん", count=get_image_upload_count())

@app.route('/c/<int:cid>/t/<int:tid>/p', methods=['POST'])
def post(cid, tid):
    if cid != 1: return redirect('/')
    try: requests.post(f"{TERMUX_API_BASE}/api/posts", json={'name': request.form.get('name', '名無しさん'), 'message': request.form.get('b', ''), 'thread_id': tid, 'd': datetime.datetime.now().strftime('%m/%d %H:%M')}, timeout=10)
    except: flash("投稿エラー")
    return redirect(url_for('v_thread', cid=cid, tid=tid))

# 🛠️ 10分割されたパーツを、Render自身の中でファイルに組み立てる処理（データベースサーバーへ重いデータを送らない）
@app.route('/c/<int:cid>/t/<int:tid>/p_chunk', methods=['POST'])
def post_chunk(cid, tid):
    if cid != 1: return "Invalid class", 400
    cnt = get_image_upload_count()
    if cnt >= 5: return "本日の画像アップロード上限（5回）に達しました。", 400
    f = request.files.get('image_chunk')
    if not f: return "No chunk file", 400

    upload_id = request.form.get('upload_id')
    chunk_index = int(request.form.get('chunk_index', 0))
    total_chunks = int(request.form.get('total_chunks', 10))

    chunk_path = os.path.join(TEMP_DIR, f"{upload_id}_{chunk_index}.part")
    f.save(chunk_path)

    if chunk_index == total_chunks - 1:
        # タプル型（.jpg）文字バグを防ぐため、文字列処理を修正
        orig_filename = request.form.get('filename', 'image.jpg')
        ext = os.path.splitext(orig_filename)[1]
        if not ext: ext = '.jpg'
        
        final_filename = f"{uuid.uuid4()}{ext}"
        final_path = os.path.join(UPLOAD_FOLDER, final_filename)

        try:
            with open(final_path, 'wb') as outfile:
                for i in range(total_chunks):
                    part_path = os.path.join(TEMP_DIR, f"{upload_id}_{i}.part")
                    with open(part_path, 'rb') as infile: outfile.write(infile.read())
                    os.remove(part_path)
            img_url_to_save = f"/static/{final_filename}"
        except Exception as e:
            return f"Render側でのファイル結合に失敗しました: {str(e)}", 500

        # 結合完了後、軽いテキスト（画像URLの文字のみ）をデータベースサーバーへPOST送信して保存をお願いする
        try:
            requests.post(f"{TERMUX_API_BASE}/api/posts", json={
                'name': request.form.get('name', '名無しさん'),
                'message': request.form.get('message', ''),
                'thread_id': tid,
                'd': datetime.datetime.now().strftime('%m/%d %H:%M'),
                'img': img_url_to_save
            }, timeout=10)
        except Exception as e:
            return f"データベースサーバーへの通信エラー: {str(e)}", 502

    resp = make_response(jsonify({"success": True}))
    if chunk_index == 9:
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
