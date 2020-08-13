from flask import Flask, render_template, redirect, url_for, request
from sqlalchemy import create_engine
import threading
import logging
import time
from email_server import start_server
from FlaskLoginSystem import LoginManager

app = Flask(__name__)
app.config["SECRET_KEY"] = b"#6\xcel\xe6\xd1*'\x82m\xc0\xa0K\xd7\x07_r\x0cv\x13x\xb1\x1d\x1e"

email_thread = None
resources_queue = {"creds" : 0, "users" : 0, "cities" : 0, "allgs" : 0}
lg_m = LoginManager("sqlite:///Users.db", "UserCreds", ["Id", "Email", "Password"], 0, [1], [1,2], [2])

@app.route("/")
def home() :
    return render_template("Index.html")

@app.route("/signup", methods=["GET", "POST"])
def profile() :
    if request.method == "POST" :
        user_details = {"Id" : lg_m.number_of_registered_users(), "Email" : request.form["email"], "Password" : request.form["pss"]}

        while(resources_queue["creds"] != 0) :
            time.sleep(0.01)

        update_queue("creds",1)
        lg_m.register_user(user_details)
        update_queue("creds",0)

        return redirect(f"{url_for('get_user_details')}")
    else :
         return render_template("emailpass.html")

@app.route("/user_info", methods=["GET", "POST"])
def get_user_details() :

    if(request.method == "POST") :
        allg_cbs = ["a1", "a2", "a3", "a4", "a5"]
        allgs = get_allergies()
        user_allgs = ""

        for a in range(0, len(allg_cbs)) :
            if(allg_cbs[a] in list(request.form.keys())) :
                user_allgs += f"{a},"
        user_allgs = user_allgs[:-1]

        user_data = {"Id" : lg_m.get_current_user(), "Name" : request.form["name"], "Location" : request.form["place"], "Allergies" : user_allgs, "Creds" : lg_m.get_current_user()}
        
        while(resources_queue["users"] != 0) :
            time.sleep(0.01)
        update_queue("users", 1)
        save_user_info(user_data)
        update_queue("users", 0)
        return redirect(f"{url_for('show_user_profile')}")
    else :
        return render_template("get_user_details.html")

@app.route("/user_profile", methods=["GET", "POST"])
def show_user_profile() :
    if(request.method == "POST") :
        lg_m.log_user_out()
        return redirect(f"{url_for('login')}")
    else :
        user_data = get_user_info(lg_m.get_current_user())
        allgs = get_allergies()

        user_allgs = user_data[0][3].split(',')
        allg_names = []
        for a in user_allgs :
            allg_names.append(allgs[int(a)][1])

        return render_template("user_profile.html", name=user_data[0][1], loc=user_data[0][2], allgs=allg_names)

@app.route("/login", methods=["GET", "POST"])
def login() :
    if(request.method == "POST") :
        user_data = {"Email" : request.form["email"], "Password" : request.form["pss"]}
        print(user_data)
        while(resources_queue["creds"] != 0) :
            time.sleep(0.01)
        update_queue("creds", 1)

        opt = lg_m.log_user(user_data)
        print(opt) 
        if(opt == 0) :
            update_queue("creds", 0)
            return redirect(f"{url_for('show_user_profile')}")

    else :
        return render_template("relogin.html")

def save_user_allergies(user_id, user_allergies) :

    allergies = get_allergies()

def get_allergies() :

    if(resources_queue["allgs"] != 0) :
        time.sleep(0.01)
    update_queue("allgs", 1)

    conn = create_engine("sqlite:///Users.db", echo=True).connect()

    cmd = "SELECT * FROM Allergies"
    res = list(conn.execute(cmd))

    conn.close()
    update_queue("allgs",0)

    return res

def save_user_info(user_data) :
    conn = create_engine("sqlite:///Users.db", echo=True).connect()

    cmd = f"""INSERT INTO UserInfo(Id, Name, Location, Allergies, Creds) VALUES ('{user_data["Id"]}', '{user_data["Name"]}', 
    '{user_data["Location"]}', '{user_data["Allergies"]}', '{user_data["Creds"]}' )"""

    conn.execute(cmd)

    conn.close()

def update_queue(table_name, queue_val) :
    resources_queue[table_name] = queue_val

def get_user_info(id) :
    while(resources_queue["users"] != 0) :
        time.sleep(0.01)
    update_queue("users", 1)

    conn = create_engine("sqlite:///Users.db", echo=True).connect()

    cmd = f"SELECT * FROM UserInfo WHERE Creds = '{id}'"
    res = list(conn.execute(cmd))

    conn.close()
    update_queue("users", 0)

    return res

if(__name__ == "__main__") :
    email_thread = threading.Thread(target=start_server, daemon=True)
    email_thread.start()
    app.run()