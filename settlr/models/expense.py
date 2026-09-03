from app import db

class Expense(db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"))
    paid_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.String(255))
    split_type = db.Column(db.Enum("equal", "percentage", "exact"), default="equal")
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.now())

class ExpenseSplit(db.Model):
    __tablename__ = "expense_splits"

    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey("expenses.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    amount_owed = db.Column(db.Numeric(10, 2))