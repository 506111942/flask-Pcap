import io
import os
import uuid
from datetime import datetime
from functools import wraps

from flask import Flask, abort, flash, jsonify, redirect, render_template, request, send_file, session, url_for
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from sqlalchemy.orm import joinedload

from migrations_util import apply_sqlite_migrations
from analysis import (
    build_attack_stats,
    build_ip_pair_stats,
    build_protocol_stats,
    build_session_hour_distribution,
    build_timeline_stats,
    build_top_ips,
    detect_sensitive_and_attacks,
    extract_sessions,
    parse_packets,
)
from models import AttackInfo, CaptureFile, PacketInfo, SensitiveInfo, SessionInfo, User, db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
MAX_SIZE = 50 * 1024 * 1024
ALLOWED_EXT = {"pcap", "cap"}
# 用户名为 lin（不区分大小写）的账号为超级用户，可管理用户并查看全部分析记录
SUPER_USERNAME = "lin"

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "packets.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = MAX_SIZE
app.config["UPLOAD_FOLDER"] = UPLOAD_DIR
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

os.makedirs(UPLOAD_DIR, exist_ok=True)
db.init_app(app)


def is_super_username(username):
    return (username or "").strip().lower() == SUPER_USERNAME


def sync_superuser_and_capture_owners():
    """仅一个超级用户：用户名为 lin（不区分大小写）中 ID 最小者；历史无归属抓包归到该账号。"""
    users = User.query.all()
    lin_candidates = [u for u in users if is_super_username(u.username)]
    lin_user = min(lin_candidates, key=lambda u: u.id) if lin_candidates else None
    for u in users:
        u.is_superuser = lin_user is not None and u.id == lin_user.id
    if lin_user:
        CaptureFile.query.filter(CaptureFile.user_id.is_(None)).update(
            {CaptureFile.user_id: lin_user.id}, synchronize_session=False
        )
    db.session.commit()


def delete_user_and_captures(user_id):
    """删除用户及其名下抓包文件与解析数据。"""
    caps = CaptureFile.query.filter_by(user_id=user_id).all()
    for cap in caps:
        fid = cap.file_uuid
        PacketInfo.query.filter_by(file_uuid=fid).delete()
        SessionInfo.query.filter_by(file_uuid=fid).delete()
        SensitiveInfo.query.filter_by(file_uuid=fid).delete()
        AttackInfo.query.filter_by(file_uuid=fid).delete()
        path = os.path.join(app.config["UPLOAD_FOLDER"], f"{fid}.pcap")
        if os.path.isfile(path):
            os.remove(path)
        db.session.delete(cap)
    victim = User.query.filter_by(id=user_id).first()
    if victim:
        db.session.delete(victim)
    db.session.commit()


with app.app_context():
    db.create_all()
    apply_sqlite_migrations(db.engine)
    sync_superuser_and_capture_owners()


@app.context_processor
def inject_role():
    return {"is_superuser": bool(session.get("is_superuser"))}


@app.before_request
def refresh_session_superuser_flag():
    uid = session.get("user_id")
    if uid is None:
        return
    if request.endpoint in (None, "static"):
        return
    user = User.query.filter_by(id=uid).first()
    if not user:
        session.clear()
        return
    session["is_superuser"] = bool(user.is_superuser)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapper


def superuser_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        if not session.get("is_superuser"):
            flash("需要超级用户权限", "danger")
            return redirect(url_for("index"))
        return view_func(*args, **kwargs)

    return wrapper


def can_access_capture(capture):
    if session.get("is_superuser"):
        return True
    return capture.user_id == session.get("user_id")


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        confirm_password = request.form.get("confirm_password") or ""

        if not username or not password:
            flash("用户名和密码不能为空", "danger")
            return render_template("register.html")
        if len(password) < 6:
            flash("密码长度不能小于6位", "danger")
            return render_template("register.html")
        if password != confirm_password:
            flash("两次输入的密码不一致", "danger")
            return render_template("register.html")
        if User.query.filter_by(username=username).first():
            flash("用户名已存在，请更换", "danger")
            return render_template("register.html")

        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            is_superuser=False,
        )
        db.session.add(user)
        db.session.commit()
        sync_superuser_and_capture_owners()
        flash("注册成功，请登录", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password_hash, password):
            flash("用户名或密码错误", "danger")
            return render_template("login.html")

        session["user_id"] = user.id
        session["username"] = user.username
        session["is_superuser"] = bool(user.is_superuser)
        return redirect(url_for("index"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    return render_template(
        "index.html",
        nav_active="upload",
        username=session.get("username"),
    )


@app.route("/history")
@login_required
def analysis_history():
    q = CaptureFile.query
    if not session.get("is_superuser"):
        q = q.filter_by(user_id=session["user_id"])
    else:
        q = q.options(joinedload(CaptureFile.owner))
    captures = q.order_by(CaptureFile.created_at.desc()).limit(50).all()
    return render_template(
        "history.html",
        captures=captures,
        nav_active="history",
        username=session.get("username"),
    )


@app.route("/users", methods=["GET", "POST"])
@login_required
@superuser_required
def user_management():
    current_id = session["user_id"]
    if request.method == "POST":
        action = request.form.get("action")
        if action == "delete":
            target_id = request.form.get("user_id", type=int)
            if not target_id or target_id == current_id:
                flash("无法删除当前登录用户或目标无效", "danger")
            else:
                user = User.query.filter_by(id=target_id).first()
                if user:
                    if user.is_superuser:
                        flash("不能删除超级用户账号", "danger")
                    else:
                        delete_user_and_captures(target_id)
                        flash("已删除用户及其分析数据", "success")
                else:
                    flash("用户不存在", "danger")
        return redirect(url_for("user_management"))

    users = User.query.order_by(User.created_at.desc()).all()
    return render_template(
        "users.html",
        users=users,
        nav_active="users",
        username=session.get("username"),
        current_user_id=current_id,
    )


@app.route("/upload", methods=["POST"])
@login_required
def upload():
    if "file" not in request.files:
        return jsonify({"ok": False, "message": "未找到上传文件"}), 400
    f = request.files["file"]
    if not f.filename:
        return jsonify({"ok": False, "message": "文件名为空"}), 400
    if not allowed_file(f.filename):
        return jsonify({"ok": False, "message": "仅支持 pcap/cap"}), 400

    file_uuid = str(uuid.uuid4())
    safe_name = secure_filename(f.filename)
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{file_uuid}.pcap")
    f.save(save_path)

    cap = CaptureFile(file_uuid=file_uuid, filename=safe_name, user_id=session["user_id"])
    db.session.add(cap)
    db.session.commit()

    parse_packets(file_uuid, save_path)
    extract_sessions(file_uuid, save_path)
    detect_sensitive_and_attacks(file_uuid)

    return jsonify({"ok": True, "file_uuid": file_uuid, "redirect": url_for("result", file_uuid=file_uuid)})


@app.route("/result/<file_uuid>")
@login_required
def result(file_uuid):
    capture = CaptureFile.query.filter_by(file_uuid=file_uuid).first_or_404()
    if not can_access_capture(capture):
        abort(404)
    packet_count = PacketInfo.query.filter_by(file_uuid=file_uuid).count()
    session_count = SessionInfo.query.filter_by(file_uuid=file_uuid).count()
    sensitive_count = SensitiveInfo.query.filter_by(file_uuid=file_uuid).count()
    attack_count = AttackInfo.query.filter_by(file_uuid=file_uuid).count()
    recent_packets = PacketInfo.query.filter_by(file_uuid=file_uuid).limit(100).all()
    attacks = (
        AttackInfo.query.filter_by(file_uuid=file_uuid)
        .order_by(AttackInfo.created_at.desc())
        .limit(200)
        .all()
    )
    attack_preview = attacks[:80]
    sensitive_items = (
        SensitiveInfo.query.filter_by(file_uuid=file_uuid).order_by(SensitiveInfo.created_at.desc()).limit(20).all()
    )
    sessions_preview = SessionInfo.query.filter_by(file_uuid=file_uuid).order_by(SessionInfo.id.desc()).limit(40).all()
    return render_template(
        "result.html",
        capture=capture,
        packet_count=packet_count,
        session_count=session_count,
        sensitive_count=sensitive_count,
        attack_count=attack_count,
        recent_packets=recent_packets,
        attacks=attacks,
        attack_preview=attack_preview,
        sensitive_items=sensitive_items,
        sessions_preview=sessions_preview,
        protocol_data=build_protocol_stats(file_uuid),
        timeline_data=build_timeline_stats(file_uuid),
        session_hour_data=build_session_hour_distribution(file_uuid),
        top_ips=build_top_ips(file_uuid),
        ip_pairs=build_ip_pair_stats(file_uuid),
        attack_stats=build_attack_stats(file_uuid),
        username=session.get("username"),
    )


@app.route("/api/stats/<file_uuid>")
@login_required
def stats_api(file_uuid):
    capture = CaptureFile.query.filter_by(file_uuid=file_uuid).first_or_404()
    if not can_access_capture(capture):
        abort(404)
    return jsonify(
        {
            "protocol": build_protocol_stats(file_uuid),
            "timeline": build_timeline_stats(file_uuid),
            "top_ips": build_top_ips(file_uuid),
        }
    )


@app.route("/report/<file_uuid>.pdf")
@login_required
def export_pdf(file_uuid):
    capture = CaptureFile.query.filter_by(file_uuid=file_uuid).first_or_404()
    if not can_access_capture(capture):
        abort(404)
    packet_count = PacketInfo.query.filter_by(file_uuid=file_uuid).count()
    session_count = SessionInfo.query.filter_by(file_uuid=file_uuid).count()
    sensitive_count = SensitiveInfo.query.filter_by(file_uuid=file_uuid).count()
    attack_count = AttackInfo.query.filter_by(file_uuid=file_uuid).count()

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    y = 800
    lines = [
        "Lightweight Packet Analyzer Report",
        f"File UUID: {capture.file_uuid}",
        f"Original Name: {capture.filename}",
        f"Generated Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Packet Count: {packet_count}",
        f"Session Count: {session_count}",
        f"Sensitive Hits: {sensitive_count}",
        f"Attack Alerts: {attack_count}",
    ]
    for line in lines:
        pdf.drawString(72, y, line)
        y -= 26
    pdf.save()
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"report-{file_uuid}.pdf",
    )


if __name__ == "__main__":
    app.run(debug=True)
