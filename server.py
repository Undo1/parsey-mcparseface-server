#!/usr/bin/python3

# sudo apt-get install python3-pip
# sudo pip3 install flask

import os
from flask import Flask, request, Response, render_template
from multiprocessing import Pool
from parser import parse_sentence
import json
import numpy as np

app = Flask(__name__)
port = 80 if os.getuid() == 0 else 8000

pool = Pool(1, maxtasksperchild=50)

def softmax(w, t=1.0):
  e = np.exp(np.array(w) / t)
  dist = e / np.sum(e)
  return dist

@app.route('/')
def index():
  q = request.args.get("q", "")
  scores, paths, raw_scores = pool.apply(parse_sentence, [q])

  positive_scores = sum([x[1] for x in raw_scores]) / float(len(raw_scores))# sorted([x[1] for x in scores])
  negative_scores = sum([x[0] for x in raw_scores]) / float(len(raw_scores))# sorted([x[0] for x in scores])

  calc_scores = softmax([positive_scores, negative_scores])

  return render_template('template.html', scores=scores, paths=paths, input_sentence=q, calc_scores = calc_scores, raw_scores=raw_scores)

  return Response(
    response=result,
    status=200)

if __name__ == '__main__':
    app.run(debug=False, port=port, host="0.0.0.0")
