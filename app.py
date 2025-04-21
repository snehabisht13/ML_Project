from flask import Flask, render_template, jsonify, request
from flask_mail import Mail, Message
import pandas as pd
from sklearn.cluster import KMeans

app = Flask(__name__)

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'sneha040222@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'agzl upvq rulm ctee'    # Use an app-specific password
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)

# Load and process data
df = pd.read_csv('Mall_Customers_with_email.csv')

# Clustering based on Income & Spending Score
X = df[['Annual Income (k$)', 'Spending Score (1-100)']]
kmeans = KMeans(n_clusters=4, random_state=42)
df['Cluster'] = kmeans.fit_predict(X)

# Basic coupon mapping
def recommend_coupon(cluster_id):
    coupons = {
        0: "💎 20% off Premium Brands",
        1: "🛒 Save on Essentials - Flat ₹100 Off",
        2: "👗 Fashion Fiesta: Buy 1 Get 1",
        3: "🎁 Loyalty Bonus: Extra Points",
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

    cluster_data = df[df['Cluster'] == cluster_id]
    return render_template('cluster_customers.html', cluster_id=cluster_id, customers=cluster_data.to_dict(orient='records'))

# API: Send coupon via email to a customer
@app.route('/send_coupon/<int:customer_id>')
def send_coupon(customer_id):
    customer = df[df['CustomerID'] == customer_id].iloc[0]
    email = customer['email']
    coupon = recommend_coupon(customer['Cluster'])

    msg = Message('Your Personalized Coupon', sender='sneha040222@gmail.com', recipients=[email])
    msg.body = f"Hello Customer,\n\nHere is your exclusive coupon:\n{coupon}\n\nEnjoy shopping!"

    try:
        mail.send(msg)
        return f"Coupon sent to {email}!"
    except Exception as e:
        return f"Error: {str(e)}"

# new customer 
@app.route('/recommend-coupon', methods=['POST'])
def recommend_coupon_form():
    customer_id = request.form['customer_id']
    email = request.form['email']
    spending_score = int(request.form['spending_score'])
    annual_income = float(request.form['annual_income'])

    # Predict cluster using KMeans model
    cluster = kmeans.predict([[annual_income, spending_score]])[0]
    coupon = recommend_coupon(cluster)

    # Render a page with coupon details and send button
    return render_template('coupon_result.html', 
                           customer_id=customer_id,
                           email=email,
                           spending_score=spending_score,
                           annual_income=annual_income,
                           cluster=cluster,
                           coupon=coupon)

# sending coupon to new user 
@app.route('/send_coupon_direct', methods=['POST'])
def send_coupon_direct():
    email = request.form['email']
    coupon = request.form['coupon']

    msg = Message('Your Personalized Coupon', sender='sneha040222@gmail.com', recipients=[email])
    msg.body = f"Hello,\n\nHere is your personalized coupon:\n{coupon}\n\nEnjoy your shopping experience!"

    try:
        mail.send(msg)
        return f"<h3>Coupon sent successfully to {email}!</h3>"
    except Exception as e:
        return f"<h3>Error sending email: {str(e)}</h3>"


# Homepage: Cluster visualization
# Homepage: Cluster visualization
@app.route('/')
def home():
    cluster_counts = []
    
    # Manual labeling for each cluster based on cluster index
    cluster_labels = {
        0: "Low income, low spender",
        1: "Moderate income, high spender",
        2: "High income, frequent spender",
        3: "Mid-income, average spender"
    }

    for i in range(4):
        cluster_data = df[df['Cluster'] == i]
        cluster_counts.append(len(cluster_data))

    # Ensure labels are ordered by cluster index
    cluster_ranges = [cluster_labels[i] for i in range(4)]

    return render_template('index.html', cluster_counts=cluster_counts, cluster_ranges=cluster_ranges)

if __name__ == '__main__':
    app.run(debug=True)
