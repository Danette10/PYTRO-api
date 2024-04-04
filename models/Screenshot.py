from datetime import datetime

from config.extensions import db


class Screenshot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    file_path = db.Column(db.String(256), unique=True, nullable=False)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.now)
    date_updated = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    client = db.relationship('Client', backref=db.backref('screenshots', lazy=True))

    def __repr__(self):
        return f'<Screenshot {self.file_path}>'
