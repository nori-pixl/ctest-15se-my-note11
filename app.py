import os, random, datetime, requests
from flask import Flask, render_template_string, request, redirect, url_for, make_response, flash, jsonify, session

app = Flask(__name__)
app.secret_key = "bbs_render_gateway_final_perfect_v96_fixed_final"

TUNNEL_URL = "https://capitol-plymouth-sheer-regulation.trycloudflare.com"

# 仮ユーザーDB（メモリ）
USERS = {}


# =========================
# 外部API
# =========================
def remote_api(endpoint, payload):
    try:
        r = requests.post(f"{TUNNEL_URL}/{endpoint}", json=payload, timeout=5)
        return r.json()
    except:
        return {"items": [], "threads": [], "posts": [], "cname": "一般クラス", "tname": "不明"}


# =========================
# メインHTML（あなたのUIそのまま）
# =========================
HTML = """（ここはあなたの元のHTMLをそのまま貼ってください。変更禁止）"""


# =========================
# ログイン・登録
# =========================
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        un = request.form['un']
        pw = request.form['pw']
        USERS[un] = pw
        return redirect('/login')
    return "<h1>register</h1>"

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        un = request.form['un']
        pw = request.form['pw']

        if USERS.get(un) == pw:
            session['user'] = un
            return redirect('/')
        return "login failed"

    return "<h1>login</h1>"

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# =========================
# ログイン強制（任意）
# =========================
@app.before_request
def auth():
    if request.endpoint in ['login', 'register', 'static']:
        return
    if 'user' not in session:
        return redirect('/login')


# =========================
# トップ
# =========================
@app.route('/')
def index():
    vlist = request.cookies.get('vlist', '1').split(',')
    res = remote_api("api/get_classes", {"vlist": vlist})

    items = [{"id": "1", "name": "一般クラス"}]
    for item in res.get("items", []):
        if isinstance(item, dict) and str(item.get('id')) != '1':
            items.append({"id": str(item['id']), "name": item['name']})

    return render_template_string(HTML, v='menu', items=items)


# =========================
# クラス表示
# =========================
@app.route('/c/<int:cid>')
def v_class(cid):
    res = remote_api("api/get_class_detail", {"cid": cid})

    threads = []
    for t in res.get("threads", []):
        threads.append({
            "id": str(t["id"]),
            "title": t.get("title", ""),
            "n": t.get("n", "名無し"),
            "d": t.get("d", "")
        })

    return render_template_string(
        HTML,
        v='class',
        cid=cid,
        cname=res.get("cname","不明"),
        items=threads
    )


# =========================
# スレッド表示
# =========================
@app.route('/c/<int:cid>/t/<int:tid>')
def v_thread(cid, tid):
    res = remote_api("api/get_thread_detail", {"tid": tid})

    posts = []
    for p in res.get("posts", []):
        if isinstance(p, list):
            posts.append({
                "id": str(p[0]),
                "n": session.get("user","名無し"),
                "b": p[2],
                "d": p[3]
            })
        else:
            posts.append({
                "id": str(p.get("id","")),
                "n": session.get("user","名無し"),
                "b": p.get("b",""),
                "d": p.get("d","")
            })

    return render_template_string(
        HTML,
        v='thread',
        cid=cid,
        tid=tid,
        tname=res.get("tname","不明"),
        items=posts
    )


# =========================
# スレ作成（名前削除→session化）
# =========================
@app.route('/c/<int:cid>/new', methods=['POST'])
def new_t(cid):
    now = datetime.datetime.now().strftime('%m/%d %H:%M')

    res = remote_api("api/add_thread", {
        "cid": cid,
        "title": request.form['t'],
        "n": session.get("user","名無し"),
        "b": request.form['b'],
        "d": now
    })

    tid = res.get("tid")
    return redirect(url_for('v_thread', cid=cid, tid=tid))


# =========================
# 投稿（名前削除→session化）
# =========================
@app.route('/c/<int:cid>/t/<int:tid>/p', methods=['POST'])
def post(cid, tid):
    now = datetime.datetime.now().strftime('%m/%d %H:%M')

    remote_api("api/add_post", {
        "tid": tid,
        "n": session.get("user","名無し"),
        "b": request.form['b'],
        "d": now
    })

    return redirect(url_for('v_thread', cid=cid, tid=tid))


# =========================
# スレ一覧リアルタイムAPI
# =========================
@app.route('/api_local/get_threads/<int:cid>')
def get_threads(cid):
    res = remote_api("api/get_class_detail", {"cid": cid})

    threads = []
    for t in res.get("threads", []):
        if isinstance(t, dict):
            threads.append({
                "id": str(t["id"]),
                "title": t.get("title",""),
                "n": t.get("n","名無し"),
                "d": t.get("d","")
            })

    return jsonify({"threads": threads})


# =========================
# 参加人数API
# =========================
@app.route('/api/members/<int:cid>')
def members(cid):
    res = remote_api("api/get_class_detail", {"cid": cid})
    return jsonify({"count": len(res.get("members", []))})


# =========================
# 起動
# =========================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
