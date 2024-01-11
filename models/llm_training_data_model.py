# This is the LLM data Model class
# The data model is used to store the data from the JSONL file
# Sample Structure is {"messages": [{"role": "user", "content": "I suddenly need the funds I used to pay for my loan. Can I still cancel the loan payment I made through the Pay Button?"}, {"role": "assistant", "content": "<p>Hi there, luv! As soon as your loan payment has been authenticated, its sole purpose is to be posted and applied to your loan on your chosen installment date.</p>\n<p>Think of it as one less worry for you, since it will be automatically applied to your loan without you needing to access your Tonik Account anymore. The reserved payment will also earn 1% interest, which will be credited to your Tonik Account every end of each month.Super thanks for understanding, luv! XOXO</p>"}]}
# where the table messages has the columns id, user, assistant. The user row has the question and the assistant row has the answer
# The id is the primary key

# llm_training_data_model.py

from db_init import db


class LLMDataModel(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Text)
    assistant = db.Column(db.Text)

    def __repr__(self):
        return f'<LLMDataModel {self.id}>'
