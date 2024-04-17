from datetime import datetime

from config.extensions import db
from enum import Enum


class CommandType(Enum):
    SCREENSHOT = "screenshot"
    MICROPHONE = "microphone"


class Command(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Enum(CommandType), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    file_path = db.Column(db.String(256), unique=True, nullable=False)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.now)
    date_updated = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    client = db.relationship('Client', backref=db.backref('commands', lazy=True))

    def __repr__(self):
        return f'<Command {self.type}>'
