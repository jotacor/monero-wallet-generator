#!/home/monero/venv/bin/python
# coding=utf-8

from base64 import b64encode
from bottle import route, run, hook, response
from glob import glob
import jinja2
import json
import os
from random import randint
import re
import subprocess as sp
from weasyprint import HTML

@hook('after_request')
def enable_cors():
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET'
    response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'
    response.headers['Content-Type'] = 'application/json; charset=utf-8'


@route('/localapi/create_wallet', method='GET')
def create_wallet():
    wallet = '/tmp/wallet_%s' % randint (1, 10000) 
    proc = sp.Popen(('monero-wallet-cli', '--generate-new-wallet', wallet, '--password', '""', '--mnemonic-language', 'English', '--command', 'exit'), stdout=sp.PIPE)
    lines = ''
    out, err = proc.communicate()
    lines = out.decode("utf-8")
    address = re.search('Generated new wallet: (\w+)', lines).group(1)
    view = re.search('View key: (\w+)', lines).group(1)
    seed = ' '.join(lines.split('\n')[-5:-2])
    pdf = create_pdf(address=address, view=view, seed=seed)

    for file in glob('/tmp/wallet*'):
        os.remove(file)

    reply = '{"address":"%s","view":"%s","seed":"%s","pdf":"%s"}' % (address, view, seed, pdf)
    json_string = json.dumps(reply, ensure_ascii=False)
    return json.loads(json_string)


def render(tpl_path, context):
    path, filename = os.path.split(tpl_path)
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(path or './')
    ).get_template(filename).render(context)


def create_pdf(address=None, view=None, seed=None):
    context = dict(address=address, view=view, seed=seed)
    html = HTML(string=render('template.html', context))
    pdf = html.write_pdf()
    basepdf = b64encode(pdf)
    return basepdf.decode("utf-8")

run(host='0.0.0.0', port=8080)
