from flask import Flask, render_template, jsonify, request
from flask_mail import Mail, Message
import pandas as pd
from sklearn.cluster import KMeans

app = Flask(__name__)

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'sneha040222@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'agzl upvq rulm ctee'  # Replace with your email password or app-specific password
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)

# Load and process data
df = pd.read_csv('Mall_Customers_with_email.csv')

# Clustering based on Income & Spending Score
X = df[['Annual Income (k$)', 'Spending Score (1-100)']]
kmeans = KMeans(n_clusters=5, random_state=42)
df['Cluster'] = kmeans.fit_predict(X)

# Basic coupon mapping
def recommend_coupon(cluster_id):
    coupons = {
        0: "💎 20% off Premium Brands",
        1: "🛒 Save on Essentials - Flat ₹100 Off",
        2: "👗 Fashion Fiesta: Buy 1 Get 1",
        3: "🎁 Loyalty Bonus: Extra Points",
        4: "💰 Cashback Week - 10% back on every purchase"
    }
    return coupons.get(cluster_id, "🎉 General Discount: Flat 5% Off")

# API: Get cluster data (number of customers, coupon recommendation, etc.)
@app.route('/api/cluster/<int:cluster_id>')
def get_cluster_data(cluster_id):
    if cluster_id < 0 or cluster_id >= 5:
        return jsonify({'error': 'Invalid cluster number'}), 400
    
    cluster_data = df[df['Cluster'] == cluster_id]
    number_of_customers = cluster_data.shape[0]
    average_spending = cluster_data['Spending Score (1-100)'].mean()
    
    coupon = recommend_coupon(cluster_id)

    return jsonify({
        'clusterId': cluster_id,
        'customers': number_of_customers,
        'averageSpending': average_spending,
        'coupon': coupon
    })

# API: Get all customers in a selected cluster
@app.route('/cluster/<int:cluster_id>')
def cluster_customers(cluster_id):
    if cluster_id < 0 or cluster_id >= 5:
        return render_template('error.html', message="Invalid Cluster ID"), 404
    
    # Get all customers for the selected cluster
    cluster_data = df[df['Cluster'] == cluster_id]
    return render_template('cluster_customers.html', cluster_id=cluster_id, customers=cluster_data.to_dict(orient='records'))

# API: Send coupon via email to a customer
@app.route('/send_coupon/<int:customer_id>')
def send_coupon(customer_id):
    customer = df[df['CustomerID'] == customer_id].iloc[0]
    email = customer['email']
    coupon = recommend_coupon(customer['Cluster'])

    msg = Message('Your Personalized Coupon', sender='your_email@gmail.com', recipients=[email])
    msg.body = f"Hello customer ,\n\nHere is your exclusive coupon:\n{coupon}\n\nEnjoy shopping!"

    try:
        mail.send(msg)
        return f"Coupon sent to {email}!"
    except Exception as e:
        return f"Error: {str(e)}"

# New customer form for predicting cluster and sending coupon
@app.route('/new_customer', methods=['GET', 'POST'])
def new_customer():
    if request.method == 'POST':
        income = request.form['income']
        spending_score = request.form['spending_score']
        
        # Predict the cluster for the new customer
        new_customer_data = [[income, spending_score]]
        predicted_cluster = kmeans.predict(new_customer_data)[0]
        
        # Recommend coupon for this cluster
        coupon = recommend_coupon(predicted_cluster)
        
        # Optionally, you can send the coupon to a new email or display it on the page
        # email = request.form['email']
        # send_coupon_email(email, coupon)  # Optionally send coupon via email
        
        return render_template('new_customer_result.html', predicted_cluster=predicted_cluster, coupon=coupon)

    return render_template('new_customer_form.html')

# Homepage: Cluster visualization
@app.route('/')
def home():
    # Get the number of customers in each cluster
    cluster_counts = []
    for i in range(5):
        cluster_data = df[df['Cluster'] == i]
        cluster_counts.append(len(cluster_data))  # Number of customers in the cluster

    return render_template('index.html', cluster_counts=cluster_counts)

if __name__ == '__main__':
    app.run(debug=True)
