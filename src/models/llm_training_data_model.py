# This is the LLM data Model class
# The data model is used to store the data from the JSONL file
# Sample Structure of the JSONL file is below
# # {"messages": [{"role": "user", "content": "I suddenly need the funds I used to pay for my loan.
# # Can I still cancel the loan payment I made through the Pay Button?"},
# where the table messages has the columns id, question, answer.
# The question colum has the user content and the answer column has assistant content.
# The id is the primary key

# llm_training_data_model.py

from ..data_tools.db_init import db


class LLMDataModel(db.Model):
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text)
    answer = db.Column(db.Text)
    dataset_type = db.Column(db.String(50), default="chat")
    payload = db.Column(db.Text)
    validation_errors = db.Column(db.Text)
    validation_warnings = db.Column(db.Text)

    def __repr__(self):
        return f"<LLMDataModel {self.id}>"

    def to_dict(self):
        return {
            'id': self.id,
            'question': self.question,
            'answer': self.answer,
            'dataset_type': self.dataset_type,
            'validation_errors': self.validation_errors,
            'validation_warnings': self.validation_warnings,
        }
