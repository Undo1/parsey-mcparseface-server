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

  positive_scores = sorted([x[1] for x in scores])
  negative_scores = sorted([x[0] for x in scores])

  max_positive_score = positive_scores.pop()
  max_negative_score = negative_scores.pop()

  calc_positive_score = max_positive_score + sum(positive_scores) / float(len(positive_scores))
  calc_negative_score = max_negative_score + sum(negative_scores) / float(len(negative_scores))

  return render_template('template.html', scores=scores, paths=paths, input_sentence=q, pos_scores=positive_scores, neg_scores=negative_scores, calc_pos=calc_positive_score, calc_neg=calc_negative_score)

  return Response(
    response=result,
    status=200)

if __name__ == '__main__':
    app.run(debug=True, port=port, host="0.0.0.0")


