import os
import json
import pandas as pd
from app import app
from flask import render_template, redirect, url_for, request, send_file

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/display_form', methods=['GET'])
def display_form():
    return render_template("extract.html")

@app.route('/display_form', methods=['POST'])
def extract_post():
    product_id = request.form.get('product_id')
    return redirect(url_for('product', product_id=product_id))

# @app.route('/products')
# def products():
#     products = os.listdir("./app/data/products")
#     return render_template("products.html", products=products)

@app.route('/products')
def products():
  products_dir = "app/data/products"
  products = []
  for filename in os.listdir(products_dir):
    if filename.endswith('.json'):
      file_path = os.path.join(products_dir, filename)
      with open(file_path, 'r', encoding='utf-8') as file:
        product = json.load(file)  
        products.append(product)  
  return render_template('products.html', products=products)

@app.route('/author')
def author():
    return render_template("author.html")

@app.route('/product/<int:product_id>')
def product(product_id:int):
  with open(f"app/data/opinions/{product_id}.json", 'r', encoding='utf-8') as jf:
    try:
      opinions = json.load(jf)
    except json.JSONDecodeError:
      error= "Nie pobrano danych"
      return render_template("product.html", error=error)
    opinions = pd.DataFrame.from_dict(opinions)
    return render_template("product.html", opinions=opinions)

@app.route('/download/<int:product_id>/<file_type>')
def download_file(product_id, file_type):
    file_path = f"app/data/products/{product_id}.{file_type}"
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return "Plik nie istnieje", 404
