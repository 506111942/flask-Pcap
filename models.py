from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_superuser = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class CaptureFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_uuid = db.Column(db.String(64), unique=True, nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    owner = db.relationship("User", backref="captures")


class PacketInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_uuid = db.Column(db.String(64), nullable=False, index=True)
    packet_num = db.Column(db.Integer, nullable=False)
    time = db.Column(db.DateTime, nullable=True)
    src_mac = db.Column(db.String(32), nullable=True)
    dst_mac = db.Column(db.String(32), nullable=True)
    src_ip = db.Column(db.String(64), nullable=True, index=True)
    dst_ip = db.Column(db.String(64), nullable=True, index=True)
    protocol_name = db.Column(db.String(32), nullable=True, index=True)
    length = db.Column(db.Integer, default=0)


class SessionInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_uuid = db.Column(db.String(64), nullable=False, index=True)
    protocol = db.Column(db.String(32), nullable=False, index=True)
    src_ip = db.Column(db.String(64), nullable=True)
    dst_ip = db.Column(db.String(64), nullable=True)
    src_port = db.Column(db.Integer, nullable=True)
    dst_port = db.Column(db.Integer, nullable=True)
    content = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class SensitiveInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_uuid = db.Column(db.String(64), nullable=False, index=True)
    session_id = db.Column(db.Integer, nullable=False, index=True)
    info_type = db.Column(db.String(32), nullable=False)
    info_value = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class AttackInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_uuid = db.Column(db.String(64), nullable=False, index=True)
    suspicious_address = db.Column(db.String(64), nullable=True, index=True)
    attack_type = db.Column(db.String(64), nullable=False)
    attack_content = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
