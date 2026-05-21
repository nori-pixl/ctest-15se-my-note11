import os, random, datetime, requests, json
from flask import Flask, render_template_string, request, redirect, url_for, make_response, flash, jsonify, session

app = Flask(__name__)
app.secret_key = "final_bbs_key_v1"

TUNNEL_URL = "https://capitol-plymouth-sheer-regulation.trycloudflare.com"


# ---------------------------
# 仮ユーザー保存（本来DB）
# ---------------------------
USERS = {}


# ---------------------------
# API通信
# ---------------------------
def remote_api(endpoint, payload):
    try:
        r = requests.post(f"{TUNNEL_URL}/{endpoint}", json=payload, timeout=5)
        return r.json()
    except:
        return {"items": [], "threads": [], "posts": [], "cname": "一般クラス", "tname": "不明"}


# ---------------------------
# HTML
# ---------------------------
HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>mynote BBS final</title>

<style>
body{font-family:monospace;background:#eee;padding:15px;}
.box{background:#fff;padding:10px;border:1px solid #ccc;margin:10px 0;}
.post{border-bottom:1px solid #ccc;padding:8px 0;}
.thread-block{padding:6px;border-bottom:1px solid #ddd;}
.id-info{background:#e3f2fd;padding:5px;margin:5px 0;}
.del-btn{font-size:0.7em;}
</style>

<script>
function linkify(text){
    const urlRegex = /(https?:\\/\\/[^\\s]+)/g;
    return text.replace(urlRegex, url => '<a href="'+url+'" target="_blank">'+url+'</a>');
}
</script>

</head>

<body>

{% if session.user %}
<div class="box">ログイン中: <b>{{session.user}}</b> <a href="/logout">ログアウト</a></div>
{% endif %}

{% with msgs = get_flashed_messages() %}
{% for m in msgs %}
<p style="color:red;">{{m}}</p>
{% endfor %}
{% endwith %}


<!-- ================= LOGIN ================= -->
{% if v == 'login' %}
<h1>ログイン</h1>
<div class="box">
<form method="POST">
<input name="un" placeholder="ユーザー名"><br><br>
<input type="password" name="pw" placeholder="パスワード"><br><br>
<button>ログイン</button>
</form>
<a href="/register">新規作成</a>
</div>
{% endif %}


<!-- ================= REGISTER ================= -->
{% if v == 'register' %}
<h1>新規作成</h1>
<div class="box">
<form method="POST">
<input name="un" placeholder="ユーザー名"><br><br>
<input type="password" name="pw" placeholder="パスワード"><br><br>
<button>作成</button>
</form>
</div>
{% endif %}


<!-- ================= MENU ================= -->
{% if v == 'menu' %}
<h1>クラス一覧</h1>

<div class="box">
<form method="POST" action="/add_c">
<input name="cn" placeholder="クラス名">
<button>作成</button>
</form>
</div>

<ul>
{% for c in items %}
<li>
<a href="/c/{{c.id}}">{{c.name}}</a>
</li>
{% endfor %}
</ul>
{% endif %}


<!-- ================= CLASS ================= -->
{% if v == 'class' %}

<div class="id-info">
クラスID: {{cid}} ｜参加人数: <span id="mc">...</span>
</div>

<a href="/">戻る</a>

<h2>{{cname}}</h2>

<div class="box">
<form method="POST" action="/c/{{cid}}/new">
<input name="t" placeholder="スレタイトル"><br>
<textarea name="b"></textarea><br>
<button>作成</button>
</form>
</div>

<div id="thread-container">
{% for t in items %}
<div class="thread-block" data-id="{{t.id}}">
<a href="/c/{{cid}}/t/{{t.id}}">{{t.title}}</a><br>
<small>{{t.n}} ・ {{t.d}}</small>
</div>
{% endfor %}
</div>

<script>
function loadMembers(){
 fetch('/api/members/{{cid}}')
 .then(r=>r.json())
 .then(d=>{
  document.getElementById("mc").innerText = d.count;
 });
}
loadMembers();
setInterval(loadMembers,5000);
</script>

{% endif %}


<!-- ================= THREAD ================= -->
{% if v == 'thread' %}

<div class="id-info">
スレ閲覧中 ｜参加人数: <span id="mc">...</span>
</div>

<a href="/c/{{cid}}">戻る</a>

<h2>{{tname}}</h2>

<a href="/c/{{cid}}/t/{{tid}}/post_form">書き込み</a>

<div id="posts">
{% for p in items %}
<div class="post post-body">
<b>{{p.n}}</b> {{p.d}}<br>
<div class="txt">{{p.b}}</div>
</div>
{% endfor %}
</div>

<script>
function loadMembers(){
 fetch('/api/members/{{cid}}')
 .then(r=>r.json())
 .then(d=>{
  document.getElementById("mc").innerText = d.count;
 });
}
loadMembers();
setInterval(loadMembers,5000);
</script>

{% endif %}

</body>
</html>
"""


# ---------------------------
# LOGIN
# ---------------------------
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        un = request.form['un']
        pw = request.form['pw']

        if USERS.get(un) == pw:
            session['user'] = un
            return redirect('/')
        flash("失敗")
    return render_template_string(HTML, v='login')


@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        USERS[request.form['un']] = request.form['pw']
        return redirect('/login')
    return render_template_string(HTML, v='register')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# ---------------------------
# MENU
# ---------------------------
@app.route('/')
def menu():
    res = remote_api("api/get_classes", {})
    items = [{"id": str(x["id"]), "name": x["name"]} for x in res.get("items", [])]
    return render_template_string(HTML, v='menu', items=items)


# ---------------------------
# CLASS
# ---------------------------
@app.route('/c/<int:cid>')
def class_view(cid):
    res = remote_api("api/get_class_detail", {"cid": cid})

    threads = []
    for t in res.get("threads", []):
        threads.append({
            "id": str(t["id"]),
            "title": t["title"],
            "n": t.get("n","名無し"),
            "d": t.get("d","")
        })

    return render_template_string(
        HTML,
        v='class',
        cid=cid,
        cname=res.get("cname","クラス"),
        items=threads
    )


# ---------------------------
# THREAD
# ---------------------------
@app.route('/c/<int:cid>/t/<int:tid>')
def thread(cid, tid):
    res = remote_api("api/get_thread_detail", {"tid": tid})

    posts = []
    for p in res.get("posts", []):
        posts.append({
            "id": p[0] if isinstance(p,list) else p.get("id"),
            "n": session.get("user","名無し"),
            "b": p[2] if isinstance(p,list) else p.get("b"),
            "d": p[3] if isinstance(p,list) else p.get("d")
        })

    return render_template_string(HTML,
        v='thread',
        cid=cid,
        tid=tid,
        tname=res.get("tname","スレ"),
        items=posts
    )


# ---------------------------
# MEMBER API（仮）
# ---------------------------
@app.route('/api/members/<int:cid>')
def members(cid):
    res = remote_api("api/get_class_detail", {"cid": cid})
    return jsonify({"count": len(res.get("members", []))})


# ---------------------------
# RUN
# ---------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",8000)))
