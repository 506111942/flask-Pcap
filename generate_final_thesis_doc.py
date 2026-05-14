from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt


TITLE = "基于Pcap的网络流量分析平台的设计与实现"
OUT_MAIN = r"F:\work\cursor\基于Pcap的网络流量分析平台的设计与实现-论文初稿.docx"
OUT_FINAL = r"F:\work\cursor\thesis_final.docx"


def add_heading(doc, text, level=1):
    h = doc.add_heading(text, level=level)
    h.runs[0].font.name = "宋体"
    h.runs[0].font.size = Pt(14 if level == 1 else 12)
    return h


def add_para(doc, text, first_indent=True):
    p = doc.add_paragraph(text)
    pf = p.paragraph_format
    pf.line_spacing = 1.5
    if first_indent:
        pf.first_line_indent = Pt(24)
    for run in p.runs:
        run.font.name = "宋体"
        run.font.size = Pt(12)
    return p


def add_cover(doc):
    p = doc.add_paragraph("本科毕业设计（论文）")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.runs[0].font.name = "宋体"
    p.runs[0].font.size = Pt(20)

    p = doc.add_paragraph("")
    p = doc.add_paragraph(TITLE)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.runs[0].font.name = "黑体"
    p.runs[0].font.size = Pt(22)

    doc.add_paragraph("")
    doc.add_paragraph("")
    add_para(doc, "学院：________________________", first_indent=False)
    add_para(doc, "专业：________________________", first_indent=False)
    add_para(doc, "学生姓名：____________________", first_indent=False)
    add_para(doc, "学号：________________________", first_indent=False)
    add_para(doc, "指导教师：____________________", first_indent=False)
    add_para(doc, "完成日期：2026年____月____日", first_indent=False)
    doc.add_page_break()


def add_abstract(doc):
    add_heading(doc, "摘要", level=1)
    add_para(
        doc,
        "随着互联网应用规模持续增长，网络安全事件和数据泄露风险不断增加，网络流量分析已成为运维与安全检测中的关键技术手段。"
        "传统抓包分析工具虽然功能强大，但在教学场景和中小型项目中存在学习成本高、部署复杂、可视化流程不统一等问题。"
        "为解决上述问题，本文设计并实现了一套基于Pcap文件的网络流量分析平台。系统以后端Flask框架为核心，结合Scapy完成离线流量解析，"
        "使用SQLite进行数据持久化，前端采用Bootstrap与ECharts实现交互式可视化展示。平台实现了数据包上传、基础字段解析、协议分布统计、"
        "时间序列分析、Top IP分析、TCP会话提取、敏感信息识别、攻击行为检测及PDF报告导出等功能，形成了“上传—解析—存储—分析—展示—导出”的完整闭环。"
        "测试结果表明，该平台能够稳定完成中小规模Pcap文件分析任务，对SQL注入、目录遍历、弱口令暴露等典型风险行为具有有效识别能力。"
        "本文研究成果可为网络安全课程实验、毕业设计实践及轻量级运维分析场景提供参考。"
    )
    add_para(doc, "关键词：Pcap；网络流量分析；Flask；Scapy；可视化；安全检测", first_indent=False)

    add_heading(doc, "Abstract", level=1)
    add_para(
        doc,
        "With the rapid growth of Internet services, network threats and data leakage risks are becoming increasingly serious. "
        "Traffic analysis has become a key capability in security operations. Although traditional packet tools are powerful, "
        "they are often difficult for beginners and costly to maintain in lightweight scenarios. This thesis designs and implements "
        "a Pcap-based network traffic analysis platform. The system uses Flask as backend framework, Scapy for offline packet parsing, "
        "SQLite for persistence, and Bootstrap with ECharts for visualization. It supports file upload, packet parsing, protocol statistics, "
        "timeline analysis, Top IP ranking, session extraction, sensitive information detection, attack behavior detection, and PDF report export. "
        "An end-to-end workflow from upload to report generation is established. Experimental results show that the platform can stably process "
        "small and medium Pcap files and detect suspicious behaviors such as SQL injection, directory traversal, and weak credential exposure."
    )
    add_para(doc, "Key Words: Pcap, Network Traffic Analysis, Flask, Scapy, Visualization, Security Detection", first_indent=False)
    doc.add_page_break()


def add_toc_placeholder(doc):
    add_heading(doc, "目录", level=1)
    add_para(doc, "（提示：在Word中右键目录区域，选择“更新域”，即可生成自动目录）", first_indent=False)
    add_para(doc, "第1章 绪论", first_indent=False)
    add_para(doc, "第2章 关键技术与理论基础", first_indent=False)
    add_para(doc, "第3章 系统需求分析", first_indent=False)
    add_para(doc, "第4章 系统总体设计", first_indent=False)
    add_para(doc, "第5章 系统详细实现", first_indent=False)
    add_para(doc, "第6章 系统测试与结果分析", first_indent=False)
    add_para(doc, "第7章 总结与展望", first_indent=False)
    add_para(doc, "参考文献", first_indent=False)
    add_para(doc, "致谢", first_indent=False)
    doc.add_page_break()


def add_body(doc):
    add_heading(doc, "第1章 绪论", level=1)
    add_heading(doc, "1.1 研究背景与意义", level=2)
    add_para(doc, "网络通信已深度融入政务、教育、金融、医疗等领域，网络空间威胁持续上升。对于运维人员和安全分析人员而言，快速定位异常流量、还原攻击路径和识别敏感数据外泄具有重要价值。Pcap文件能够完整记录网络通信过程，是网络分析和安全取证的重要数据来源。")
    add_para(doc, "在实际教学和工程实践中，传统流量分析工具虽然功能完备，但普遍存在操作门槛高、结果分散、报告输出流程不一致等问题。面向本科毕业设计，构建一套可部署、可展示、可扩展的轻量级平台，有助于将理论知识转化为可运行系统。")

    add_heading(doc, "1.2 国内外研究现状", level=2)
    add_para(doc, "国外在流量分析工具与检测体系方面发展较早，形成了Wireshark、Snort、Suricata等成熟生态，覆盖协议解析、规则检测和日志关联等能力。国内研究则更强调场景化应用和系统集成，逐步从单点检测向可视化协同分析演进。")
    add_para(doc, "现有研究总体呈现“能力强但复杂度高”的特点。对于教学实践和中小型项目，仍需要更轻量、低成本且可视化友好的技术方案。")

    add_heading(doc, "1.3 研究内容与目标", level=2)
    add_para(doc, "本文目标是实现一个面向Pcap离线文件的网络流量分析平台，重点完成数据解析、行为统计、风险识别和结果展示四类能力，形成端到端可运行系统。")
    add_para(doc, "具体研究内容包括：系统需求分析与架构设计；核心功能模块开发；测试样本构建与效果评估；总结系统优劣并提出扩展方向。")

    add_heading(doc, "1.4 论文结构", level=2)
    add_para(doc, "全文共七章，依次介绍关键技术、需求分析、系统设计、系统实现、测试分析和结论展望。")

    add_heading(doc, "第2章 关键技术与理论基础", level=1)
    add_heading(doc, "2.1 Pcap文件与协议分析基础", level=2)
    add_para(doc, "Pcap（Packet Capture）是一种通用抓包文件格式，记录网络数据包的时间戳与原始二进制内容。通过分层解析可提取链路层、网络层、传输层以及部分应用层字段，为流量统计与安全检测提供基础数据。")
    add_heading(doc, "2.2 Flask Web开发框架", level=2)
    add_para(doc, "Flask具有轻量、灵活、扩展性强等特点，适合快速构建Web应用。本文利用Flask实现文件上传接口、分析结果页面和报告导出接口。")
    add_heading(doc, "2.3 Scapy离线流量解析", level=2)
    add_para(doc, "Scapy提供强大的数据包读取和解析能力。系统使用rdpcap读取离线文件，通过协议层判断提取IP地址、端口、协议类型、负载内容等信息。")
    add_heading(doc, "2.4 SQLite与ORM持久化", level=2)
    add_para(doc, "SQLite作为嵌入式数据库可显著降低部署成本，配合Flask-SQLAlchemy实现模型化数据管理，提升代码可维护性。")
    add_heading(doc, "2.5 前端可视化技术", level=2)
    add_para(doc, "Bootstrap用于页面布局与样式统一，ECharts用于图表展示。通过协议分布饼图和时序折线图，提升分析结果可解释性。")

    add_heading(doc, "第3章 系统需求分析", level=1)
    add_heading(doc, "3.1 功能需求分析", level=2)
    add_para(doc, "系统需支持：pcap/cap文件上传、数据包解析、协议统计、时间序列展示、Top IP统计、会话提取、敏感信息识别、攻击行为检测、报告导出。")
    add_heading(doc, "3.2 非功能需求分析", level=2)
    add_para(doc, "系统需满足易用性、可靠性、性能、扩展性和安全性等要求。对50MB以内样本文件应能在可接受时间内完成分析。")

    add_heading(doc, "第4章 系统总体设计", level=1)
    add_heading(doc, "4.1 架构设计", level=2)
    add_para(doc, "平台采用B/S架构，包含表示层、业务逻辑层和数据访问层。用户通过浏览器发起上传请求，服务端完成解析与检测后返回可视化结果。")
    add_heading(doc, "4.2 功能模块设计", level=2)
    add_para(doc, "系统划分为文件上传模块、流量解析模块、统计分析模块、会话提取模块、安全检测模块、可视化模块和报告导出模块。各模块通过file_uuid串联，形成完整分析链路。")
    add_heading(doc, "4.3 数据库设计", level=2)
    add_para(doc, "数据库设计包含CaptureFile、PacketInfo、SessionInfo、SensitiveInfo、AttackInfo五张核心表，分别用于记录文件元信息、包明细、会话内容、敏感信息和攻击告警。")

    add_heading(doc, "第5章 系统详细实现", level=1)
    add_heading(doc, "5.1 开发环境", level=2)
    add_para(doc, "系统在Windows 10环境开发，Python 3.10运行，采用Flask、Scapy、Flask-SQLAlchemy、ReportLab等依赖。")
    add_heading(doc, "5.2 文件上传与任务触发实现", level=2)
    add_para(doc, "上传接口对文件类型和大小进行校验，生成唯一file_uuid并持久化文件信息。随后自动触发解析、会话提取与安全检测流程。")
    add_heading(doc, "5.3 数据包解析与协议识别实现", level=2)
    add_para(doc, "解析模块遍历数据包提取时间、MAC、IP、长度等字段；结合端口启发式对HTTP、HTTPS、FTP、TELNET等协议进行识别并入库。")
    add_heading(doc, "5.4 会话提取与内容聚合实现", level=2)
    add_para(doc, "以源IP、源端口、目的IP、目的端口为索引聚合TCP会话，提取Raw负载并进行截断保存，为后续风险识别提供文本语料。")
    add_heading(doc, "5.5 敏感信息识别与攻击检测实现", level=2)
    add_para(doc, "系统基于正则规则识别手机号、邮箱、身份证号等敏感信息；同时对SQL注入、目录遍历、弱口令暴露特征进行检测，命中后记录告警。")
    add_heading(doc, "5.6 可视化展示与报告导出实现", level=2)
    add_para(doc, "结果页展示统计卡片、协议分布、时序图、Top IP、告警列表和敏感信息列表。导出模块将关键指标写入PDF，实现分析结果归档。")

    add_heading(doc, "第6章 系统测试与结果分析", level=1)
    add_heading(doc, "6.1 测试环境与测试方法", level=2)
    add_para(doc, "测试环境为Windows 10、Python 3.10。测试方法包括功能测试、异常测试、样本验证测试。")
    add_heading(doc, "6.2 功能测试结果", level=2)
    add_para(doc, "测试结果表明，系统上传、解析、统计、展示与导出功能均可稳定运行，页面响应正常，核心流程闭环完整。")
    add_heading(doc, "6.3 安全检测结果分析", level=2)
    add_para(doc, "在构造样本中，系统可识别UNION SELECT等SQL注入特征、../目录遍历特征及弱口令参数暴露，且可在页面中展示告警来源与摘要。")
    add_heading(doc, "6.4 性能与不足分析", level=2)
    add_para(doc, "当前系统针对中小规模离线文件分析表现良好，但对超大文件的处理效率仍有提升空间。后续可引入异步任务队列、分片解析和缓存机制。")

    add_heading(doc, "第7章 总结与展望", level=1)
    add_heading(doc, "7.1 全文总结", level=2)
    add_para(doc, "本文完成了基于Pcap的网络流量分析平台设计与实现，构建了完整的离线分析流程，并实现了多项可视化与安全检测能力。系统具备较好的实用性与可扩展性，满足本科毕业设计目标。")
    add_heading(doc, "7.2 后续展望", level=2)
    add_para(doc, "后续可从实时抓包、协议深度解析、IP地理可视化、规则引擎配置、用户权限审计、机器学习异常检测等方向持续完善。")

    add_heading(doc, "参考文献", level=1)
    add_para(doc, "[1] Combs G. Wireshark User’s Guide.", first_indent=False)
    add_para(doc, "[2] Biondi P. Scapy Documentation.", first_indent=False)
    add_para(doc, "[3] Grinberg M. Flask Web Development.", first_indent=False)
    add_para(doc, "[4] Stallings W. Data and Computer Communications.", first_indent=False)
    add_para(doc, "[5] 李某某, 王某某. 网络流量分析技术研究综述[J]. 计算机工程与应用, 2022.", first_indent=False)
    add_para(doc, "[6] 张某某. 网络安全态势感知关键技术研究[D]. 某高校, 2023.", first_indent=False)

    add_heading(doc, "致谢", level=1)
    add_para(doc, "在本论文完成过程中，感谢指导教师在选题、系统设计与论文写作方面给予的悉心指导；感谢同学和朋友在测试与修改阶段提供的帮助。通过本次毕业设计，我进一步提升了工程实现能力与问题分析能力。")


def build_document():
    doc = Document()
    normal = doc.styles["Normal"]
    normal.font.name = "宋体"
    normal.font.size = Pt(12)

    add_cover(doc)
    add_abstract(doc)
    add_toc_placeholder(doc)
    add_body(doc)

    doc.save(OUT_MAIN)
    doc.save(OUT_FINAL)
    print(OUT_MAIN)
    print(OUT_FINAL)


if __name__ == "__main__":
    build_document()
