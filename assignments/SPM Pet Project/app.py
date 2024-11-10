# app.py
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    products = [
        {
            'title': 'AI-Powered Chatbot',
            'description': 'Enhance customer support with our intelligent chatbot solution.',
            'image': '/static/images/chatbot.jpg'
        },
        {
            'title': 'Commissions Estimator',
            'description': 'Accurately forecast and calculate sales commissions with ease.',
            'image': '/static/images/commissions.jpg'
        },
        {
            'title': 'Real-Time Insights Dashboard',
            'description': 'Get instant access to critical sales performance metrics.',
            'image': '/static/images/dashboard.jpg'
        },
        {
            'title': 'Gamification App',
            'description': 'Motivate your sales team with engaging gamification features.',
            'image': '/static/images/gamification.jpg'
        }
    ]
    return render_template('index.html', products=products)

if __name__ == '__main__':
    app.run(debug=True)

# templates/base.html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Sales Performance Management Solutions{% endblock %}</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100">
    <header class="bg-blue-600 text-white p-4">
        <h1 class="text-3xl font-bold">Sales Performance Management Solutions</h1>
    </header>
    
    <main class="container mx-auto mt-8">
        {% block content %}{% endblock %}
    </main>
    
    <footer class="bg-gray-200 mt-12 py-6 text-center">
        <p>&copy; 2024 Sales Performance Management Solutions. All rights reserved.</p>
    </footer>
</body>
</html>

# templates/index.html
{% extends "base.html" %}

{% block content %}
<section class="grid grid-cols-1 md:grid-cols-2 gap-8">
    {% for product in products %}
    <div class="bg-white p-6 rounded-lg shadow-md">
        <h2 class="text-2xl font-semibold mb-4">{{ product.title }}</h2>
        <div class="aspect-w-16 aspect-h-9 mb-4">
            <img src="{{ product.image }}" alt="{{ product.title }} Demo" class="rounded-lg object-cover" />
        </div>
        <p>{{ product.description }}</p>
    </div>
    {% endfor %}
</section>
{% endblock %}

# Directory structure:
# /your_project
#   /static
#     /images
#       chatbot.jpg
#       commissions.jpg
#       dashboard.jpg
#       gamification.jpg
#   /templates
#     base.html
#     index.html
#   app.py
#   requirements.txt