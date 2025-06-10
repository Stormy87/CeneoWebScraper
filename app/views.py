import os
import json
from flask import requests
import pandas as pd
from bs4 import BeautifulSoup
from app import app
from flask import render_template, redirect, url_for, request, send_file


  
def extract(ancestor, selector, attribute=None, multiple=False):
  if selector:
    if multiple:
      if attribute:
        return [tag[attribute].strip() for tag in ancestor.select(selector) if tag.has_attr(attribute)]
      return [tag.text.strip() for tag in ancestor.select(selector) if tag.text.strip()]
    if attribute:
        try:
            return ancestor.select_one(selector)[attribute].strip(),
        except (TypeError, AttributeError):
            return None,
    else:
        try:
            return ancestor.select_one(selector).text.strip(),
        except AttributeError:
            return None,
  if attribute:
    return ancestor[attribute].strip()
  return None

selectors = {
  "opinion_id": ( None, "data-entry-id"),
  "author": ("span.user-post__author-name",),
  "recommendation": ("span.user-post__author-recommendation > em",),
  "stars": ( "span.user-post__score-count",),
  "content": ("div.user-post__text",),
  "pros": ( "div.review-feature__item--positive", None, True),
  "cons": ("div.review-feature__item--negative", None, True),
  "useful": ("button.vote-yes","data-total-vote"),
  "useless": ("button.vote-no","data-total-vote"),
  "post_date": ("span.user-post__published > time:nth-child(1)", "datetime"),
  "purchase_date": ( "span.user-post__published > time:nth-child(2)", "datetime"),
}


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

@app.route('/extract', methods=['POST'])
def extract_data():
  product_id = request.form.get('product_id')
  url = f"https://www.ceneo.pl/{product_id}#tab=reviews"
  while url:
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
      page_dom = BeautifulSoup(response.text, 'html.parser')
      opinions = page_dom.select('div.js_product-review:not(.user-post--highlight)')
      if opinions:
        all_opinions = []
        for opinion in opinions:
          single_opinion = {
            key: extract(opinion, *value) for key, value in selectors.items()
          }
          all_opinions.append(single_opinion)
        try:
          url = "https://ceneo.pl"+extract(page_dom, "a.pagination__next", "href")
        except TypeError:
          url = None
    else:
      error = "Coś poszło nie tak"
      return render_template("extract.html", error=error)
  else:
      error = "Coś poszło nie tak"
      return render_template("extract.html", error=error)
  if not os.path.exists("./app/data"):
    os.makedirs("./app/data")
  if not os.path.exists("./app/data/opinions"):
    os.makedirs("./app/data/opinions")
  with open(f"./app/data/opinions/{product_id}.json", 'w', encoding='utf-8') as file:
    json.dump(all_opinions, file, ensure_ascii=False, indent=4)
  return redirect(url_for('product', product_id=product_id))

    # error = "Coś poszło nie tak"
    # return render_template("extract.html", error=error)


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
  try:
    with open(f"app/data/opinions/{product_id}.json", 'r', encoding='utf-8') as jf:
      try:
        opinions = json.load(jf)
      except json.JSONDecodeError:
        error= "Nie pobrano danych"
        return render_template("product.html", error=error)
      opinions = pd.DataFrame.from_dict(opinions)
      return render_template("product.html", opinions=opinions)
  except FileNotFoundError:
    error = "Nie znaleziono pliku z danymi"
  return render_template("product.html", error=error)

@app.route('/download/<int:product_id>/<file_type>')
def download_file(product_id, file_type):
    file_path = f"app/data/products/{product_id}.{file_type}"
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return "Plik nie istnieje", 404
