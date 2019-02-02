"""
初版：2018-12-30
Flaskのパッケージをインストールしておきます
pip install Flask
"""
# pipでインストールするもの
from flask import Flask, render_template, url_for, request, redirect

# はじめから入っているもの
import sys
import os
import sqlite3

# データベースファイルのパス
DB_PATH = "../notes.db"

# データベースファイルのサイズ
file_size = 0

# Pythonのバージョンを確認、表示
version = sys.version


app = Flask(__name__)


def dbaccess():
    """
    データベースのConnectionとCursorを作成して返す
    """

    # もしファイルがなければテーブルを作る
    if not os.path.isfile(DB_PATH):
        create_table()

    # Connection があれば、
    conn = sqlite3.connect(DB_PATH)
    # Cursor オブジェクトを作り
    cursor = conn.cursor()
    # その execute() メソッドを呼んで SQL コマンドを実行することができます

    # ファイルサイズの取得
    global file_size
    file_size = os.path.getsize(DB_PATH) / 1024

    return conn, cursor


def create_table():
    """
    もしデータベースファイルがなければ新規にテーブルを作る関数
    """

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # executeメソッドでSQL文を実行する
    cursor.execute("""
CREATE TABLE `category` (
	`id`	integer,
	`name`	text,
	PRIMARY KEY(`id`)
);
    """)

    # executeメソッドでSQL文を実行する
    cursor.execute("""
CREATE TABLE `memo` (
	`id`	integer,
	`category_id`	integer,
	`title`	text,
	`detail`	text,
	PRIMARY KEY(`id`)
);
    """)

    conn.commit()
    cursor.close()
    conn.close()


@app.route("/")
def index():
    """
    トップページや検索など
    """

    conn, cursor = dbaccess()
    # キーワード検索
    q = request.args.get("q", default="", type=str)
    # カテゴリ絞り込み
    id = request.args.get("id", default=0, type=int)
    # 返すリスト
    lists = []
    # タイトル
    page_title = "メモ (Flask版)"
    # 検索文字
    word = q
    # 検索とカテゴリ絞り込みは同時にできない仕様
    if q != "":
        # 検索なら
        cursor.execute("""
SELECT t.id, t.category_id, c.name, t.title
FROM memo as t LEFT OUTER JOIN category as c ON t.category_id = c.id
WHERE c.name LIKE ? OR t.title LIKE ? OR t.detail LIKE ? ORDER BY t.id DESC;
        """, ("%"+q+"%", "%"+q+"%", "%"+q+"%"))
        lists = cursor.fetchall()
        page_title = q
    elif id != 0:
        # カテゴリ絞り込みなら
        cursor.execute("""
SELECT t.id, t.category_id, c.name, t.title 
FROM memo as t LEFT OUTER JOIN category as c ON t.category_id = c.id 
WHERE t.category_id = ?  ORDER BY t.id DESC;
        """, (id,))
        lists = cursor.fetchall()
        # カテゴリ名を取得
        page_title = lists[0][2]
    else:
        # 普通のトップページ
        cursor.execute("""
SELECT t.id, t.category_id, c.name, t.title 
FROM memo as t LEFT OUTER JOIN category as c ON t.category_id = c.id ORDER BY t.id DESC;
        """)
        # 全件取得は c.fetchall()
        # 一つ一つ取り出す場合はfetchoneを使います。
        lists = cursor.fetchall()

    # dbから切断
    cursor.close()
    conn.close()

    # 辞書に変数を詰め込む
    dic = {
        "page_title": page_title,
        "file_size": file_size,
        "word": word,
        "version": version,
        "lists": lists
    }

    return render_template("index.html", dic=dic)


@app.route("/memo_insert", methods=["POST", "GET"])
def memo_insert():
    """
    新規入力
    """

    conn, cursor = dbaccess()

    if request.method == "POST":

        category_id = request.form["category_id"]
        title = request.form["title"]
        detail = request.form["detail"]
        # エラー用
        maxid = 1

        try:
            cursor.execute("""
INSERT INTO memo (category_id, title, detail) VALUES (?,?,?);
            """, (category_id, title, detail))
            conn.commit()

            # 今INSERTした行のidを取得
            cursor.execute("""SELECT max(id) as maxid FROM memo;""")
            # タプルなので
            maxid = cursor.fetchone()[0]
        except:
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

        # 編集画面にリダイレクト
        return redirect(url_for("memo_update", id=maxid))

    # getなら
    else:
        # カテゴリをselect化
        cursor.execute("""SELECT * FROM category;""")
        lists = cursor.fetchall()
        cursor.close()
        conn.close()

    # 辞書に変数を詰め込む
    dic = {
        "page_title": "新規追加",
        "version": version,
        "lists": lists
    }

    return render_template('memo_insert.html', dic=dic)


@app.route("/memo_update/<int:id>", methods=["POST", "GET"])
def memo_update(id):
    """
    更新・削除
    """

    if request.method == "POST":
        delete = 0
        try:
            delete = int(request.form["delete"])
        except:
            pass

        category_id = request.form["category_id"]
        title = request.form["title"]
        detail = request.form["detail"]

        conn, cursor = dbaccess()
        # 削除
        if delete == 1:
            try:
                cursor.execute("""DELETE FROM memo WHERE id=?;""", (id,))
                conn.commit()
            except:
                conn.rollback()
            finally:
                cursor.close()
                conn.close()

            # トップページにリダイレクト
            return redirect(url_for("index"))

        # 更新
        else:
            try:
                cursor.execute("""
UPDATE memo SET category_id = ?, title = ?, detail = ? WHERE id = ?;
            """, (category_id, title, detail, id))
                conn.commit()
            except:
                conn.rollback()
            finally:
                cursor.close()
                conn.close()

    conn, cursor = dbaccess()
    # カテゴリをselect化
    cursor.execute("""SELECT * FROM category;""")
    lists = cursor.fetchall()

    cursor.execute("""
SELECT t.category_id, c.name, t.title, t.detail 
FROM memo as t LEFT OUTER JOIN category as c ON t.category_id = c.id WHERE t.id = ?;
    """, (id,))
    category_id, name, title, detail = cursor.fetchone()

    cursor.close()
    conn.close()

    # 辞書に変数を詰め込む
    dic = {
        "page_title": "編集",
        "version": version,
        "lists": lists,
        "id": id,
        "category_id": category_id,
        "title": title,
        "detail": detail
    }

    return render_template("memo_update.html", dic=dic)


@app.route("/detail/<int:_id>")
def detail(_id):
    """
    詳細表示
    """

    conn, cursor = dbaccess()
    cursor.execute("""
SELECT t.id, t.category_id, c.name, t.title, t.detail 
FROM memo as t LEFT OUTER JOIN category as c ON t.category_id = c.id WHERE t.id = ?;
    """, (_id,))
    id, category_id, name, title, detail = cursor.fetchone()

    cursor.close()
    conn.close()

    # 辞書に変数を詰め込む
    dic = {
        "page_title": title,
        "version": version,
        "id": id,
        "category_id": category_id,
        "name": name,
        "title": title,
        "detail": detail
    }

    return render_template("detail.html", dic=dic)


@app.route("/category", methods=["POST", "GET"])
def category():
    """
    カテゴリ編集画面
    """

    if request.method == "POST":
        name = request.form["name"]

        conn, cursor = dbaccess()
        try:
            cursor.execute(
                """INSERT INTO category (name) VALUES (?);""", (name,))
            conn.commit()
        except:
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    conn, cursor = dbaccess()
    cursor.execute("""SELECT * FROM category;""")
    lists = cursor.fetchall()
    cursor.close()
    conn.close()

    # 辞書に変数を詰め込む
    dic = {
        "page_title": "カテゴリ編集画面",
        "version": version,
        "lists": lists
    }

    return render_template('category.html', dic=dic)


@app.route("/category_update", methods=["POST"])
def category_update():
    """
    カテゴリ更新
    """
    if request.method == "POST":
        id = request.form["id"]
        name = request.form["name"]
        if id != "" and name != "":
            f = "ok"
            conn, cursor = dbaccess()
            try:
                cursor.execute(
                    """UPDATE category SET name=? WHERE id=?;""", (name, id))
                conn.commit()
            except:
                conn.rollback()
                f = "ng"
            finally:
                cursor.close()
                conn.close()

            return f

    return "ng"


@app.route("/category_delete", methods=["POST"])
def category_delete():
    """
    カテゴリ削除
    """

    if request.method == "POST":
        id = request.form["id"]
        if id != "":
            conn, cursor = dbaccess()
            f = "ok"
            try:
                cursor.execute("""DELETE FROM category WHERE id=?;""", (id,))
                conn.commit()
            except:
                conn.rollback()
                f = "ng"
            finally:
                cursor.close()
                conn.close()

            return f

    return "ng"


@app.route("/vacuum")
def vacuum():
    """
    SQLiteの空き領域開放
    """
    conn, cursor = dbaccess()
    try:
        cursor.execute("""VACUUM;""")
        conn.commit()
    except:
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

    # トップページにリダイレクト
    return redirect(url_for("index"))


if __name__ == '__main__':
    app.run(debug=True)
