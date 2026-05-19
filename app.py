import os, random, datetime, requests
from flask import Flask, render_template_string, request, redirect, url_for, make_response, flash

app = Flask(__name__)
app.secret_key = "bbs_render_gateway_final_perfect_v71_divided"

# ⚠️ あなたの最新のCloudflare Tunnelの裏口URLを設定
TUNNEL_URL = "https://knitting-gender-dvds-hidden.trycloudflare.com"

HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>秘密の掲示板</title><style>
    body{font-family:monospace;background:#eee;padding:15px;color:#333;}
    .box{background:#fff;border:1px solid #ccc;padding:10px;margin:10px 0;width:95%;max-width:500px;}
    .post{border-bottom:1px solid #ccc;padding:10px 0;}
    .del-btn{background:#ffcccc;cursor:pointer;font-size:0.7em;border:1px solid #999;float:right;}
    .id-info{background:#e3f2fd; color:#1565c0; padding:5px; border-radius:3px; font-weight:bold; display:inline-block; margin-bottom:10px;}
    .nav-btn{display:inline-block;background:#e0e0e0;color:#333;text-decoration:none;padding:5px 10px;font-size:0.8em;border:1px solid #999;margin-bottom:10px;}
</style></head>
<body>
    <h1><a href="/">掲示板メニュー</a></h1><hr>
    {% with msgs = get_flashed_messages() %}{% for m in msgs %}<p style="color:red;">{{m}}</p>{% endfor %}{% endwith %}

    {# ------------------ 1. トップメニュー画面 ------------------ #}
    {% if v == 'menu' %}
        {% if new_cid %}<div class="box" style="border:2px solid #2196f3;">作成成功！このクラスのID: <b style="font-size:1.4em;">{{new_cid}}</b></div>{% endif %}
        <h2>表示中のクラス</h2>
        <ul>
        {% for c in items %}
            <li style="margin-bottom:12px;">
                <a href="/c/{{c.id}}"><b>{{c.name}}</b></a>
                {% if c.id != '1' and c.id != 1 %}
                <form method="POST" action="/remove_from_list/{{c.id}}" style="display:inline;margin-left:10px;">
                    <input type="submit" value="非表示" style="font-size:0.7em;">
                </form>
                {% endif %}
            </li>
        {% endfor %}
        </ul>
        <hr>
        <div class="box">
            <h3>クラスを呼び出す(5桁ID)</h3>
            <form method="POST" action="/find_class">
                <input name="fid" required style="width:80px;"> <input type="submit" value="追加">
            </form>
        </div>
        <div class="box">
            <h3>新クラス作成</h3>
            <form method="POST" action="/add_c">
                <input name="cn" required placeholder="クラス名"> <input type="submit" value="作成">
            </form>
        </div>

    {# ------------------ 2. スレ一覧を表示する画面 ------------------ #}
    {% elif v == 'class' %}
        <div class="id-info">このクラスのID: {{cid}}</div><br>
        <h2>クラス: {{cname}}</h2>
        <a href="/" class="nav-btn">⬅ メニューに戻る</a>
        <a href="/c/{{cid}}/create_form" class="nav-btn" style="background:#ccffcc;margin-left:10px;">➕ 新規スレ作成画面へ</a>
        <hr>
        <h3>スレ一覧</h3>
        <ul>{% for t in items %}
            <li style="margin-bottom:12px;font-size:1.1em;">
                👉 <a href="/c/{{cid}}/t/{{t.id}}"><b>{{t.title}}</b></a>
                <form method="POST" action="/del_t/{{cid}}/{{t.id}}" style="display:inline;">
                    <input type="submit" value="削除" class="del-btn" onclick="return confirm('消去しますか？')">
                </form>
            </li>
        {% endfor %}</ul>
        
        {% if cid|string != '1' and cid|int != 1 %}
        <hr><form method="POST" action="/del_c/{{cid}}">
            <input type="submit" value="このクラスを完全に削除する" class="del-btn" style="float:none; background:#ff5252; color:white; border:none; padding:5px 10px;" onclick="return confirm('全データが消えますが本当によろしいですか？')">
        </form>
        {% endif %}

    {# ------------------ 3. スレを作るための専用画面 ------------------ #}
    {% elif v == 'create_form' %}
        <h2>新規スレッド作成</h2>
        <a href="/c/{{cid}}" class="nav-btn">⬅ スレ一覧に戻る</a>
        <hr>
        <div class="box" style="border:2px solid #4caf50;">
            <form method="POST" action="/c/{{cid}}/new">
                <b>タイトル:</b><br><input name="t" required style="width:95%;padding:5px;"><br><br>
                <b>お名前:</b><br><input name="n" value="{{sn}}" style="width:95%;padding:5px;"><br><br>
                <b>最初の本文:</b><br>
                <textarea name="b" required style="width:95%;height:100px;padding:5px;"></textarea><br><br>
                <input type="submit" value="🚀 この内容でスレッドを作成する" style="padding:10px;font-weight:bold;cursor:pointer;">
            </form>
        </div>

    {# ------------------ 4. 投稿一覧を表示する専用画面 ------------------ #}
    {% elif v == 'thread' %}
        <div class="id-info">クラスID: {{cid}}</div><br>
        <h2>スレッド: {{tname}}</h2>
        <a href="/c/{{cid}}" class="nav-btn">⬅ スレ一覧に戻る</a>
        <a href="/c/{{cid}}/t/{{tid}}/post_form" class="nav-btn" style="background:#cce6ff;margin-left:10px;">✍️ このスレに書き込む</a>
        <hr>
        
        <h3>投稿一覧</h3>
        {% for p in items %}
            <div class="post">
                {{loop.index}}: <b>{{p.n}}</b> [{{p.d}}] <a href="/c/{{cid}}/t/{{tid}}/post_form?r={{loop.index}}">[返信]</a>
                <form method="POST" action="/del_p/{{cid}}/{{tid}}/{{p.id}}" style="display:inline;">
                    <input type="submit" value="消" class="del-btn">
                </form><br>
                <div style="white-space:pre-wrap;margin-left:10px;margin-top:5px;font-size:1.1em;">{{p.b}}</div>
            </div>
        {% endfor %}

    {# ------------------ 5. 【新規】コメントを書き込むための専用画面 ------------------ #}
    {% elif v == 'post_form' %}
        <h2>コメント書き込み</h2>
        <a href="/c/{{cid}}/t/{{tid}}" class="nav-btn">⬅ スレに戻る</a>
        <hr>
        <div class="box" style="border:2px solid #2196f3;">
            <h4>スレ「{{tname}}」への返信</h4>
            <form method="POST" action="/c/{{cid}}/t/{{tid}}/p">
                <b>お名前:</b><br><input name="n" value="{{sn}}" style="width:95%;padding:5px;"><br><br>
                <b>コメント本文:</b><br>
                <textarea name="b" required style="width:95%;height:120px;padding:5px;">{{r_txt}}</textarea><br><br>
                <input type="submit" value="💬 書き込みを送信する" style="padding:10px;font-weight:bold;cursor:pointer;">
            </form>
        </div>
    {% endif %}
</body></html>
"""

def remote_api(endpoint, payload):
    try:
        r = requests.post(f"{TUNNEL_URL}/{endpoint}", json=payload, timeout=5)
        return r.json()
    except:
        return {"items": [], "threads": [], "posts": [], "cname": "一般クラス", "tname": "不明"}

@app.route('/')
def index():
    vlist = request.cookies.get('vlist', '1').split(',')
    res = remote_api("api/get_classes", {"vlist": vlist})
    items = [{"id": "1", "name": "一般クラス"}]
    for item in res.get("items", []):
        try:
            if isinstance(item, dict) and str(item.get('id')) != '1':
                items.append({"id": str(item['id']), "name": str(item['name'])})
        except:
            pass
    return render_template_string(HTML, v='menu', items=items, new_cid=request.args.get('new_cid'))

@app.route('/find_class', methods=['POST'])
def find_class():
    fid = request.form.get('fid')
    if not fid or not fid.isdigit(): return redirect('/')
    if str(fid) == '1': return redirect('/')
    res = remote_api("api/check_class", {"fid": fid})
    if res.get("exists"):
        vlist = request.cookies.get('vlist', '1').split(',')
        if str(fid) not in vlist: vlist.append(str(fid))
        resp = make_response(redirect('/'))
        resp.set_cookie('vlist', ','.join(vlist), max_age=60*60*24*30)
        return resp
    flash("そのIDのクラスは見つかりません"); return redirect('/')

@app.route('/add_c', methods=['POST'])
def add_c():
    nid = random.randint(10000, 99999)
    remote_api("api/add_class", {"id": nid, "name": request.form['cn']})
    vlist = request.cookies.get('vlist', '1').split(',')
    vlist.append(str(nid))
    resp = make_response(redirect(url_for('index', new_cid=nid)))
    resp.set_cookie('vlist', ','.join(vlist), max_age=60*60*24*30); return resp

@app.route('/remove_from_list/<int:cid>', methods=['POST'])
def remove_from_list(cid):
    vlist = request.cookies.get('vlist', '1').split(',')
    if str(cid) in vlist: vlist.remove(str(cid))
    resp = make_response(redirect('/'))
    resp.set_cookie('vlist', ','.join(vlist), max_age=60*60*24*30); return resp

@app.route('/c/<int:cid>')
def v_class(cid):
    sn = request.cookies.get('un', '名無し')
    res = remote_api("api/get_class_detail", {"cid": cid})
    threads = []
    for t in res.get("threads", []):
        try:
            if isinstance(t, dict):
                threads.append({"id": str(t['id']), "title": str(t['title'])})
        except:
            pass
    cname = "一般クラス" if str(cid) == '1' else str(res.get("cname", "不明"))
    return render_template_string(HTML, v='class', cid=cid, cname=cname, items=threads, sn=sn)

@app.route('/c/<int:cid>/create_form')
def create_form(cid):
    sn = request.cookies.get('un', '名無し')
    return render_template_string(HTML, v='create_form', cid=cid, sn=sn)

@app.route('/c/<int:cid>/new', methods=['POST'])
def new_t(cid):
    now_str = datetime.datetime.now().strftime('%m/%d %H:%M')
    res = remote_api("api/add_thread", {
        "cid": cid, 
        "title": request.form['t'], 
        "n": request.form['n'], 
        "b": request.form['b'],
        "d": now_str
    })
    tid = res.get("tid")
    resp = make_response(redirect(url_for('v_thread', cid=cid, tid=tid) if tid else url_for('v_class', cid=cid)))
    resp.set_cookie('un', request.form['n']); return resp

@app.route('/c/<int:cid>/t/<int:tid>')
def v_thread(cid, tid):
    sn = request.cookies.get('un', '名無し')
    res = remote_api("api/get_thread_detail", {"tid": tid})
    posts = []
    for p in res.get("posts", []):
        try:
            if isinstance(p, dict):
                posts.append({"id": str(p.get('id', '')), "n": str(p.get('n', '名無し')), "b": str(p.get('b', '')), "d": str(p.get('d', ''))})
            elif isinstance(p, list) and len(p) >= 4:
                posts.append({"id": str(p), "n": str(p), "b": str(p), "d": str(p) if len(p)>3 else ""})
        except:
            pass
    return render_template_string(HTML, v='thread', cid=cid, tid=tid, tname=str(res.get("tname", "不明")), items=posts, sn=sn)

# 💡 コメント書き込み専用画面を表示するルーティング
@app.route('/c/<int:cid>/t/<int:tid>/post_form')
def post_form(cid, tid):
    sn = request.cookies.get('un', '名無し')
    res = remote_api("api/get_thread_detail", {"tid": tid})
    r = request.args.get("r")
    r_txt = f'>>{r}\\n' if r else ""
    return render_template_string(HTML, v='post_form', cid=cid, tid=tid, tname=str(res.get("tname", "不明")), sn=sn, r_txt=r_txt)

@app.route('/c/<int:cid>/t/<int:tid>/p', methods=['POST'])
def post(cid, tid):
    now_str = datetime.datetime.now().strftime('%m/%d %H:%M')
    remote_api("api/add_post", {
        "tid": tid, 
        "n": request.form['n'], 
        "b": request.form['b'],
        "d": now_str
    })
    resp = make_response(redirect(url_for('v_thread', cid=cid, tid=tid)))
    resp.set_cookie('un', request.form['n']); return resp

@app.route('/del_c/<int:cid>', methods=['POST'])
def del_c(cid):
    if str(cid) == '1': return redirect('/')
    remote_api("api/del_class", {"cid": cid})
    return redirect('/')

@app.route('/del_t/<int:cid>/<int:tid>', methods=['POST'])
def del_t(cid, tid):
    remote_api("api/del_thread", {"tid": tid})
    return redirect(url_for('v_class', cid=cid))

@app.route('/del_p/<int:cid>/<int:tid>/<int:pid>', methods=['POST'])
def del_p(cid, tid, pid):
    remote_api("api/del_post", {"pid": pid})
    return redirect(url_for('v_thread', cid=cid, tid=tid))

if __name__ == '__main__':
    if not os.environ.get('DATABASE_URL'):
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
