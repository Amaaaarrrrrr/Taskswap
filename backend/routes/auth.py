from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity
)
from datetime import timedelta

from models import User, Task, SwapRequest, Review
from extensions import db

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://username:password@localhost:5432/taskswap'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'super-secret-key'  # Change this!
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=15)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=7)

db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

# -----------------------------
# Auth Routes
# -----------------------------
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    hashed_password = generate_password_hash(data['password'])
    user = User(
        name=data['name'],
        email=data['email'],
        password_hash=hashed_password
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if user and check_password_hash(user.password_hash, data['password']):
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        return jsonify({'access_token': access_token, 'refresh_token': refresh_token})
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/refresh-token', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify({'access_token': access_token})

@app.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    # Optional: Implement token blacklist if desired
    return jsonify({'message': 'Logout successful'})


# -----------------------------
# User Routes
# -----------------------------
@app.route('/profile/<int:user_id>', methods=['GET'])
@jwt_required()
def get_profile(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.serialize())

@app.route('/users', methods=['GET'])
@jwt_required()
def list_users():
    # Example filters: ?name=alice&skill=python
    name = request.args.get('name')
    skill = request.args.get('skill')
    query = User.query
    if name:
        query = query.filter(User.name.ilike(f'%{name}%'))
    if skill:
        query = query.filter(User.skills.ilike(f'%{skill}%'))
    users = query.all()
    return jsonify([u.serialize() for u in users])


# -----------------------------
# Task Routes
# -----------------------------
@app.route('/tasks', methods=['POST'])
@jwt_required()
def create_task():
    data = request.get_json()
    user_id = get_jwt_identity()
    task = Task(
        title=data['title'],
        description=data.get('description', ''),
        category=data.get('category', ''),
        created_by=user_id
    )
    db.session.add(task)
    db.session.commit()
    return jsonify(task.serialize()), 201

@app.route('/tasks', methods=['GET'])
@jwt_required()
def list_tasks():
    tasks = Task.query.all()
    return jsonify([t.serialize() for t in tasks])

@app.route('/tasks/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id):
    task = Task.query.get_or_404(task_id)
    return jsonify(task.serialize())

@app.route('/tasks/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    task = Task.query.get_or_404(task_id)
    data = request.get_json()
    for field in ['title', 'description', 'status', 'assigned_to', 'category']:
        if field in data:
            setattr(task, field, data[field])
    db.session.commit()
    return jsonify(task.serialize())

@app.route('/tasks/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return jsonify({'message': 'Task deleted'})


# -----------------------------
# SwapRequest Routes
# -----------------------------
@app.route('/swap', methods=['POST'])
@jwt_required()
def create_swap_request():
    data = request.get_json()
    user_id = get_jwt_identity()
    swap = SwapRequest(
        task_id=data['task_id'],
        requester_id=user_id
    )
    db.session.add(swap)
    db.session.commit()
    return jsonify(swap.serialize()), 201

@app.route('/swap/<int:swap_id>/accept', methods=['POST'])
@jwt_required()
def accept_swap(swap_id):
    swap = SwapRequest.query.get_or_404(swap_id)
    task = swap.task
    user_id = get_jwt_identity()
    if task.created_by != user_id:
        return jsonify({'error': 'Only task owner can accept'}), 403
    swap.status = 'accepted'
    task.assigned_to = swap.requester_id
    db.session.commit()
    return jsonify(swap.serialize())

@app.route('/swap/<int:swap_id>/reject', methods=['POST'])
@jwt_required()
def reject_swap(swap_id):
    swap = SwapRequest.query.get_or_404(swap_id)
    user_id = get_jwt_identity()
    if swap.task.created_by != user_id:
        return jsonify({'error': 'Only task owner can reject'}), 403
    swap.status = 'rejected'
    db.session.commit()
    return jsonify(swap.serialize())


# -----------------------------
# Review Routes
# -----------------------------
@app.route('/reviews', methods=['POST'])
@jwt_required()
def create_review():
    data = request.get_json()
    review = Review(
        reviewer_id=get_jwt_identity(),
        reviewee_id=data['reviewee_id'],
        task_id=data['task_id'],
        rating=data['rating'],
        comment=data.get('comment', '')
    )
    db.session.add(review)
    db.session.commit()
    return jsonify(review.serialize()), 201

@app.route('/reviews', methods=['GET'])
@jwt_required()
def list_reviews():
    task_id = request.args.get('task_id')
    user_id = request.args.get('user_id')
    query = Review.query
    if task_id:
        query = query.filter_by(task_id=task_id)
    if user_id:
        query = query.filter_by(reviewee_id=user_id)
    reviews = query.all()
    return jsonify([r.serialize() for r in reviews])


if __name__ == '__main__':
    app.run(debug=True)
