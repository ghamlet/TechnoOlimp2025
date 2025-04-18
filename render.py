from flask import Flask, render_template, request
  
app = Flask(__name__, template_folder='.')  
  
  
  
@app.route("/", methods=["GET", "POST"])  
def web():  
    # Получаем данные из POST-запроса (если они есть)
    post_data = {}
    if request.method == "POST":
        try:
            post_data = request.get_json()  # Для JSON данных
        except:
            post_data = request.form.to_dict()  # Для form-data
            
            
    return render_template('index.html', type=post_data.get('type'),
                         data=post_data.get('data'),
                         user_id=post_data.get('user_id'))  
  
  

@app.route("/api", methods=["POST"])
def submit():
    # Получаем данные из формы
    type = request.form.get("type")
    data = request.form.get("data")
    
    # Отправляем данные на новую страницу
    return render_template('result.html', type = type, data=data)


if __name__ == "__main__":  
    app.run(debug=True, host="127.0.0.1", port='8000')  
