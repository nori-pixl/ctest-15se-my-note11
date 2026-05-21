import os, random, datetime, requests, base64
from flask import Flask, render_template_string, request, redirect, url_for, make_response, flash, jsonify
app = Flask(__name__)
app.secret_key = "bbs_final_perfect_v127_ultimate"
TUNNEL_URL = "https://street-handbook-basically-lisa.trycloudflare.com"
HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>秘密の掲示板</title>
<style>body{font-family:monospace;background:#eee;padding:15px;color:#333;}.box{background:#fff;border:1px solid #ccc;padding:10px;margin:10px 0;width:95%;max-width:500px;}.post{border-bottom:1px solid #ccc;padding:10px 0;}.del-btn{background:#ffcccc;cursor:pointer;font-size:0.7em;border:1px solid #999;float:right;}.id-info{background:#e3f2fd;color:#1565c0;padding:5px;border-radius:3px;font-weight:bold;display:inline-block;margin-bottom:10px;}.nav-btn{display:inline-block;background:#e0e0e0;color:#333;text-decoration:none;padding:5px 10px;font-size:0.8em;border:1px solid #999;margin-bottom:10px;}.member-box{background:#f9f9f9;border:1px dashed #bbb;padding:8px;font-size:0.85em;color:#666;margin-bottom:15px;}.error-screen{background:#fff;border:2px solid #ff5252;padding:20px;margin:20px auto;max-width:500px;text-align:center;}.posted-img{max-width:80%;max-height:200px;display:block;margin-top:8px;border:1px solid #ccc;}</style>
{% if v == 'class' %}<script>var existingThreadIds = new Set();document.addEventListener("DOMContentLoaded", function() {var ts = document.getElementsByClassName('thread-block');for(var i=0; i<ts.length; i++) { existingThreadIds.add(ts[i].getAttribute('data-id')); }});
var checkTimer = setInterval(function(){fetch('/api_local/get_threads/{{cid}}').then(r => r.json()).then(d => {if(d.error==='not_found'){clearInterval(checkTimer);showDeleteError();return;}if(d.members){document.getElementById('member-count').innerText=d.members.length;document.getElementById('member-list').innerText=d.members.join(', ');}if(d.threads){var container = document.getElementById('threads-container');d.threads.forEach((t)=>{if(!existingThreadIds.has(String(t.id))){existingThreadIds.add(String(t.id));var li=document.createElement('li');li.className='thread-block';li.setAttribute('data-id',t.id);li.style.marginBottom='12px';li.style.fontSize='1.1em';li.innerHTML='[スレ] <a href="/c/{{cid}}/t/'+t.id+'"><b>'+t.title+'</b></a> <form method="POST" action="/del_t/{{cid}}/'+t.id+'" style="display:inline;"><input type="submit" value="削除" class="del-btn" onclick="return confirm(\\'消去しますか？\\')"></form>';container.appendChild(li);}})}});},1000);function showDeleteError(){document.body.innerHTML='<div class="error-screen"><h2 style="color:#ff5252;margin-top:0;">error:404 notfound ページが見つかりません。</h2><p><b>なぜこれが表示されてますか?</b></p><p>作成主が削除した可能性があります。</p><p>作成主に連絡を推奨します。</p><br><a href="/" class="nav-btn" style="background:#2196f3;color:#fff;border:none;padding:10px 20px;">ホームにもどる</a></div>';}</script>{% endif %}
{% if v == 'thread' %}<script>var existingPostIds = new Set();document.addEventListener("DOMContentLoaded", function() {var ps = document.getElementsByClassName('post-block');for(var i=0; i<ps.length; i++) { existingPostIds.add(ps[i].getAttribute('data-id')); }});
var checkTimer = setInterval(function(){fetch('/api_local/get_posts/{{cid}}/{{tid}}').then(r => r.json()).then(d => {if(d.error==='not_found'){clearInterval(checkTimer);showDeleteError();return;}if(d.members){document.getElementById('member-count').innerText=d.members.length;document.getElementById('member-list').innerText=d.members.join(', ');}if(d.posts){var container = document.getElementById('posts-container');var currentCount = container.getElementsByClassName('post-block').length;d.posts.forEach((p, index)=>{if(!existingPostIds.has(String(p.id))){existingPostIds.add(String(p.id));currentCount++;var div=document.createElement('div');div.className='post post-block';div.setAttribute('data-id',p.id);var imgHtml = p.img ? '<img src="'+p.img+'" class="posted-img">' : '';div.innerHTML=currentCount+': <b>'+p.n+'</b> ['+p.d+'] <a href="/c/{{cid}}/t/{{tid}}/post_form?r='+currentCount+'">[返信]</a> <form method="POST" action="/del_p/{{cid}}/{{tid}}/'+p.id+'" style="display:inline;"><input type="submit" value="消" class="del-btn"></form><br><div style="white-space:pre-wrap;margin-left:10px;margin-top:5px;font-size:1.1em;">'+p.b+'</div>'+imgHtml;container.appendChild(div);}})}});},1000);function showDeleteError(){document.body.innerHTML='<div class="error-screen"><h2 style="color:#ff5252;margin-top:0;">error:404 notfound ページが見つかりません。</h2><p><b>なぜこれが表示されてますか?</b></p><p>作成主が削除した可能性があります。</p><p>作成主に連絡を推奨します。</p><br><a href="/" class="nav-btn" style="background:#2196f3;color:#fff;border:none;padding:10px 20px;">ホームにもどる</a></div>';}</script>{% endif %}
</head><body><h1><a href="/">秘密の掲示板</a></h1>{% if login_user %}<div style="text-align:right;font-size:0.8em;">ログイン中: <b>{{login_user}}</b> | <a href="/logout">[ ログアウト ]</a></div>{% endif %}<hr>
{% with msgs = get_flashed_messages() %}{% for m in msgs %}<p style="color:red;">{{m}}</p>{% endfor %}{% endwith %}
{% if v == 'login' %}<h2>[ ログイン ]</h2><div class="box"><form method="POST" action="/login">ユーザーID:<br><input name="uid" required style="width:90%;"><br><br>パスワード:<br><input type="password" name="pw" required style="width:90%;"><br><br><input type="submit" value="ログイン"></form></div><p><a href="/register_form">[ 新規アカウント作成はこちら ]</a></p>
{% elif v == 'register' %}<h2>[ 新規アカウント作成 ]</h2><div class="box" style="border:2px solid #4caf50;"><form method="POST" action="/register">お好きなユーザーID:<br><input name="uid" required style="width:90%;"><br><br>表示されるお名前:<br><input name="un" value="名無し" required style="width:90%;"><br><br>パスワード:<br><input type="password" name="pw" required style="width:90%;"><br><br><input type="submit" value="アカウントを作成する"></form></div><p><a href="/login_form">[ ログイン画面に戻る ]</a></p>
{% elif v == 'menu' %}<h2>表示中のクラス</h2><ul>{% for c in items %}<li style="margin-bottom:12px;"><a href="/c/{{c.id}}"><b>{{c.name}}</b></a>{% if c.id != '1' and c.id != 1 %}<form method="POST" action="/remove_from_list/{{c.id}}" style="display:inline;margin-left:10px;"><input type="submit" value="非表示" style="font-size:0.7em;"></form>{% endif %}</li>{% endfor %}</ul><hr><div class="box"><h3>クラスを呼び出す(5桁ID)</h3><form method="POST" action="/find_class"><input name="fid" required style="width:80px;"> <input type="submit" value="追加"></form></div><div class="box"><h3>新クラス作成</h3><form method="POST" action="/add_c"><input name="cn" required placeholder="クラス名"> <input type="submit" value="作成"></form></div>
{% elif v == 'class' %}<div class="id-info">このクラスのID: {{cid}}</div><br><h2>クラス: {{cname}}</h2><div class="member-box">[ 参加メンバー / 合計 <span id="member-count">{{ members|length }}</span>人 ]<br><span id="member-list">{% for m in members %}<b>{{m}}</b>{% if not loop.last %}, {% endif %}{% else %}まだ登録メンバーはいません{% endfor %}</span></div><a href="/" class="nav-btn">[ メニューに戻る ]</a><a href="/c/{{cid}}/create_form" class="nav-btn" style="background:#ccffcc;margin-left:10px;">[ 新規スレ作成画面へ ]</a><hr><h3>スレ一覧 (自動追加モード)</h3><ul id="threads-container">{% for t in items %}<li class="thread-block" data-id="{{t.id}}" style="margin-bottom:12px;font-size:1.1em;">[スレ] <a href="/c/{{cid}}/t/{{t.id}}"><b>{{t.title}}</b></a> <form method="POST" action="/del_t/{{cid}}/{{t.id}}" style="display:inline;"><input type="submit" value="削除" class="del-btn" onclick="return confirm('消去しますか？')"></form></li>{% endfor %}</ul>
{% if cid|string != '1' and cid|int != 1 %}<hr><form method="POST" action="/del_c/{{cid}}"><input type="submit" value="このクラスを完全に削除する" class="del-btn" style="float:none; background:#ff5252; color:white; border:none; padding:5px 10px;" onclick="return confirm('全データが消えますが本当によろしいですか？')"></form>{% endif %}
{% elif v == 'create_form' %}<h2>新規スレッド作成</h2><a href="/c/{{cid}}" class="nav-btn">[ スレ一覧に戻る ]</a><hr><div class="box" style="border:2px solid #4caf50;"><form method="POST" action="/c/{{cid}}/new"><b>タイトル:</b><br><input name="t" required style="width:95%;padding:5px;"><br><br><b>最初の本文:</b><br><textarea name="b" required style="width:95%;height:100px;padding:5px;"></textarea><br><br><input type="submit" value="この内容でスレッドを作成する" style="padding:10px;font-weight:bold;cursor:pointer;"></form></div>
{% elif v == 'thread' %}<div class="id-info">クラスID: {{cid}}</div><br><h2>スレッド: {{tname}}</h2><div class="member-box">[ 参加メンバー / 合計 <span id="member-count">{{ members|length }}</span>人 ]<br><span id="member-list">{% for m in members %}<b>{{m}}</b>{% if not loop.last %}, {% endif %}{% else %}まだ登録メンバーはいません{% endfor %}</span></div><a href="/c/{{cid}}" class="nav-btn">[ スレ一覧に戻る ]</a><a href="/c/{{cid}}/t/{{tid}}/post_form" class="nav-btn" style="background:#cce6ff;margin-left:10px;">[ このスレに書き込む ]</a><hr><h3>投稿一覧 (自動追加モード)</h3><div id="posts-container">{% for p in items %}<div class="post post-block" data-id="{{p.id}}">{{loop.index}}: <b>{{p.n}}</b> [{{p.d}}] <form method="POST" action="/del_p/{{cid}}/{{tid}}/{{p.id}}" style="display:inline;"><input type="submit" value="消" class="del-btn"></form><br><div style="white-space:pre-wrap;margin-left:10px;margin-top:5px;font-size:1.1em;">{{p.b}}</div>{% if p.img %}<img src="{{p.img}}" class="posted-img">{% endif %}</div>{% endfor %}</div>
{% elif v == 'post_form' %}<h2>コメント書き込み</h2><a href="/c/{{cid}}/t/{{tid}}" class="nav-btn">[ スレに戻る ]</a><hr><div class="box" style="border:2px solid #2196f3;"><h4>スレ「{{tname}}」への返信</h4><form method="POST" action="/c/{{cid}}/t/{{tid}}/p" enctype="multipart/form-data"><b>コメント本文:</b><br><textarea name="b" required style="width:95%;height:120px;padding:5px;"></textarea><br><br><b>画像貼り付け (任意):</b><br><input type="file" name="f" accept="image/*"><br><br><input type="submit" value="書き込みを送信する" style="padding:10px;font-weight:bold;cursor:pointer;"></form></div>{% endif %}
</body></html>
"""
def remote_api(endpoint, payload):
    try:
        r = requests.post(f"{TUNNEL_URL}/{endpoint}", json=payload, timeout=5)
        return r.json()
    except: return {}
def clean_str(val):
    if not val: return ""
    v = str(val)
    for c in ["(", ")", "'", ",", "[", "]", '"']: v = v.replace(c, "")
    return v.strip()
def parse_item(data):
    # 💡 辞書型・リスト型のどちらでデータが届いても、100%安全に文字データを救出するハイブリッドパーサー
    if isinstance(data, dict): return data
    if isinstance(data, list):
        if len(data) >= 5: return {"id": clean_str(data[0]), "n": clean_str(data[1]), "b": clean_str(data[2]), "d": clean_str(data[3]), "img": str(data[4])}
        if len(data) >= 2: return {"id": clean_str(data[0]), "name": clean_str(data[1]), "title": clean_str(data[1])}
    return {}
def check_login(): return clean_str(request.cookies.get('uid')), clean_str(request.cookies.get('un'))
DELETE_COUNTER = {"date": "", "count": 0}
IMAGE_COUNTER = {"date": "", "count": 0}
def check_delete_limit():
    global DELETE_COUNTER
    t = datetime.datetime.now().strftime('%Y-%m-%d')
    if DELETE_COUNTER["date"] != t:
        DELETE_COUNTER["date"] = t
        DELETE_COUNTER["count"] = 0
    if DELETE_COUNTER["count"] >= 5: return False
    DELETE_COUNTER["count"] += 1
    return True
def check_image_limit():
    global IMAGE_COUNTER
    t = datetime.datetime.now().strftime('%Y-%m-%d')
    if IMAGE_COUNTER["date"] != t:
        IMAGE_COUNTER["date"] = t
        IMAGE_COUNTER["count"] = 0
    if IMAGE_COUNTER["count"] >= 5: return False
    IMAGE_COUNTER["count"] += 1
    return True
@app.route('/')
def index():
    uid, un = check_login()
    if not uid: return render_template_string(HTML, v='login', login_user=None)
    res = remote_api("api/get_classes", {"vlist": request.cookies.get('vlist', '1').split(',')})
    items = []
    raw_items = res.get("items", []) if isinstance(res, dict) else []
    for i in raw_items:
        parsed = parse_item(i)
        if parsed.get('id'): items.append({"id": parsed['id'], "name": parsed.get('name', '一般クラス')})
    return render_template_string(HTML, v='menu', items=items, login_user=un, new_cid=request.args.get('new_cid'))
@app.route('/login_form')
def login_form(): return render_template_string(HTML, v='login', login_user=None)
@app.route('/register_form')
def register_form(): return render_template_string(HTML, v='register', login_user=None)
@app.route('/register', methods=['POST'])
def register():
    res = remote_api("api/register", {"uid": request.form['uid'], "un": request.form['un'], "pw": request.form['pw']})
    if isinstance(res, dict) and res.get("status") == "ok":
        flash("アカウントを作成しました。ログインしてください")
        return redirect('/login_form')
    flash(res.get("message", "作成に失敗しました") if isinstance(res, dict) else "作成に失敗しました"); return redirect('/register_form')
@app.route('/login', methods=['POST'])
def login():
    res = remote_api("api/login", {"uid": request.form['uid'], "pw": request.form['pw']})
    if isinstance(res, dict) and res.get("status") == "ok":
        resp = make_response(redirect('/'))
        resp.set_cookie('uid', clean_str(res.get('uid')), max_age=60*60*24*30)
        resp.set_cookie('un', clean_str(res.get('un')), max_age=60*60*24*30)
        return resp
    flash("ユーザーIDまたはパスワードが違います"); return redirect('/login_form')
@app.route('/logout')
def logout():
    resp = make_response(redirect('/login_form')); resp.delete_cookie('uid'); resp.delete_cookie('un'); return resp
@app.route('/api_local/get_threads/<int:cid>')
def api_local_get_threads(cid):
    res = remote_api("api/get_class_detail", {"cid": cid})
    if not res or clean_str(res.get("cname")) == "不明": return jsonify({"error": "not_found"})
    threads = []
    raw_threads = res.get("threads", []) if isinstance(res, dict) else []
    for t in raw_threads:
        parsed = parse_item(t)
        if parsed.get('id'): threads.append({"id": parsed['id'], "title": parsed.get('title', '無題')})
    return jsonify({"threads": threads, "members": [clean_str(m) for m in res.get("members", [])] if isinstance(res, dict) else []})
@app.route('/api_local/get_posts/<int:cid>/<int:tid>')
def api_local_get_posts(cid, tid):
    res = remote_api("api/get_thread_detail", {"tid": tid})
    if not res or clean_str(res.get("tname")) == "不明": return jsonify({"error": "not_found"})
    posts = []
    raw_posts = res.get("posts", []) if isinstance(res, dict) else []
    for p in raw_posts:
        parsed = parse_item(p)
        if parsed.get('id'): posts.append({"id": parsed['id'], "n": parsed.get('n', '名無し'), "b": parsed.get('b', ''), "d": parsed.get('d', ''), "img": parsed.get('img', '')})
    return jsonify({"posts": posts, "members": [clean_str(m) for m in res.get("members", [])] if isinstance(res, dict) else []})
@app.route('/find_class', methods=['POST'])
def find_class():
    uid, un = check_login()
    if not uid: return redirect('/login_form')
    fid = request.form.get('fid')
    if not fid or not fid.isdigit() or str(fid) == '1': return redirect('/')
    res = remote_api("api/check_class", {"fid": fid})
    if isinstance(res, dict) and res.get("exists"):
        vlist = request.cookies.get('vlist', '1').split(',')
        if str(fid) not in vlist: vlist.append(str(fid))
        resp = make_response(redirect('/')); resp.set_cookie('vlist', ','.join(vlist), max_age=60*60*24*30); return resp
    flash("そのIDのクラスは見つかりません"); return redirect('/')
@app.route('/add_c', methods=['POST'])
def add_c():
    uid, un = check_login()
    if not uid: return redirect('/login_form')
    nid = random.randint(10000, 99999)
    remote_api("api/add_class", {"id": nid, "name": request.form['cn']})
    vlist = request.cookies.get('vlist', '1').split(',')
    vlist.append(str(nid))
    resp = make_response(redirect(url_for('index', new_cid=nid))); resp.set_cookie('vlist', ','.join(vlist), max_age=60*60*24*30); return resp
@app.route('/remove_from_list/<int:cid>', methods=['POST'])
def remove_from_list(cid):
    vlist = request.cookies.get('vlist', '1').split(',')
    if str(cid) in vlist: vlist.remove(str(cid))
    resp = make_response(redirect('/')); resp.set_cookie('vlist', ','.join(vlist), max_age=60*60*24*30); return resp
@app.route('/c/<int:cid>')
def v_class(cid):
    uid, un = check_login()
    if not uid: return redirect('/login_form')
    res = remote_api("api/get_class_detail", {"cid": cid})
    threads = []
    raw_threads = res.get("threads", []) if isinstance(res, dict) else []
    for t in raw_threads:
        parsed = parse_item(t)
        if parsed.get('id'): threads.append({"id": parsed['id'], "title": parsed.get('title', '無題')})
    return render_template_string(HTML, v='class', cid=cid, cname=clean_str(res.get("cname", "不明")) if isinstance(res, dict) else "不明", items=threads, members=[clean_str(m) for m in res.get("members", [])] if isinstance(res, dict) else [], login_user=un)
@app.route('/c/<int:cid>/create_form')
def create_form(cid):
    uid, un = check_login()
    if not uid: return redirect('/login_form')
    return render_template_string(HTML, v='create_form', cid=cid, login_user=un)
@app.route('/c/<int:cid>/new', methods=['POST'])
def new_t(cid):
    uid, un = check_login()
    if not uid: return redirect('/login_form')
    res = remote_api("api/add_thread", {"cid": cid, "title": request.form['t'], "n": un, "b": request.form['b'], "d": datetime.datetime.now().strftime('%m/%d %H:%M')})
    tid = clean_str(res.get("tid")) if isinstance(res, dict) else None
    return redirect(url_for('v_thread', cid=cid, tid=tid) if tid else url_for('v_class', cid=cid))
@app.route('/c/<int:cid>/t/<int:tid>')
def v_thread(cid, tid):
    uid, un = check_login()
    if not uid: return redirect('/login_form')
    res = remote_api("api/get_thread_detail", {"tid": tid})
    posts = []
    raw_posts = res.get("posts", []) if isinstance(res, dict) else []
    for p in raw_posts:
        parsed = parse_item(p)
        if parsed.get('id'): posts.append({"id": parsed['id'], "n": parsed.get('n', '名無し'), "b": parsed.get('b', ''), "d": parsed.get('d', ''), "img": parsed.get('img', '')})
    return render_template_string(HTML, v='thread', cid=cid, tid=tid, tname=clean_str(res.get("tname", "不明")) if isinstance(res, dict) else "不明", items=posts, members=[clean_str(m) for m in res.get("members", [])] if isinstance(res, dict) else [], login_user=un)
@app.route('/c/<int:cid>/t/<int:tid>/post_form')
def post_form(cid, tid):
    uid, un = check_login()
    if not uid: return redirect('/login_form')
    res = remote_api("api/get_thread_detail", {"tid": tid})
    return render_template_string(HTML, v='post_form', cid=cid, tid=tid, tname=clean_str(res.get("tname", "不明")) if isinstance(res, dict) else "不明", login_user=un)
@app.route('/c/<int:cid>/t/<int:tid>/p', methods=['POST'])
def post(cid, tid):
    uid, un = check_login()
    if not uid: return redirect('/login_form')
    img_b64 = ""
    f = request.files.get('f')
    if f and f.filename != '':
        if not check_image_limit():
            flash("画像のアップロードは1日合計5枚までです。")
            return redirect(url_for('v_thread', cid=cid, tid=tid))
        img_b64 = f"data:{f.content_type};base64," + base64.b64encode(f.read()).decode('utf-8')
    remote_api("api/add_post", {"tid": tid, "n": un, "b": request.form['b'], "d": datetime.datetime.now().strftime('%m/%d %H:%M'), "img": img_b64})
    return redirect(url_for('v_thread', cid=cid, tid=tid))
@app.route('/del_c/<int:cid>', methods=['POST'])
def del_c(cid):
    if not check_delete_limit():
        flash("本日の削除回数の上限(5回)に達しました。削除できません")
        return redirect('/')
    if str(cid) == '1': return redirect('/')
    remote_api("api/del_class", {"cid": cid})
    return redirect('/')
@app.route('/del_t/<int:cid>/<int:tid>', methods=['POST'])
def del_t(cid, tid):
    if not check_delete_limit():
        flash("本日の削除回数の上限(5回)に達しました。削除できません")
        return redirect(url_for('v_class', cid=cid))
    remote_api("api/del_thread", {"tid": tid}); return redirect(url_for('v_class', cid=cid))
@app.route('/del_p/<int:cid>/<int:tid>/<int:pid>', methods=['POST'])
def del_p(cid, tid, pid):
    if not check_delete_limit():
        fl
