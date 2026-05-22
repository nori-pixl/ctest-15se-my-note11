import os
import requests
import uuid
import pymysql
from flask import Flask, request, jsonify

app = Flask(__name__)

# ==========================================
# 設定（MySQLの接続情報のみ）
# ==========================================
MYSQL_CONFIG = {
    'user': 'root',
    'password': '',
    'host': '127.0.0.1',
    'database': 'board_db',
    'cursorclass': pymysql.cursors.DictCursor
}

# MySQLへの通信ヘルパー関数
def query_mysql(sql, params=[], is_select=True, return_insert_id=False):
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            if is_select:
                result = cursor.fetchall()
            else:
                conn.commit()
                result = conn.insert_id() if return_insert_id else True
        conn.close()
        return result
    except Exception as e:
        print("MySQL Error:", e)
        return [] if is_select else False

# 1. クラス詳細（一般クラス固定）のスレッド一覧取得
@app.route('/api/class/1', methods=['GET'])
def get_class_detail():
    threads = query_mysql("SELECT * FROM threads WHERE class_id = 1 ORDER BY id DESC")
    return jsonify({
        "success": True,
        "class": {"id": 1, "name": "一般クラス"},
        "threads": threads
    })

# 2. 特定スレッドの情報と投稿一覧の取得
@app.route('/api/thread/<int:tid>', methods=['GET'])
def get_thread_detail(tid):
    thread_rows = query_mysql("SELECT * FROM threads WHERE id = %s", [tid])
    if not thread_rows:
        return jsonify({"success": False, "message": "Thread not found"}), 404
    
    # 辞書型として安全に抽出
    thread_data = thread_rows[0] if isinstance(thread_rows, list) and len(thread_rows) > 0 else thread_rows
    posts = query_mysql("SELECT * FROM posts WHERE thread_id = %s ORDER BY id ASC", [tid])
    return jsonify({
        "success": True,
        "thread": thread_data,
        "posts": posts
    })
# 3. 新規スレッドの作成 ＆ 最初の本文を投稿1番目として登録（エラー対策版）
@app.route('/api/threads', methods=['POST'])
def create_thread():
    data = request.json
    if not data:
        return jsonify({"success": False, "message": "No data received"}), 400

    class_id = data.get("class_id", 1)
    title = data.get("title", "無題")
    body = data.get("body", "")
    name = data.get("n", "名無しさん")
    date_str = data.get("d", "")

    # スレッドをMySQLに挿入し、新規発行されたIDを取得
    tid = query_mysql(
        "INSERT INTO threads (class_id, title) VALUES (%s, %s)", 
        [class_id, title], 
        is_select=False, 
        return_insert_id=True
    )
    
    if not tid:
        print("Failed to insert thread into MySQL.")
        return jsonify({"success": False}), 500
    
    # 最初の本文を「posts」テーブルに1番目のレスとして挿入
    # D1移植時のカラム名（n, b, d, img）の不一致を防ぐため、安全なクエリを発行
    query_mysql(
        "INSERT INTO posts (thread_id, n, b, d, img) VALUES (%s, %s, %s, %s, %s)",
        [tid, name, body, date_str, ""],
        is_select=False
    )
    
    return jsonify({"success": True, "tid": tid})

# 4. 新しい投稿（レス）の追加処理
@app.route('/api/posts', methods=['POST'])
def create_post():
    name = request.form.get("name", "名無しさん")
    message = request.form.get("b", "") or request.form.get("message", "")
    thread_id = request.form.get("thread_id")
    date_str = request.form.get("d", "")
    image_url = ""

    # JSON形式リクエストでのフォールバック
    if not thread_id and request.json:
        data = request.json
        name = data.get("name", "名無しさん")
        message = data.get("body", "") or data.get("message", "")
        thread_id = data.get("thread_id")
        date_str = data.get("d", "")

    query_mysql(
        "INSERT INTO posts (thread_id, n, b, d, img) VALUES (%s, %s, %s, %s, %s)",
        [thread_id, name, message, date_str, image_url],
        is_select=False
    )
    return jsonify({"success": True})

# 5. 【削除機能】スレッドの完全削除
@app.route('/api/del_thread', methods=['POST'])
def delete_thread():
    data = request.json
    tid = data.get("tid")
    if tid:
        query_mysql("DELETE FROM posts WHERE thread_id = %s", [tid], is_select=False)
        query_mysql("DELETE FROM threads WHERE id = %s", [tid], is_select=False)
    return jsonify({"success": True})

# 6. 【削除機能】特定の投稿（レス）の削除
@app.route('/api/del_post', methods=['POST'])
def delete_post():
    data = request.json
    pid = data.get("pid")
    if pid:
        query_mysql("DELETE FROM posts WHERE id = %s", [pid], is_select=False)
    return jsonify({"success": True})

if __name__ == '__main__':
    # タブレットのTermuxローカル環境（ポート7000）で起動
    app.run(host='0.0.0.0', port=7000)
