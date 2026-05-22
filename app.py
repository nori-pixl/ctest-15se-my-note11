import os
import datetime
import requests
from flask import Flask, request, redirect, render_template_string, make_response, url_for, flash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "temporary_secret_key_string")

# Termux側のCloudflare Tunnel URLを設定
TERMUX_API_BASE = os.environ.get(
    "TERMUX_API_URL", 
    "https://tim-advisors-novel-varieties.trycloudflare.com"
)

# 共通HTMLテンプレート
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>BBS</title>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <style>
        body { font-family: sans-serif; background: #fffff0; color: #000000; padding: 20px; }
        a { color: #0000ff; text-decoration: none; }
        a:hover { text-decoration: underline; }
        .box { background: #fafafa; border: 1px solid #ccc; padding: 10px; margin-bottom: 10px; }
        .thread-title { font-size: 1.2em; font-weight: bold; color: #ff0000; margin-bottom: 5px; }
        .post-box { border-bottom: 1px solid #ccc; padding: 10px 0; }
        .post-meta { font-weight: bold; color: #228b22; }
        .post-body { margin: 5px 0 5px 20px; white-space: pre-wrap; word-break: break-all; }
        .error-msg { color: #ff0000; font-weight: bold; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div>ログイン中: {{ login_user }}</div>
    <hr>
    
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        {% for message in messages %}
          <div class="error-msg">[注意] {{ message }}</div>
        {% endfor %}
      {% endif %}
    {% endwith %}

    {% if v == 'class' %}
        <div class="thread-title">{{ cname }} - スレッド一覧</div>
        [<a href="/c/{{ cid }}/create_form">新しいスレッドを建てる</a>]
        <hr>
        <div>
            {% if not items %}
                <p>まだスレッドがありません。</p>
            {% endif %}
            {% for t in items %}
                <div class="box">
                    <a href="/c/{{ cid }}/t/{{ t.id }}">{{ loop.index }}: {{ t.title }}</a>
                    {% if t.id|string in vlist %}
                        <form method="POST" action="/remove_from_list/{{ t.id }}" style="display:inline; margin-left:10px;">
                            <button type="submit" style="font-size:0.8em;">お気に入り解除</button>
                        </form>
                    {% endif %}
                    <form method="POST" action="/del_t/{{ cid }}/{{ t.id }}" style="display:inline; margin-left:10px;">
                        <button type="submit" style="font-size:0.8em;">削除</button>
                    </form>
                </div>
            {% endfor %}
        </div>
        
    {% elif v == 'create_form' %}
        <div class="thread-title">新しいスレッドを建てる</div>
        [<a href="/c/{{ cid }}">キャンセルして戻る</a>]
        <hr>
        <form method="POST" action="/c/{{ cid }}/new">
            <table border="0">
                <tr><td>タイトル:</td><td><input type="text" name="t" required style="width: 300px;"></td></tr>
                <tr><td valign="top">最初の本文:</td><td><textarea name="b" required style="width: 300px; height: 100px;"></textarea></td></tr>
                <tr><td></td><td><button type="submit">新規スレッド作成</button></td></tr>
            </table>
        </form>
        
    {% elif v == 'thread' %}
        <div class="thread-title">{{ tname }}</div>
        [<a href="/c/{{ cid }}">スレッド一覧に戻る</a>] | 
        [<a href="/c/{{ cid }}/t/{{ tid }}/post_form">このスレッドに書き込む</a>]
        <p style="font-size: 0.9em; color: #555;">本日の画像残りアップロード回数: {{ 5 - count }} / 5 回</p>
        <hr>
        <div>
            {% for p in items %}
                <div class="post-box">
                    <span class="post-meta">{{ loop.index }} : 名前: {{ p.n }} : {{ p.d }} ID: {{ p.id }}</span>
                    <form method="POST" action="/del_p/{{ cid }}/{{ tid }}/{{ p.id }}" style="display:inline; margin-left:10px;">
                        <button type="submit" style="font-size:0.8em;">削除</button>
                    </form>
                    <div class="post-body">{{ p.b }}</div>
                </div>
            {% endfor %}
        </div>
        
    {% elif v == 'post_form' %}
        <div class="thread-title">{{ tname }} への書き込み</div>
        [<a href="/c/{{ cid }}/t/{{ tid }}">キャンセルして戻る</a>]
        <hr>
        <form method="POST" action="/c/{{ cid }}/t/{{ tid }}/p" enctype="multipart/form-data">
            <table border="0">
                <tr><td>名前:</td><td><input type="text" name="name" value="名無しさん" style="width: 250px;"></td></tr>
                <tr><td valign="top">本文:</td><td><textarea name="b" required style="width: 250px; height: 80px;"></textarea></td></tr>
                <tr><td>画像:</td><td><input type="file" name="image" accept="image/*" {% if count >= 5 %}disabled{% endif %}></td></tr>
                <tr><td></td><td>
                    <button type="submit">
                        {% if count >= 5 %}画像上限のため本文のみ送信可{% else %}書き込む{% endif %}
                    </button>
                </td></tr>
            </table>
        </form>
    {% endif %}

    <script>
        document.querySelectorAll('.post-body').forEach(function(el) {
            var exp = /(https?:\/\/[^\s]+)/g;
            el.innerHTML = el.innerHTML.replace(exp, '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>');
        });
    </script>
</body>
</html>
"""

def get_image_upload_count():
    return int(request.cookies.get('img_upload_count', 0))

def check_delete_limit():
    return True

@app.route('/')
def index():
    return redirect('/c/1')

@app.route('/remove_from_list/<int:tid>', methods=['POST'])
def remove_from_list(tid):
    vlist = request.cookies.get('vlist', '').split(',')
    if str(tid) in vlist: 
        vlist.remove(str(tid))
    resp = make_response(redirect('/c/1'))
    resp.set_cookie('vlist', ','.join(vlist), max_age=60*60*24*30)
    return resp

@app.route('/c/<int:cid>')
def v_class(cid):
    if cid != 1: 
        return redirect('/')
    try:
        res = requests.get(f"{TERMUX_API_BASE}/api/class/{cid}", timeout=10).json()
        threads = res.get("threads", [])
        cname = res.get("class", {}).get("name", "一般クラス")
    except Exception:
        threads, cname = [], "一般クラス"
        flash("データベースAPI（タブレット）に接続できませんでした。")
        
    vlist = request.cookies.get('vlist', '').split(',')
    return render_template_string(HTML, v='class', cid=cid, cname=cname, items=threads, vlist=vlist, login_user="名無しさん")

@app.route('/c/<int:cid>/create_form')
def create_form(cid):
    if cid != 1: 
        return redirect('/')
    return render_template_string(HTML, v='create_form', cid=cid, login_user="名無しさん")
    @app.route('/c/<int:cid>/new', methods=['POST'])
def new_t(cid):
    if cid != 1: 
        return redirect('/')
    title = request.form.get('t')
    body = request.form.get('b')
    if title and body:
        now_str = datetime.datetime.now().strftime('%m/%d %H:%M')
        try:
            res = requests.post(f"{TERMUX_API_BASE}/api/threads", json={
                "class_id": cid, 
                "title": title, 
                "body": body, 
                "n": "名無しさん", 
                "d": now_str
            }, timeout=10).json()
            
            tid = res.get("tid")
            if tid:
                vlist = request.cookies.get('vlist', '').split(',')
                if str(tid) not in vlist:
                    vlist.append(str(tid))
                resp = make_response(redirect(url_for('v_thread', cid=cid, tid=tid)))
                resp.set_cookie('vlist', ','.join(vlist), max_age=60*60*24*30)
                return resp
        except Exception as e:
            flash(f"スレッド作成エラー: {str(e)}")
            
    return redirect(url_for('v_class', cid=cid))

@app.route('/c/<int:cid>/t/<int:tid>')
def v_thread(cid, tid):
    if cid != 1: 
        return redirect('/')
    try:
        res = requests.get(f"{TERMUX_API_BASE}/api/thread/{tid}", timeout=10).json()
        thread_data = res.get("thread", [])
        thread = thread_data[0] if isinstance(thread_data, list) and len(thread_data) > 0 else thread_data
        posts = res.get("posts", [])
    except Exception:
        thread, posts = {"title": "不明"}, []
        flash("投稿データの取得に失敗しました。")
        
    upload_count = get_image_upload_count()
    return render_template_string(HTML, v='thread', cid=cid, tid=tid, tname=thread.get('title', '不明'), items=posts, login_user="名無しさん", count=upload_count)

@app.route('/c/<int:cid>/t/<int:tid>/post_form')
def post_form(cid, tid):
    if cid != 1: 
        return redirect('/')
    try:
        res = requests.get(f"{TERMUX_API_BASE}/api/thread/{tid}", timeout=10).json()
        thread_data = res.get("thread", [])
        thread = thread_data[0] if isinstance(thread_data, list) and len(thread_data) > 0 else thread_data
        tname = thread.get("title", "不明")
    except Exception:
        tname = "不明"
    upload_count = get_image_upload_count()
    return render_template_string(HTML, v='post_form', cid=cid, tid=tid, tname=tname, login_user="名無しさん", count=upload_count)

@app.route('/c/<int:cid>/t/<int:tid>/p', methods=['POST'])
def post(cid, tid):
    if cid != 1: 
        return redirect('/')
    name = request.form.get('name', '名無しさん')
    message = request.form.get('b', '')
    file = request.files.get('image')
    
    upload_count = get_image_upload_count()
    img_uploaded = False
    now_str = datetime.datetime.now().strftime('%m/%d %H:%M')

    if file and file.filename != '':
        if upload_count >= 5:
            flash("画像のアップロードは1日合計5枚までです。本文のみで再投稿してください。")
            return redirect(url_for('v_thread', cid=cid, tid=tid))
        
        try:
            files = {'image': (file.filename, file.stream, file.content_type)}
            data = {'name': name, 'message': message, 'thread_id': tid, 'd': now_str}
            api_res = requests.post(f"{TERMUX_API_BASE}/api/posts", data=data, files=files, timeout=30).json()
            if api_res.get("success"):
                img_uploaded = True
        except Exception as e:
            flash(f"画像転送エラー: {str(e)}")
            return redirect(url_for('v_thread', cid=cid, tid=tid))
    else:
        try:
            requests.post(f"{TERMUX_API_BASE}/api/posts", json={'name': name, 'message': message, 'thread_id': tid, 'd': now_str}, timeout=10)
        except Exception as e:
            flash(f"投稿エラー: {str(e)}")
            return redirect(url_for('v_thread', cid=cid, tid=tid))

    resp = make_response(redirect(url_for('v_thread', cid=cid, tid=tid)))
    if img_uploaded:
        upload_count += 1
        tomorrow = datetime.datetime.now().date() + datetime.timedelta(days=1)
        expires = datetime.datetime.combine(tomorrow, datetime.time.min)
        resp.set_cookie('img_upload_count', str(upload_count), expires=expires)
    return resp

@app.route('/del_t/<int:cid>/<int:tid>', methods=['POST'])
def del_t(cid, tid):
    if not check_delete_limit():
        flash("本日の削除回数の上限(5回)に達しました。削除できません")
        return redirect(url_for('v_class', cid=cid))
    try:
        requests.post(f"{TERMUX_API_BASE}/api/del_thread", json={"tid": tid}, timeout=10)
    except Exception as e:
        flash(f"削除通信エラー: {str(e)}")
    return redirect(url_for('v_class', cid=cid))

@app.route('/del_p/<int:cid>/<int:tid>/<int:pid>', methods=['POST'])
def del_p(cid, tid, pid):
    if not check_delete_limit():
        flash("本日の削除回数の上限(5回)に達しました。削除できません")
        return redirect(url_for('v_thread', cid=cid, tid=tid))
    try:
        requests.post(f"{TERMUX_API_BASE}/api/del_post", json={"pid": pid}, timeout=10)
    except Exception as e:
        flash(f"削除通信エラー: {str(e)}")
    return redirect(url_for('v_thread', cid=cid, tid=tid))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
