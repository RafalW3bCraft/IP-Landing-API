from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

API_URL = "http://httpbin.org/post"  # Example URL for posting data

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/get', methods=['GET'])
def get_api():
    response = requests.get("https://jsonplaceholder.typicode.com/posts/1")
    return jsonify(response.json()), 200

@app.route('/api/post', methods=['POST'])
def post_api():
    # Simulate data from a form
    data = request.form
    response = requests.post(API_URL, json=data)
    return jsonify(response.json()), 200

@app.route('/submit', methods=['POST'])
def submit():
    # Get form data
    name = request.form.get('name')
    email = request.form.get('email')
    message = request.form.get('message')

    # Send data to an external API
    payload = {"name": name, "email": email, "message": message}
    api_response = requests.post(API_URL, json=payload)

    return render_template(
        "index.html",
        api_response=api_response.json(),
        submitted_data=payload,
    )

if __name__ == '__main__':
    app.run(debug=True)
