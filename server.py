#!/usr/bin/python3

# sudo apt-get install python3-pip
# sudo pip3 install flask

import os
from flask import Flask, request, Response, render_template
from multiprocessing import Pool
from parser import parse_flags, parse_single_flag
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
  scores, paths, raw_scores = pool.apply(parse_single_flag, [q])

  positive_scores = sum([x[1] for x in raw_scores]) / float(len(raw_scores))# sorted([x[1] for x in scores])
  negative_scores = sum([x[0] for x in raw_scores]) / float(len(raw_scores))# sorted([x[0] for x in scores])

  calc_scores = softmax([positive_scores, negative_scores])

  return render_template('template.html', scores=scores, paths=paths, input_sentence=q, calc_scores = calc_scores, raw_scores=raw_scores)

  return Response(
    response=result,
    status=200)

@app.route('/batch', methods=['POST'])
def batch():
  flags = request.get_json()['flags']

  results = pool.apply(parse_flags, [flags])

  print(results)

  per_flag_results = []

  for result in results:
    positive_scores = sum([x[1] for x in result]) / float(len(result))
    negative_scores = sum([x[0] for x in result]) / float(len(result))

    calc_scores = round(softmax([positive_scores, negative_scores]).tolist()[0], 3)

    per_flag_results.append(calc_scores)

  return Response(
    response=json.dumps(per_flag_results),
    status=200)

if __name__ == '__main__':
    app.run(debug=False, port=port, host="0.0.0.0")
