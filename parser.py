#!/usr/bin/python3

from collections import OrderedDict
from flask import render_template
import subprocess
import datetime
import sys
import os

sys.path.insert(0, '../cnn-text-classification-tf')

import cnntest # Comes from that directory ^. Ugly hack, as usual

ROOT_DIR = "../models/syntaxnet"
PARSER_EVAL = "bazel-bin/syntaxnet/parser_eval"
MODEL_DIR = "syntaxnet/models/parsey_mcparseface"

def open_parser_eval(args):
  return subprocess.Popen(
    [PARSER_EVAL] + args,
    cwd=ROOT_DIR,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE
  )

def send_input(process, input):
  process.stdin.write(input.encode("utf8"))
  process.stdin.write(b"\n\n") # signal end of documents
  process.stdin.flush()
  response = b""
  while True:
    line = process.stdout.readline()
    print(line.strip())
    if line.strip().startswith("1\tPARSEFINISHED"):
      if process == pos_tagger:
        response += line
      break

    response += line
  return response.decode("utf8")

# Open the part-of-speech tagger.
pos_tagger = open_parser_eval([
    "--input=stdin",
    "--output=stdout-conll",
    "--hidden_layer_sizes=64",
    "--arg_prefix=brain_tagger",
    "--graph_builder=structured",
    "--task_context=" + MODEL_DIR + "/context.pbtxt",
    "--model_path=" + MODEL_DIR + "/tagger-params",
    "--slim_model",
    "--batch_size=1024",
    "--alsologtostderr",
  ])

# Open the syntactic dependency parser.
dependency_parser = open_parser_eval([
    "--input=stdin-conll",
    "--output=stdout-conll",
    "--hidden_layer_sizes=512,512",
    "--arg_prefix=brain_parser",
    "--graph_builder=structured",
    "--task_context=" + MODEL_DIR + "/context.pbtxt",
    "--model_path=" + MODEL_DIR + "/parser-params",
    "--slim_model",
    "--batch_size=1024",
    "--alsologtostderr",
  ])

def split_tokens(parse):
  # Format the result.
  def format_token(line):
    x = OrderedDict(zip(
     ["index", "token", "unknown1", "label", "pos", "unknown2", "parent", "relation", "unknown3", "unknown4"],
     line.split("\t")
    ))
    x["index"] = int(x["index"])
    x["parent"] = int(x["parent"])
    del x["unknown1"]
    del x["unknown2"]
    del x["unknown3"]
    del x["unknown4"]
    return x
                                   
  return [
    format_token(line)
    for line in parse.strip().split("\n")
  ]

# We show different information on a single-flag parse (web) than on a multi-flag
# parse (JSON response). This really should be one method, but until then this is
# slightly faster to implement

def parse_single_flag(flag):
  if "\n" in flag or "\r" in flag:
    raise ValueError()

  # Do POS tagging.
  pos_tags = send_input(pos_tagger, flag + "\n")

  # Do syntax parsing.
  dependency_parse = send_input(dependency_parser, pos_tags)

  tokenizer = subprocess.Popen(["ruby", "parse.rb"],
    cwd=os.getcwd(),
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE)

  tokenizer.stdin.write(dependency_parse.encode('utf8'))
  tokenizer.stdin.write(b"\n\n") # signal end
  tokenizer.stdin.flush()

  response = b""
  while True:
   line = tokenizer.stdout.readline()
   if "FINISHED" in line:
     break
   if len(line) > 1:
     response += line

  response = response.lower()

  parses = response.decode('utf8').split("\n")
  parses = filter(None, parses) # filter out blank strings

  print(len(parses))
  print(parses)

  raw_result, scores = cnntest.test_single_flag(parses)

  return (scores, parses, raw_result)

def parse_flags(flags):
  all_parses = []

  # Do POS tagging.
  print(datetime.datetime.now())
  pos_tags = send_input(pos_tagger, "\n".join(flags) + "\nPARSEFINISHED\n")
  print(datetime.datetime.now())

  print pos_tags
  print len(pos_tags)

  dependency_parsings = send_input(dependency_parser, pos_tags + "\n").split("\n\n")
  print dependency_parsings

  for dependency_parse in dependency_parsings:
    # Do syntax parsing.

    dependency_parse = os.linesep.join([s for s in dependency_parse.splitlines() if s.strip()])

    print(datetime.datetime.now())

    tokenizer = subprocess.Popen(["ruby", "parse.rb"],
      cwd=os.getcwd(),
      stdin=subprocess.PIPE,
      stdout=subprocess.PIPE)

    print(datetime.datetime.now())

    tokenizer.stdin.write(dependency_parse.encode('utf8'))
    tokenizer.stdin.write(b"\n\n") # signal end
    tokenizer.stdin.flush()

    print(dependency_parse.encode('utf8'))

    response = b""
    while True:
     line = tokenizer.stdout.readline()
     if "FINISHED" in line:
       break
     if len(line) > 1:
       response += line

    response = response.lower()

    parses = response.decode('utf8').split("\n")
    parses = [parse for parse in parses if parse != [] and parse != None and parse != ""]

    print(datetime.datetime.now())

    print(len(parses))
    print(parses)

    all_parses.append(parses)


  all_parses = [parse for parse in all_parses if len([n for n in parse if n != None and n != ""]) >= 1]
  print all_parses
  print len(all_parses)

  results = cnntest.test_multiple_flags(all_parses)

  print(datetime.datetime.now())

  return results

#  return render_template('template.html', scores=cnntest.test_paths(parses), flag=flag, parses=parses)

  return dependency_parse.decode('utf8')

  # Make a tree.
  dependency_parse = split_tokens(dependency_parse)

  tokens = { tok["index"]: tok for tok in dependency_parse }
  tokens[0] = OrderedDict([ ("flag", flag) ])
  for tok in dependency_parse:
     tokens[tok['parent']]\
       .setdefault('tree', OrderedDict()) \
       .setdefault(tok['relation'], []) \
       .append(tok)
     del tok['parent']
     del tok['relation']

  return tokens[0]
