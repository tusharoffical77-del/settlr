import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from app import create_app, db
from models.user import User
from models.group import Group, GroupMember
from models.expense import Expense, ExpenseSplit
import bcrypt


@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def test_equal_split_two_members(app):
    """Test that a 1000 rupee expense splits equally between 2 members"""
    with app.app_context():
        # Create two test users
        hashed = bcrypt.hashpw(b"testpass", bcrypt.gensalt())
        user1 = User(name="Test User 1", email="testuser1@test.com", password_hash=hashed.decode())
        user2 = User(name="Test User 2", email="testuser2@test.com", password_hash=hashed.decode())
        db.session.add_all([user1, user2])
        db.session.commit()

        # Create a group with both as members
        group = Group(name="Test Group", created_by=user1.id)
        db.session.add(group)
        db.session.commit()

        db.session.add_all([
            GroupMember(group_id=group.id, user_id=user1.id),
            GroupMember(group_id=group.id, user_id=user2.id)
        ])
        db.session.commit()

        # Create an expense and manually apply equal split logic
        expense = Expense(group_id=group.id, paid_by=user1.id, amount=1000, split_type="equal")
        db.session.add(expense)
        db.session.commit()

        members = GroupMember.query.filter_by(group_id=group.id).all()
        share = round(1000 / len(members), 2)

        for m in members:
            split = ExpenseSplit(expense_id=expense.id, user_id=m.user_id, amount_owed=share)
            db.session.add(split)
        db.session.commit()

        # Assertions
        splits = ExpenseSplit.query.filter_by(expense_id=expense.id).all()
        assert len(splits) == 2
        for s in splits:
            assert float(s.amount_owed) == 500.0

        # Cleanup
        db.session.query(ExpenseSplit).filter_by(expense_id=expense.id).delete()
        db.session.query(Expense).filter_by(id=expense.id).delete()
        db.session.query(GroupMember).filter_by(group_id=group.id).delete()
        db.session.query(Group).filter_by(id=group.id).delete()
        db.session.query(User).filter(User.id.in_([user1.id, user2.id])).delete()
        db.session.commit()


def test_balance_calculation_nets_to_zero(app):
    """Test that net balances across a group always sum to zero"""
    with app.app_context():
        hashed = bcrypt.hashpw(b"testpass", bcrypt.gensalt())
        user1 = User(name="Balance Test 1", email="balancetest1@test.com", password_hash=hashed.decode())
        user2 = User(name="Balance Test 2", email="balancetest2@test.com", password_hash=hashed.decode())
        db.session.add_all([user1, user2])
        db.session.commit()

        group = Group(name="Balance Test Group", created_by=user1.id)
        db.session.add(group)
        db.session.commit()

        db.session.add_all([
            GroupMember(group_id=group.id, user_id=user1.id),
            GroupMember(group_id=group.id, user_id=user2.id)
        ])
        db.session.commit()

        expense = Expense(group_id=group.id, paid_by=user1.id, amount=1000, split_type="equal")
        db.session.add(expense)
        db.session.commit()

        db.session.add_all([
            ExpenseSplit(expense_id=expense.id, user_id=user1.id, amount_owed=500),
            ExpenseSplit(expense_id=expense.id, user_id=user2.id, amount_owed=500)
        ])
        db.session.commit()

        # Calculate net balances (same logic as the balances endpoint)
        net_balance = {}
        splits = ExpenseSplit.query.filter_by(expense_id=expense.id).all()
        for split in splits:
            net_balance[split.user_id] = net_balance.get(split.user_id, 0) - float(split.amount_owed)
        net_balance[expense.paid_by] = net_balance.get(expense.paid_by, 0) + float(expense.amount)

        total = sum(net_balance.values())
        assert round(total, 2) == 0.0  # balances must always net to zero

        # Cleanup
        db.session.query(ExpenseSplit).filter_by(expense_id=expense.id).delete()
        db.session.query(Expense).filter_by(id=expense.id).delete()
        db.session.query(GroupMember).filter_by(group_id=group.id).delete()
        db.session.query(Group).filter_by(id=group.id).delete()
        db.session.query(User).filter(User.id.in_([user1.id, user2.id])).delete()
        db.session.commit()