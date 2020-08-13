from flask import Flask, request, render_template, redirect, url_for
from FlaskLoginSystem import LoginManager

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def profile() :
    if request.method == "POST" :
        profile = [request.form["name"],
                   request.form["gender"],
                   request.form["email"],
                   request.form["phone"],
                   request.form["place"]]
        print(profile)
        return redirect(f"{url_for('allergies')}")
    else :
         return render_template("homepage.html")

@app.route("/allergies", methods=["GET", "POST"])
def allergies() :
    if request.method == "POST" :
        checkboxes = ["a1", "a2", "a3", "a4", "a5", "a6"]
        allergies = ["Pollen Allergy", "Dust Allergy", "Throat Infection", "Chronic sinus", "Asthma", "Bronchitis"]
        user_allergies = []
        for a in range(0, len(checkboxes)) :
            if(checkboxes[a] in list(request.form.keys())) :
                user_allergies.append(allergies[a])


        print(user_allergies)
        return render_template("success.html")
    else :
         return render_template("allergies.html")

if __name__=="__main__":
    app.run(debug=True)
