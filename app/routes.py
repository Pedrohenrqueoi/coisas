# -*- coding: utf-8 -*-
"""
Main HTML Routes (Frontend)
"""
from flask import Blueprint, render_template, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Landing page"""
    return render_template('index.html')


@main_bp.route('/dashboard')
@jwt_required(optional=True)
def dashboard():
    """User dashboard (requires auth)"""
    return render_template('index.html')


@main_bp.route('/pricing')
def pricing():
    """Pricing page"""
    from flask import current_app
    return jsonify({
        "plans": current_app.config['PLANS']
    })


@main_bp.route('/docs')
def docs():
    """API documentation"""
    return render_template('docs.html')

@main_bp.route('/login')
def login():
    return render_template('login.html')