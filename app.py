# app.py (نسخة مبسطة لـ Vercel)
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return 'مرحباً بك في ChaletHub! التطبيق يعمل بشكل صحيح.'

@app.route('/api/test')
def test():
    return {'status': 'success', 'message': 'API تعمل بشكل صحيح'}

if __name__ == '__main__':
    app.run()
