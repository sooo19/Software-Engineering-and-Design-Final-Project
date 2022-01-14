from flask import Flask
from flask import request
from flask import render_template
from flask import url_for, redirect, flash
from flask import abort
from bson.objectid import ObjectId
from flask_pymongo import PyMongo
from datetime import datetime
import time


app = Flask(__name__, template_folder="templates")
app.config["MONGO_URI"] = "mongodb://localhost:27017/DGUclub"        # DGUclub Database 생성
app.config['SECRET_KEY'] = '4453844'

mongo = PyMongo(app)


@app.template_filter('formatdatetime')
def format_datetime(value):     # UTC time을 local 시간으로 표기하도록 변환
    if value is None:
        return ""

    # 게시글 작성 시간 구하기(타임스탬프 사용)
    now_timestamp = time.time()
    
    # 시간차이 = datetime형 현재시간 - datetime형 UTC 시간
    offset = datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(now_timestamp)
    
    # GMT시간에 각 지역에서 발생하는 시간 차이를 더해 현재 시간을 표기
    value = datetime.fromtimestamp((int(value) / 1000)) + offset
    return value.strftime('%Y-%m-%d %H:%M:%S')


# 게시글 상세보기
@app.route("/view")
def board_view():
    idx = request.args.get("idx")
    if idx is not None:
        board = mongo.db.board
        
        # mongodb의 id 값이 Object형이므로, idx를 Object형으로 변환
        data = board.find_one({"_id": ObjectId(idx)})
        if data is not None:
            result = {
                "id": data.get("_id"),
                "name": data.get("name"),
                "title": data.get("title"),
                "contents": data.get("contents"),
                "pubdate": data.get("pubdate")
            }
            return render_template("view.html", result=result)
    return abort(404)   # 예외 발생 시, 오류 메시지 출력


# 게시판 글 작성
@app.route("/write", methods=["GET", "POST"])
def board_write():
    # request method가 POST인 경우 작성자 '이름, 제목, 내용'을 받아옴
    if request.method == "POST":
        name = request.form.get("name")
        title = request.form.get("title")
        contents = request.form.get("contents")

        current_utc_time = round(datetime.utcnow().timestamp() * 1000)
        board = mongo.db.board

        post = {
            "name": name,
            "title": title,
            "contents": contents,
            "pubdate": current_utc_time     # 게시글 작성 시간
        }

        print(post)
        x = board.insert_one(post)      # db에 정보를 저장

        flash("게시글이 정상적으로 작성되었습니다.")

        # 게시글 작성하고 화면 전환 후, 작성한 게시글이 화면에 나타나도록 할 때 사용
        return redirect(url_for("board_view", idx=x.inserted_id))
    else:   # request method가 GET인 경우, write template 보여주기
        return render_template("write.html")


# 게시글 목록
@app.route("/list")
def lists():
    query = {}
    board = mongo.db.board
    datas = board.find(query)
    return render_template("list.html", datas=list(datas))


# 게시글 수정하기
@app.route("/edit/<idx>", methods=["GET", "POST"])
def board_edit(idx):
    if request.method == "GET":
        board = mongo.db.board
        data = board.find_one({"_id": ObjectId(idx)})
        if data is None:
            flash("해당 게시물이 존재하지 않습니다.")
            return redirect(url_for("lists"))
        else:
            return render_template("edit.html", data=data)

    else:
        name = request.form.get("name")
        title = request.form.get("title")
        contents = request.form.get("contents")
        board = mongo.db.board

        data = board.find_one({"_id": ObjectId(idx)})

        board.update_one({"_id": ObjectId(idx)}, {
            "$set": {
                "name": name,
                "title": title,
                "contents": contents,
            }
        })
        flash("게시글이 수정되었습니다.")
        return redirect(url_for("board_view", idx=idx))


# 게시글 삭제하기
@app.route("/delete/<idx>")
def board_delete(idx):
    board = mongo.db.board
    board.delete_one({"_id": ObjectId(idx)})
    flash("게시글이 삭제 되었습니다.")

    return redirect(url_for("lists"))


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=5000)