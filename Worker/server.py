from flask import Flask
from flask import request
from flask import redirect
from werkzeug.utils import secure_filename
from src import encoding
import os

app = Flask(__name__)
folder = os.getenv('FOLDER', './contents')
if not os.path.exists(folder):
    os.makedirs(folder)
print("Launched for folder: " + folder)
app.config['FOLDER'] = folder


@app.route('/upload', methods=['POST'])
def upload_file():
    f = request.files['nom']
    f.save(app.config['FOLDER'] + '/' + secure_filename(f.filename))
    encoding.preEncoding(app.config['FOLDER'], secure_filename(f.filename), 'test')
    return redirect('/static/index.html')


@app.route('/')
def web_front():
    return redirect('/static/index.html')


@app.errorhandler(404)
def redirecting(error):
    return redirect('/static/index.html')





