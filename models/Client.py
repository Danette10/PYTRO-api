from config.extensions import db


class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(15), unique=True, nullable=False)
    os = db.Column(db.String(50), nullable=True)
    os_version = db.Column(db.String(50), nullable=True)
    hostname = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(10), nullable=False)
    sid = db.Column(db.String(128), nullable=True)
    date_created = db.Column(db.DateTime, default=db.func.now())
    date_updated = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
