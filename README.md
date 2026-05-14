# 基于Pcap的网络流量分析平台的设计与实现

一个可直接运行的毕业设计项目实现，技术栈为 Flask + Scapy + SQLite + Bootstrap + ECharts。

## 已实现功能

- pcap/cap 文件上传（限制 50MB）
- 数据包解析与基础字段入库（时间、IP、协议、长度）
- 协议分布统计与时间序列流量图
- TCP 会话提取（含 payload 拼接）
- 敏感信息识别（手机号/邮箱/身份证号）
- 攻击行为检测（SQL 注入/目录遍历/弱口令暴露）
- Top IP 统计
- 分析结果页面展示
- PDF 报告导出

## 快速启动

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

打开浏览器访问：`http://127.0.0.1:5000`

## 项目结构

- `app.py`：Flask 路由、上传流程、结果页、报告导出
- `analysis.py`：pcap 解析、会话提取、统计分析、告警检测
- `models.py`：SQLAlchemy 数据模型
- `templates/index.html`：上传入口
- `templates/result.html`：分析可视化结果页

## 说明

- 当前实现优先保证“可运行 + 可演示 + 对应论文功能点”。
- 可按论文后续版本继续扩展：IP 地理位置地图、更多协议重组、文件重建下载、权限管理等。
