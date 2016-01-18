import tests

import os
from flask import Flask, request, redirect, url_for, send_from_directory
from werkzeug import secure_filename

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
THIS_DIR = os.path.dirname(os.path.realpath(__file__))

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(THIS_DIR, 'images', 'user_images', 'input')
app.config['OUTPUT_FOLDER'] = os.path.join(THIS_DIR, 'images', 'user_images', 'output')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            final_image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(final_image_path)

            solve_uploaded_set(final_image_path)

            return redirect(url_for('show_results', filename=filename))
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form action="" method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    '''

@app.route('/<filename>')
def show_results(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], 'OUTPUT_{0}'.format(filename))

def solve_uploaded_set(image_url):
    kwargs = {
        'pop_open': False,
        'save_image': True,
        'output_dir': app.config['OUTPUT_FOLDER'],
    }

    return tests.play_game(image_url, **kwargs)

if __name__ == "__main__":
    app.run(host='192.168.1.101')
