from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models.group import Group, GroupMember
from models.user import User

group_bp = Blueprint("group", __name__)

@group_bp.route("", methods=["POST"])
@jwt_required()
def create_group():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    name = data.get("name")

    if not name:
        return jsonify({"error": "Group name is required"}), 400

    new_group = Group(name=name, created_by=user_id)
    db.session.add(new_group)
    db.session.commit()

    # Automatically add the creator as a member
    member = GroupMember(group_id=new_group.id, user_id=user_id)
    db.session.add(member)
    db.session.commit()

    return jsonify({"message": "Group created", "group_id": new_group.id}), 201


@group_bp.route("", methods=["GET"])
@jwt_required()
def list_groups():
    user_id = int(get_jwt_identity())

    memberships = GroupMember.query.filter_by(user_id=user_id).all()
    group_ids = [m.group_id for m in memberships]
    groups = Group.query.filter(Group.id.in_(group_ids)).all()

    result = [{"id": g.id, "name": g.name, "created_by": g.created_by} for g in groups]
    return jsonify(result), 200


@group_bp.route("/<int:group_id>/members", methods=["POST"])
@jwt_required()
def add_member(group_id):
    data = request.get_json()
    email = data.get("email")

    group = Group.query.get(group_id)
    if not group:
        return jsonify({"error": "Group not found"}), 404

    user_to_add = User.query.filter_by(email=email).first()
    if not user_to_add:
        return jsonify({"error": "No user found with that email"}), 404

    existing = GroupMember.query.filter_by(group_id=group_id, user_id=user_to_add.id).first()
    if existing:
        return jsonify({"error": "User is already a member of this group"}), 409

    new_member = GroupMember(group_id=group_id, user_id=user_to_add.id)
    db.session.add(new_member)
    db.session.commit()

    return jsonify({"message": f"{user_to_add.name} added to group"}), 201


@group_bp.route("/<int:group_id>/members", methods=["GET"])
@jwt_required()
def list_members(group_id):
    members = GroupMember.query.filter_by(group_id=group_id).all()
    user_ids = [m.user_id for m in members]
    users = User.query.filter(User.id.in_(user_ids)).all()

    result = [{"id": u.id, "name": u.name, "email": u.email} for u in users]
    return jsonify(result), 200