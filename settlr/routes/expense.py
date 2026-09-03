from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models.expense import Expense, ExpenseSplit
from models.group import GroupMember

expense_bp = Blueprint("expense", __name__)

@expense_bp.route("/<int:group_id>/expenses", methods=["POST"])
@jwt_required()
def add_expense(group_id):
    paid_by = int(get_jwt_identity())
    data = request.get_json()

    amount = data.get("amount")
    description = data.get("description", "")
    split_type = data.get("split_type", "equal")

    if not amount:
        return jsonify({"error": "Amount is required"}), 400

    # Get all members of this group
    members = GroupMember.query.filter_by(group_id=group_id).all()
    if not members:
        return jsonify({"error": "Group has no members"}), 400

    # Create the expense
    new_expense = Expense(
        group_id=group_id,
        paid_by=paid_by,
        amount=amount,
        description=description,
        split_type=split_type
    )
    db.session.add(new_expense)
    db.session.commit()

    # Equal split logic
    if split_type == "equal":
        share = round(float(amount) / len(members), 2)
        for m in members:
            split = ExpenseSplit(
                expense_id=new_expense.id,
                user_id=m.user_id,
                amount_owed=share
            )
            db.session.add(split)
        db.session.commit()

    return jsonify({
        "message": "Expense added",
        "expense_id": new_expense.id,
        "split_type": split_type
    }), 201


@expense_bp.route("/<int:group_id>/expenses", methods=["GET"])
@jwt_required()
def list_expenses(group_id):
    expenses = Expense.query.filter_by(group_id=group_id).all()
    result = []
    for e in expenses:
        result.append({
            "id": e.id,
            "amount": float(e.amount),
            "description": e.description,
            "paid_by": e.paid_by,
            "split_type": e.split_type
        })
    return jsonify(result), 200