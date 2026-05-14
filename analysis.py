import os
import re
from collections import Counter, defaultdict
from datetime import datetime

from scapy.all import IP, TCP, UDP, Ether, Raw, rdpcap

from models import AttackInfo, PacketInfo, SensitiveInfo, SessionInfo, db

MAX_PACKETS = 30000


def detect_protocol(packet):
    if packet.haslayer(TCP):
        sport = int(packet[TCP].sport)
        dport = int(packet[TCP].dport)
        ports = {sport, dport}
        if 80 in ports or 8080 in ports:
            return "HTTP"
        if 443 in ports:
            return "HTTPS"
        if 21 in ports:
            return "FTP"
        if 23 in ports:
            return "TELNET"
        return "TCP"
    if packet.haslayer(UDP):
        return "UDP"
    if packet.haslayer(IP):
        return "IP"
    if packet.haslayer(Ether):
        return "ETH"
    return "OTHER"


def parse_packets(file_uuid, file_path):
    packets = rdpcap(file_path, count=MAX_PACKETS)
    saved_count = 0
    for idx, packet in enumerate(packets, start=1):
        row = PacketInfo(
            file_uuid=file_uuid,
            packet_num=idx,
            time=datetime.fromtimestamp(float(packet.time)) if hasattr(packet, "time") else None,
            src_mac=packet[Ether].src if packet.haslayer(Ether) else None,
            dst_mac=packet[Ether].dst if packet.haslayer(Ether) else None,
            src_ip=packet[IP].src if packet.haslayer(IP) else None,
            dst_ip=packet[IP].dst if packet.haslayer(IP) else None,
            protocol_name=detect_protocol(packet),
            length=len(packet),
        )
        db.session.add(row)
        saved_count += 1
    db.session.commit()
    return saved_count


def extract_sessions(file_uuid, file_path):
    packets = rdpcap(file_path, count=MAX_PACKETS)
    grouped = defaultdict(list)
    for packet in packets:
        if not (packet.haslayer(IP) and packet.haslayer(TCP)):
            continue
        key = (
            packet[IP].src,
            packet[TCP].sport,
            packet[IP].dst,
            packet[TCP].dport,
        )
        payload = ""
        if packet.haslayer(Raw):
            payload = packet[Raw].load[:2000].decode("utf-8", errors="ignore")
        grouped[key].append(payload)

    count = 0
    for (src_ip, sport, dst_ip, dport), payloads in grouped.items():
        content = "\n".join([x for x in payloads if x]).strip()
        if not content:
            continue
        proto = "HTTP" if int(sport) in (80, 8080) or int(dport) in (80, 8080) else "TCP"
        row = SessionInfo(
            file_uuid=file_uuid,
            protocol=proto,
            src_ip=src_ip,
            dst_ip=dst_ip,
            src_port=int(sport),
            dst_port=int(dport),
            content=content[:10000],
        )
        db.session.add(row)
        count += 1
    db.session.commit()
    return count


def detect_sensitive_and_attacks(file_uuid):
    sessions = SessionInfo.query.filter_by(file_uuid=file_uuid).all()
    phone_pattern = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")
    email_pattern = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
    id_pattern = re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)")

    sql_injection_pattern = re.compile(
        r"(union\s+select|or\s+1=1|drop\s+table|xp_cmdshell|information_schema)",
        re.IGNORECASE,
    )
    directory_traversal_pattern = re.compile(r"(\.\./|\.\.\\|/etc/passwd|/windows/system32)", re.IGNORECASE)
    weak_password_pattern = re.compile(r"(password|passwd|pwd)\s*=\s*['\"]?[A-Za-z0-9@#$%^&*]{1,8}", re.IGNORECASE)

    sensitive_count = 0
    attack_count = 0

    for session in sessions:
        content = session.content or ""
        for v in phone_pattern.findall(content):
            db.session.add(SensitiveInfo(file_uuid=file_uuid, session_id=session.id, info_type="phone", info_value=v))
            sensitive_count += 1
        for v in email_pattern.findall(content):
            db.session.add(SensitiveInfo(file_uuid=file_uuid, session_id=session.id, info_type="email", info_value=v))
            sensitive_count += 1
        for v in id_pattern.findall(content):
            db.session.add(SensitiveInfo(file_uuid=file_uuid, session_id=session.id, info_type="id_card", info_value=v))
            sensitive_count += 1

        attack_types = []
        if sql_injection_pattern.search(content):
            attack_types.append("SQL Injection")
        if directory_traversal_pattern.search(content):
            attack_types.append("Directory Traversal")
        if weak_password_pattern.search(content):
            attack_types.append("Weak Credential Exposure")

        for item in attack_types:
            db.session.add(
                AttackInfo(
                    file_uuid=file_uuid,
                    suspicious_address=session.src_ip,
                    attack_type=item,
                    attack_content=content[:500],
                )
            )
            attack_count += 1

    db.session.commit()
    return {"sensitive_count": sensitive_count, "attack_count": attack_count}


def build_protocol_stats(file_uuid):
    rows = PacketInfo.query.filter_by(file_uuid=file_uuid).all()
    counter = Counter([r.protocol_name or "OTHER" for r in rows])
    return [{"name": k, "value": v} for k, v in counter.items()]


def build_timeline_stats(file_uuid):
    rows = PacketInfo.query.filter_by(file_uuid=file_uuid).all()
    buckets = defaultdict(int)
    for row in rows:
        if row.time:
            t = row.time.replace(microsecond=0).isoformat(sep=" ")
            buckets[t] += 1
    keys = sorted(buckets.keys())
    return {"labels": keys, "values": [buckets[k] for k in keys]}


def build_top_ips(file_uuid, topn=10):
    rows = PacketInfo.query.filter_by(file_uuid=file_uuid).all()
    counter = Counter()
    for r in rows:
        if r.src_ip:
            counter[r.src_ip] += 1
        if r.dst_ip:
            counter[r.dst_ip] += 1
    total_mentions = sum(counter.values()) or 1
    return [
        {"ip": ip, "count": count, "ratio": round(100 * count / total_mentions, 2)}
        for ip, count in counter.most_common(topn)
    ]


def build_ip_pair_stats(file_uuid, topn=25):
    rows = PacketInfo.query.filter_by(file_uuid=file_uuid).all()
    pair_counter = Counter()
    for r in rows:
        if r.src_ip and r.dst_ip:
            pair_counter[(r.src_ip, r.dst_ip)] += 1
    total = sum(pair_counter.values()) or 1
    return [
        {"src_ip": s, "dst_ip": d, "count": c, "ratio": round(100 * c / total, 2)}
        for (s, d), c in pair_counter.most_common(topn)
    ]


def build_session_hour_distribution(file_uuid):
    rows = PacketInfo.query.filter_by(file_uuid=file_uuid).all()
    buckets = defaultdict(int)
    for r in rows:
        if r.time is not None:
            buckets[r.time.hour] += 1
    labels = [f"{h:02d}:00" for h in range(24)]
    values = [buckets[h] for h in range(24)]
    return {"labels": labels, "values": values}


def build_attack_stats(file_uuid):
    attacks = AttackInfo.query.filter_by(file_uuid=file_uuid).all()
    type_counter = Counter(a.attack_type for a in attacks)
    risk_map = {
        "SQL Injection": "高",
        "Directory Traversal": "高",
        "Weak Credential Exposure": "中",
    }
    risk_counter = Counter(risk_map.get(a.attack_type, "低") for a in attacks)
    return {
        "by_type": [{"name": k, "value": v} for k, v in type_counter.items()],
        "by_risk": [{"name": k, "value": v} for k, v in risk_counter.items()],
    }

