from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/AnantGyanDB"
app.secret_key = "supersecretkey"
mongo = PyMongo(app)

#---------------------------------------------------------------------------------------------------------

@app.route('/')
def index():
    return render_template('main.html')

# code for the login page where the user can login to the website
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = mongo.db.users.find_one({"username": username})
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            session['username'] = username
            return redirect(url_for('user_home'))
        else:
            return "Invalid username or password"

    return render_template('login.html')

# code for the registration page where the user can register to the website
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirmation = request.form['confirmation']
        
        if password == confirmation:
            hashed_password = generate_password_hash(password)
            mongo.db.users.insert_one({
                "username": username,
                "email": email,
                "password": hashed_password
            })
            return redirect(url_for('login'))
        else:
            return "Passwords do not match"

    return render_template('register.html')

# code for the user home page where the user can see the home page after logging in
@app.route('/user_home')
def user_home():
    if 'user_id' in session:
        return render_template('user.html', username=session['username'])
    return redirect(url_for('login'))

# code for the writer page where the user can write the content
@app.route('/writer', methods=['GET', 'POST'])
def writer():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.json['title']
        content = request.json['content']
        publisher = session['username']
        user_id = session['user_id']
        mongo.db.ag_writers_field.insert_one({
            "title": title,
            "content": content,
            "publisher": publisher,
            "user_id": ObjectId(user_id)
        })
        return jsonify({"message": "success"})
    
    return render_template('writer.html')

# code for the viewer page where the user can see the content written by the writer
@app.route('/ag_viewers', methods=['GET'])
def ag_viewers():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    ag_writers_field = mongo.db.ag_writers_field.find({"user_id": ObjectId(user_id)})
    return render_template('ag_viewers.html', ag_writers_field=ag_writers_field)

# code for the reader page where the user can read the content written by the writer
@app.route('/reader')
def reader():
    ag_writers_field = mongo.db.ag_writers_field.find()
    return render_template('reader.html', ag_writers_field=ag_writers_field)


# code for the delete, update, edit, and logout functionality

@app.route('/delete/<id>', methods=['DELETE'])
def delete(id):
    if 'user_id' not in session:
        return jsonify({"message": "error"}), 403  # Forbidden
    
    user_id = session['user_id']
    ag_writer = mongo.db.ag_writers_field.find_one({"_id": ObjectId(id)})
    
    if ag_writer and ag_writer['user_id'] == ObjectId(user_id):
        mongo.db.ag_writers_field.delete_one({"_id": ObjectId(id)})
        return jsonify({"message": "success"})
    
    return jsonify({"message": "error"}), 400

# code for the update functionality where the user can update the content
@app.route('/update/<id>', methods=['PUT'])
def update(id):
    if 'user_id' not in session:
        return jsonify({"message": "error"}), 403  # Forbidden
    
    user_id = session['user_id']
    ag_writer = mongo.db.ag_writers_field.find_one({"_id": ObjectId(id)})
    
    if ag_writer and ag_writer['user_id'] == ObjectId(user_id):
        data = request.get_json()
        title = data.get('title')
        content = data.get('content')
        mongo.db.ag_writers_field.update_one(
            {"_id": ObjectId(id)},
            {"$set": {"title": title, "content": content}}
        )
        return jsonify({"message": "success"})
    
    return jsonify({"message": "error"}), 400  # Bad request

# code for the edit functionality where the user can edit the content
@app.route('/edit/<id>', methods=['GET'])
def edit(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    ag_writer = mongo.db.ag_writers_field.find_one({"_id": ObjectId(id)})
    
    if ag_writer and ag_writer['user_id'] == ObjectId(user_id):
        return render_template('edit.html', item=ag_writer)
    
    return redirect(url_for('ag_viewers'))

# code for the logout functionality where the user can logout from the website

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

#---------------------------------------------------------------------------------------------------------

# code for the cluster functionality where the user can create a cluster and add the content to the cluster
@app.route('/content/<id>')
def view_content(id):
    content = mongo.db.ag_writers_field.find_one({"_id": ObjectId(id)})
    if content:
        return render_template('content_page.html', content=content)
    return redirect(url_for('reader'))

# code for the cluster functionality where the user can create a cluster and add the content to the cluster
@app.route('/cluster', methods=['GET', 'POST'])
def cluster():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        cluster_name = request.form['cluster_name']
        user_id = session['user_id']
        mongo.db.ag_clusters.insert_one({
            "cluster_name": cluster_name,
            "user_id": ObjectId(user_id)
        })
        return redirect(url_for('select_cluster'))
    
    user_id = session['user_id']
    ag_clusters = mongo.db.ag_clusters.find({"user_id": ObjectId(user_id)})
    return render_template('cluster.html', ag_clusters=ag_clusters)

# code for the select cluster functionality where the user can select the cluster and add the content to the cluster
@app.route('/select_cluster', methods=['GET', 'POST'])
def select_cluster():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    ag_clusters = mongo.db.ag_clusters.find({"user_id": ObjectId(user_id)})
    ag_writers_field = mongo.db.ag_writers_field.find({"user_id": ObjectId(user_id)})

    if request.method == 'POST':
        cluster_id = request.form['cluster_id']
        selected_content = request.form.getlist('selected_content')

        for content_id in selected_content:
            mongo.db.ag_writers_field.update_one(
                {"_id": ObjectId(content_id)},
                {"$set": {"cluster_id": ObjectId(cluster_id)}}
            )

        return redirect(url_for('user_home'))

    return render_template('select_cluster.html', ag_clusters=ag_clusters, ag_writers_field=ag_writers_field)
#
# code for the view clusters functionality where the user can view the clusters created by the user
@app.route('/view_clusters')
def view_clusters():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    clusters = mongo.db.ag_clusters.find({"user_id": ObjectId(user_id)})
    clusters_with_content = []

    for cluster in clusters:
        contents = mongo.db.ag_writers_field.find({"cluster_id": ObjectId(cluster['_id'])})
        clusters_with_content.append({
            "cluster": cluster,
            "contents": contents
        })

    return render_template('view_clusters.html', clusters_with_content=clusters_with_content)

# code for the delete cluster functionality where the user can delete the cluster
@app.route('/delete_cluster/<id>', methods=['DELETE'])
def delete_cluster(id):
    if 'user_id' not in session:
        return jsonify({"message": "error"}), 403  # Forbidden
    
    user_id = session['user_id']
    cluster = mongo.db.ag_clusters.find_one({"_id": ObjectId(id)})
    
    if cluster and cluster['user_id'] == ObjectId(user_id):
        mongo.db.ag_clusters.delete_one({"_id": ObjectId(id)})
        mongo.db.ag_writers_field.update_many({"cluster_id": ObjectId(id)}, {"$unset": {"cluster_id": ""}})
        return jsonify({"message": "success"})
    
    return jsonify({"message": "error"}), 400

# code for the delete content functionality where the user can delete the content
@app.route('/delete_content/<id>', methods=['DELETE'])
def delete_content(id):
    if 'user_id' not in session:
        return jsonify({"message": "error"}), 403  # Forbidden
    
    user_id = session['user_id']
    content = mongo.db.ag_writers_field.find_one({"_id": ObjectId(id)})
    
    if content and content['user_id'] == ObjectId(user_id):
        mongo.db.ag_writers_field.delete_one({"_id": ObjectId(id)})
        return jsonify({"message": "success"})
    
    return jsonify({"message": "error"}), 400

@app.route('/group_page')
def group_page():
    return render_template('group_page.html')

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == "__main__":
    app.run(debug=True)
