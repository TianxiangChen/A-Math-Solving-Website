#!/usr/bin/env python3
import sys
import base64
import requests
import json
import re
import sympy
from latex2sympy import process_latex
from math_recog.math_account import math_acc_config
'''
Input: a path for a picture which contains some math equations
the file_path should be from S3
Output: a string which converted by recogning the input photo, in a
latex format.
'''
def math_recog(file_path):
    image_uri = "data:image/jpg;base64," + base64.b64encode(open(file_path, "rb").read()).decode('utf-8')
    r = requests.post("https://api.mathpix.com/v3/latex",
        data=json.dumps({'url': image_uri}),
        headers={"app_id": math_acc_config['email'], "app_key": math_acc_config['pass'],
            "Content-type": "application/json"})
    result = json.dumps(json.loads(r.text), indent=4, sort_keys=True)
    print(result)
    return post_process_latex(json.loads(result).get('latex'))

def post_process_latex(latex_str):
    # remove \\operatorname{}
    res = re.match(r'.*operatorname\{(\w+)\}.*', latex_str)

    if res:
        operator = res.group(1)
        return latex_str.replace('operatorname{%s}'%operator, operator)
    # 12\\longdiv { 144}"
    res = re.match(r'(.*)\\longdiv.*\{(.*)\}', latex_str)
    if res:
        return '\\frac{%s}{%s}' % (res.group(2).strip(), res.group(1).strip())

    return latex_str


def calculate_latex(latex_str, latex_out=False):
    expression = process_latex.process_sympy(latex_str)
    result = expression.doit()
    if latex_out:
        return sympy.latex(result)
    return result


def process_img(path_to_image):
    """Recognize the formula in the picture
    :param path_to_image: path to the picture, preferably absolute path
    :return: recognized latex and result latex
    """
    recognized_latex = math_recog(path_to_image)
    return recognized_latex, calculate_latex(recognized_latex, latex_out=True)

if __name__ == '__main__':
    print(post_process_latex('12\\longdiv { 144}'))
    # a = calculate_latex(post_process_latex('12\\longdiv { 144}'))
    # print(sympy.latex(a))
    # print(process_img('/Users/luyuanchen/Desktop/5.JPG'))
