from flask import Flask, render_template, request
from dataclasses import dataclass
import requests
import json
from decouple import config
import pika

app = Flask(__name__)

@dataclass
class Product:
    uuid: str
    product: str
    price: float

@dataclass
class Order:
    def __init__(self, name: str, email: str, phone: str, product_id: str):
        self.Name = name
        self.Email = email
        self.Phone = phone
        self.ProductId = product_id


products_url = config("PRODUCT_URL") or 'http://localhost:8080'

def connect():
    #dsn = "amqp://rabbitmq:rabbitmq@localhost:5672/"
    dsn = f"amqp://{config('RABBITMQ_DEFAULT_USER')}:{config('RABBITMQ_DEFAULT_PASS')}@{config('RABBITMQ_DEFAULT_HOST')}/"


    print("DSN DO RABBIT")
    print(dsn)
    conn = pika.BlockingConnection(pika.URLParameters(dsn))
    channel = conn.channel()

    return channel


def notify(payload, exchange, routing_key, ch):
    ch.basic_publish(exchange=exchange,
                     routing_key=routing_key,
                     body=payload,
                     properties=pika.BasicProperties(
                         content_type="application/json"))

    print("Message sent")


@app.route('/<string:id>')
def display_checkout(id: str):  
    response = requests.get(f"{products_url}/{id}")

    if response.status_code != 200:
        print(f"The HTTP request failed with error {response.status}")
        return "Error fetching product information", response.status

    product = response.json()
    product_obj = Product(product["uuid"], product["product"], float(product["price"]))

    return render_template('checkout.html', product=product_obj)


@app.route('/')
def index():
    return render_template('checkout.html')

@app.route('/finish', methods=['POST'])
def finish():
    order = Order(
        name=request.form.get('name'),
        email=request.form.get('email'),
        phone=request.form.get('phone'),
        product_id=request.form.get('product_id')
    )

    data = json.dumps(order.__dict__)
    print(data)

    connection = connect()
    notify(data, "checkout_ex", "", connection)

    return "Processou!"


@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
