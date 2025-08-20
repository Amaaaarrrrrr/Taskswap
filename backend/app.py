from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity
)
from datetime import timedelta
from functools import wraps
from extensions import db
from models import User, Task, SwapRequest, Review
import csv
import io

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://taskswap_user:taskswap@localhost/taskswap_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'super-secret-key'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=15)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=7)

db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)


# -----------------------------
# Helper: Admin decorator
# -----------------------------
def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user or not user.is_admin():
            return jsonify({"error": "Admin access required"}), 403
        return fn(*args, **kwargs)
    return wrapper


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
        password_hash=hashed_password,
        role='user'   # 🔒 always default to user
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
    # optional: implement token blacklist
    return jsonify({'message': 'Logout successful'})


# -----------------------------
# User Routes
# -----------------------------
@app.route('/profile/<int:user_id>', methods=['GET'])
@jwt_required()
def get_profile(user_id):
    current_user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    if current_user_id != user.id and not User.query.get(current_user_id).is_admin():
        return jsonify({'error': 'Access denied'}), 403
    return jsonify(user.serialize())


@app.route('/users', methods=['GET'])
@jwt_required()
def list_users():
    current_user = User.query.get(get_jwt_identity())
    if not current_user.is_admin():
        return jsonify({'error': 'Admin access required'}), 403

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
    current_user_id = get_jwt_identity()
    task = Task(
        title=data['title'],
        description=data.get('description', ''),
        category=data.get('category', ''),
        created_by=current_user_id
    )
    db.session.add(task)
    db.session.commit()
    return jsonify(task.serialize()), 201


@app.route('/tasks', methods=['GET'])
@jwt_required()
def list_tasks():
    current_user = User.query.get(get_jwt_identity())
    if current_user.is_admin():
        tasks = Task.query.all()
    else:
        tasks = Task.query.filter(
            (Task.created_by == current_user.id) | (Task.assigned_to == current_user.id)
        ).all()
    return jsonify([t.serialize() for t in tasks])


@app.route('/tasks/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id):
    task = Task.query.get_or_404(task_id)
    current_user = User.query.get(get_jwt_identity())
    if not current_user.is_admin() and current_user.id not in [task.created_by, task.assigned_to]:
        return jsonify({'error': 'Access denied'}), 403
    return jsonify(task.serialize())


@app.route('/tasks/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    task = Task.query.get_or_404(task_id)
    current_user = User.query.get(get_jwt_identity())
    if not current_user.is_admin() and task.created_by != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

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
    current_user = User.query.get(get_jwt_identity())
    if not current_user.is_admin() and task.created_by != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

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
    current_user_id = get_jwt_identity()
    swap = SwapRequest(
        task_id=data['task_id'],
        requester_id=current_user_id
    )
    db.session.add(swap)
    db.session.commit()
    return jsonify(swap.serialize()), 201


@app.route('/swap/<int:swap_id>/accept', methods=['POST'])
@jwt_required()
def accept_swap(swap_id):
    swap = SwapRequest.query.get_or_404(swap_id)
    current_user_id = get_jwt_identity()
    task = swap.task
    if task.created_by != current_user_id:
        return jsonify({'error': 'Only task owner can accept'}), 403
    swap.status = 'accepted'
    task.assigned_to = swap.requester_id
    db.session.commit()
    return jsonify(swap.serialize())


@app.route('/swap/<int:swap_id>/reject', methods=['POST'])
@jwt_required()
def reject_swap(swap_id):
    swap = SwapRequest.query.get_or_404(swap_id)
    current_user_id = get_jwt_identity()
    task = swap.task
    if task.created_by != current_user_id:
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
    current_user_id = get_jwt_identity()
    review = Review(
        reviewer_id=current_user_id,
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
    return jsonify([r.serialize() for r in query.all()])


# -----------------------------
# ADMIN ROUTES
# -----------------------------
# User management
@app.route('/admin/users', methods=['GET'])
@admin_required
def admin_list_users():
    users = User.query.all()
    return jsonify([u.serialize() for u in users])


@app.route('/admin/users/<int:user_id>', methods=['PUT'])
@admin_required
def admin_update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    if 'role' in data:
        user.role = data['role']
    if 'skills' in data:
        user.skills = data['skills']
    if 'password' in data:
        user.password_hash = generate_password_hash(data['password'])
    db.session.commit()
    return jsonify(user.serialize())


@app.route('/admin/users/<int:user_id>', methods=['DELETE'])
@admin_required
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted'})


# Task management
@app.route('/admin/tasks', methods=['GET'])
@admin_required
def admin_list_tasks():
    tasks = Task.query.all()
    return jsonify([t.serialize() for t in tasks])


@app.route('/admin/tasks/<int:task_id>', methods=['PUT'])
@admin_required
def admin_update_task(task_id):
    task = Task.query.get_or_404(task_id)
    data = request.get_json()
    for field in ['title', 'description', 'status', 'assigned_to', 'category']:
        if field in data:
            setattr(task, field, data[field])
    db.session.commit()
    return jsonify(task.serialize())


@app.route('/admin/tasks/<int:task_id>', methods=['DELETE'])
@admin_required
def admin_delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return jsonify({'message': 'Task deleted'})


# Swap override
@app.route('/admin/swaps/<int:swap_id>/override', methods=['POST'])
@admin_required
def admin_override_swap(swap_id):
    swap = SwapRequest.query.get_or_404(swap_id)
    data = request.get_json()
    if data.get('action') == 'accept':
        swap.status = 'accepted'
        swap.task.assigned_to = swap.requester_id
    elif data.get('action') == 'reject':
        swap.status = 'rejected'
    else:
        return jsonify({'error': 'Invalid action'}), 400
    db.session.commit()
    return jsonify(swap.serialize())


# Review moderation
@app.route('/admin/reviews/<int:review_id>', methods=['DELETE'])
@admin_required
def admin_delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    db.session.delete(review)
    db.session.commit()
    return jsonify({'message': 'Review deleted'})


# Statistics
@app.route('/admin/stats/users', methods=['GET'])
@admin_required
def admin_user_stats():
    total_users = User.query.count()
    admins = User.query.filter_by(role='admin').count()
    return jsonify({"total_users": total_users, "admins": admins})


@app.route('/admin/stats/tasks', methods=['GET'])
@admin_required
def admin_task_stats():
    total_tasks = Task.query.count()
    completed = Task.query.filter_by(status='completed').count()
    open_tasks = Task.query.filter_by(status='open').count()
    assigned = Task.query.filter(Task.assigned_to.isnot(None)).count()
    return jsonify({
        "total_tasks": total_tasks,
        "completed": completed,
        "open": open_tasks,
        "assigned": assigned
    })


# Export users as CSV
@app.route('/admin/export/users', methods=['GET'])
@admin_required
def admin_export_users():
    users = User.query.all()
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'Name', 'Email', 'Role', 'Skills', 'Rating'])
    for u in users:
        cw.writerow([u.id, u.name, u.email, u.role, u.skills, u.rating])
    output = si.getvalue()
    return app.response_class(output, mimetype='text/csv')


# Export tasks as CSV
@app.route('/admin/export/tasks', methods=['GET'])
@admin_required
def admin_export_tasks():
    tasks = Task.query.all()
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'Title', 'Category', 'Status', 'Created_By', 'Assigned_To'])
    for t in tasks:
        cw.writerow([t.id, t.title, t.category, t.status, t.created_by, t.assigned_to])
    output = si.getvalue()
    return app.response_class(output, mimetype='text/csv')


# Announcement
@app.route('/admin/announce', methods=['POST'])
@admin_required
def admin_announce():
    data = request.get_json()
    message = data.get('message')
    if not message:
        return jsonify({'error': 'Message required'}), 400
    # For simplicity, just return message; you can extend to email/push notifications
    return jsonify({'announcement': message, 'status': 'sent'})


if __name__ == '__main__':
    app.run(debug=True)
