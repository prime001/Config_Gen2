# https://docs.python.org/3/library/argparse.html
from flask import Flask, send_file, render_template
from flask import request
import os
import config_gen2
import sqlite3


os.environ["FLASK_ENV"] = str("development")

app = Flask(__name__, static_url_path="/static")


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/config_gen/", methods=["GET", "POST"])
def config_gen():
    if request.method == "POST":
        data = request.form
        zipped = config_gen2.passinput(data)
        return send_file(zipped, as_attachment=True)
    else:
        return render_template("config_gen.html")


@app.route("/ip_plan/", methods=["GET"])
# /ip_plan/:ip_plan # /ip_plan/all, /ip_plan/ans
# /ip_plan # all
# /ip_plan?plan=ans # ans
def ip_plan():
    sub = request.args.get("sub", "ALL")
    con = sqlite3.connect("/opt/NetDevOps/Config_gen2/ip_plan.db")
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    # 'SELECT foo  FROM ' + ip_plan
    # ip_plan = '; SELECT * FROM users'
    cur.execute(
        "select * from ip_plan where hostname like ? order by hostname",
        [f"%{sub}-%" if sub != "ALL" else "%%"],
    )
    rows = cur.fetchall()
    con.close()
    return render_template("ip_plan.html", sub=sub, rows=rows)


@app.route("/inventory/")
def inventory():
    con = sqlite3.connect("/opt/NetDevOps/Config_gen2/inventory.db")
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("select * from inventory")
    rows = cur.fetchall()
    return render_template("inventory.html", rows=rows)


@app.route("/reports/")
def reports():
    return render_template("reports.html")


@app.route("/test/")
def test():
    return render_template("test.html")


def main(data):
    print("Printing Data From Function main")
    params = {}
    params["Model"] = data["Model"]
    params["EF_Type"] = data["EF_Type"]
    params["hostname"] = data["hostname"]
    params["num_switches"] = data["num_switches"]
    print(params)
    return get_config(params)


def get_config(params):
    print("Configs")
    pass


if __name__ == "__main__":
    # Start flask
    # And tell user to go to page
    # https://flask.palletsprojects.com/en/1.1.x/quickstart/
    app.run(host="0.0.0.0")
