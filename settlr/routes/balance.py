from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from models.expense import Expense, ExpenseSplit
from models.user import User

balance_bp = Blueprint("balance", __name__)

@balance_bp.route("/<int:group_id>/balances", methods=["GET"])
@jwt_required()
def get_balances(group_id):
    expenses = Expense.query.filter_by(group_id=group_id).all()
    expense_ids = [e.id for e in expenses]

    net_balance = {}  # user_id -> net amount (positive = owed to them, negative = they owe)

    for expense in expenses:
        splits = ExpenseSplit.query.filter_by(expense_id=expense.id).all()
        for split in splits:
            # Person who paid gets credited
            net_balance[expense.paid_by] = net_balance.get(expense.paid_by, 0) + float(split.amount_owed)
            # Person who owes gets debited
            net_balance[split.user_id] = net_balance.get(split.user_id, 0) - float(split.amount_owed)

    # Remove the payer's own share double-counting when payer == split user
    # (simplify: recalculate cleanly)
    net_balance = {}
    for expense in expenses:
        splits = ExpenseSplit.query.filter_by(expense_id=expense.id).all()
        for split in splits:
            net_balance[split.user_id] = net_balance.get(split.user_id, 0) - float(split.amount_owed)
        net_balance[expense.paid_by] = net_balance.get(expense.paid_by, 0) + float(expense.amount)

    # Build readable result with names
    result = []
    for user_id, balance in net_balance.items():
        user = User.query.get(user_id)
        result.append({
            "user_id": user_id,
            "name": user.name if user else "Unknown",
            "net_balance": round(balance, 2)
        })

    return jsonify(result), 200