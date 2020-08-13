import datetime, requests, json, os, time, smtplib
from sqlalchemy import create_engine

def start_server() :

    print("Email Server Started")
    while(True) :
        current_time = datetime.datetime.now()
        time_difference = timecon(current_time, [13, 20, 0])

        if(time_difference <= 1)  :
            update_current_conditions()
            update_users()
            time.sleep(60)

            new_time = datetime.datetime.now()
            new_time_diff = timecon(new_time, [0,0,0])

            time.sleep(new_time_diff)
        else :
            time.sleep(time_difference)

from app import resources_queue, update_queue

def update_users() :

    users = get_users()
    allergies = get_allergies()

    for a in range(0,len(users)) :
        if(a == 60) :
            time.sleep(60)
        user_allergies = users[a][3].split(",")
        next_day_conds = get_day_conds(2, users[a][2])[1]
        current_conds = get_current_conds(users[a][2])

        flared_all = get_flared_allergies(user_allergies, allergies, (next_day_conds[0] - current_conds[0], next_day_conds[1] - current_conds[1]))
        if(len(flared_all) != 0) :
            notify_user(flared_all, allergies, get_user_email(users[a][4]))

def get_users() :
    
    while(resources_queue["users"] != 0) :
        time.sleep(0.01)
    update_queue("users", 1)

    conn = create_engine("sqlite:///Users.db", echo=True).connect()

    cmd = "SELECT * FROM UserInfo"

    users = list(conn.execute(cmd))

    conn.close()

    update_queue("users", 0)
    return users

def get_allergies() :

    while(resources_queue["allgs"] != 0) :
        time.sleep(0.01)
    update_queue("allgs", 1)

    conn = create_engine("sqlite:///Users.db", echo=True).connect()

    cmd = "SELECT * FROM Allergies"

    allergies = list(conn.execute(cmd))

    conn.close()

    update_queue("allgs", 0)
    return allergies

def get_day_conds(days, city) :

    api_key = os.environ.get("OPEN_WEATHER_API_KEY")

    req_url = f"""http://api.openweathermap.org/data/2.5/forecast?q={city}&cnt={days}&appid={api_key}"""

    resp = requests.get(req_url)
    conv_resp = resp.json()

    conds = []
    for a in range(0, days) :
        conds.append((float(conv_resp["list"][a]["main"]["temp"]), float(conv_resp["list"][a]["main"]["humidity"])))

    return conds

def get_current_conds(city) :

    while(resources_queue["cities"] != 0) :
        time.sleep(0.01)
    update_queue("cities", 1)

    conn = create_engine("sqlite:///Users.db", echo=True).connect()

    cmd = f"SELECT * FROM Cities WHERE Name = '{city}'"
    res = list(conn.execute(cmd))[0]

    conn.close()
    update_queue("cities", 0)

    conds = (res[2], res[3])

    return conds

def get_flared_allergies(user_allergies, allergies, conds_diff) :

    flared_allergies = []
    for a in range(0,len(user_allergies)) :
        user_allergy = int(user_allergies[a])

        if(allergies[user_allergy][2] != None) :
            if(allergies[user_allergy][2] < 0) :
                if(conds_diff[0] < allergies[user_allergy][2]) :
                    flared_allergies.append(a)
                    continue
            elif(allergies[user_allergy][2] > 0) :
                if(conds_diff[0] > allergies[user_allergy][2]) :
                    flared_allergies.append(a)
                    continue
        
        if(allergies[user_allergy][3] != None) :
            if(allergies[user_allergy][3] < 0) :
                if(conds_diff[0] < allergies[user_allergy][3]) :
                    flared_allergies.append(a)
                    continue
            elif(allergies[user_allergy][3] > 0) :
                if(conds_diff[0] > allergies[user_allergy[3]]) :
                    flared_allergies.append(a)
                    continue
    
    return flared_allergies
    
def timecon(timenow,timetarget):
    td=(timenow.hour*3600)+(timenow.minute*60)+timenow.second
    tt=(timetarget[0]*3600)+(timetarget[1]*60)+timetarget[2]
    tl=tt-td

    if(tl < 0) :
        return 24*3600-tl
    return tl

def notify_user(flared_allergies, allergies, user_email) :

    sender_addr = os.environ.get("CARETAKER_EMAIL_ADDR")
    sender_pss = os.environ.get("CARETAKER_EMAIL_PSS")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp :
        smtp.login(sender_addr, sender_pss)

        msg = "Subject: AllergyAlert\n\nYou are more susceptible to the following allergies tommorrow: "
        for allergy in flared_allergies :
            msg += f"\n{allergies[allergy][1]}"

        smtp.sendmail(sender_addr, user_email, msg)
        print("Email sent to {}".format(user_email))

def update_current_conditions() :
    
    while(resources_queue["cities"] != 0) :
        time.sleep(0.01)
    update_queue("cities", 1)

    cities = get_cities()

    conn = create_engine("sqlite:///Users.db", echo=True).connect()

    for a in range(0, len(cities)) :
        if(a == 60) :
            time.sleep(60)
        current_conds = get_day_conds(1, cities[a][1])
        cmd = f"UPDATE Cities SET Temp = {current_conds[0][0]}, Humi = {current_conds[0][1]} WHERE Id = {a}"
        conn.execute(cmd)
    
    conn.close()
    update_queue("cities", 0)
        
def get_cities() :

    conn = create_engine("sqlite:///Users.db", echo=True).connect()

    cmd = f"SELECT * FROM Cities"
    res = list(conn.execute(cmd))

    conn.close()

    return res

def get_user_email(user_id) :

    while(resources_queue["creds"] != 0) :
        time.sleep(0.01)
    update_queue("creds", 1)

    conn = create_engine("sqlite:///Users.db", echo=True).connect()

    cmd = f"SELECT * FROM UserCreds WHERE Id = '{user_id}'"
    res = list(conn.execute(cmd))[0]

    conn.close()
    update_queue("creds", 1)

    return res[1]
