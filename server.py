#!/usr/bin/python3

# sudo apt-get install python3-pip
# sudo pip3 install flask

import os
from flask import Flask, request, Response, render_template
from multiprocessing import Pool
from parser import parse_sentence
import json

app = Flask(__name__)
port = 80 if os.getuid() == 0 else 8000

pool = Pool(1, maxtasksperchild=50)

@app.route('/')
def index():
  q = request.args.get("q", "")
  scores, paths = pool.apply(parse_sentence, [q])

  return render_template('template.html', scores=scores, paths=paths, input_sentence=q)

  return Response(
    response=result,
    status=200)

if __name__ == '__main__':
    app.run(debug=True, port=port, host="0.0.0.0")


