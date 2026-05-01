# 果感知·智选助手

> 农业机器人传感器实时选型与验证引擎

## 项目简介

果感知·智选助手是一个帮助农业机器人初创团队和实验室用户快速完成传感器选型的Web应用。用户只需用自然语言描述需求（如"草莓采摘机器人需要判断成熟度的视觉+触觉传感器"），系统即可智能推荐合适的传感器组合方案。

## 功能特点

- **智能推荐**: 基于关键词匹配，快速推荐传感器组合方案
- **方案详情**: 包含传感器型号、关键指标、价格区间、供应商联系方式
- **选型解析**: 详细说明推荐理由和对标分析
- **测试建议**: 提供测试验证项、参考标准和测试设备建议
- **采购指导**: 典型客户案例、样片申请渠道
- **数据概览**: 内置10+传感器型号、5+应用场景

## 技术栈

- **前端**: HTML + Vue 3 (CDN)
- **后端**: Python Flask
- **数据**: JSON 文件存储
- **部署**: 本地运行 / PythonAnywhere / Render

## 快速开始

### 前置要求

- Python 3.8+

### 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 启动服务

#### 方式一：Windows 双击运行

```bash
双击运行 run.bat
```

#### 方式二：命令行启动

```bash
# 启动后端服务
cd backend
python app.py
```

### 访问应用

1. 打开浏览器访问 `frontend/index.html`
2. 或直接在浏览器输入后端地址测试API：`http://localhost:5000/api/sensors`

## 使用示例

在搜索框中输入以下需求：

- "草莓采摘机器人需要判断果实成熟度"
- "番茄采摘机器人目标识别和避障"
- "无人机农田巡检病虫害检测"
- "果园自主导航SLAM"

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/recommend` | POST | 智能推荐传感器方案 |
| `/api/sensors` | GET | 获取所有传感器列表 |
| `/api/scenarios` | GET | 获取所有场景方案 |
| `/api/search` | GET | 搜索传感器 |
| `/api/realtime` | POST | 实时检索（预留） |

## 项目结构

```
果感知·智选助手/
├── backend/
│   ├── app.py              # Flask 后端服务
│   ├── data/
│   │   ├── sensors.json    # 传感器数据
│   │   └── scenarios.json  # 场景方案数据
│   └── requirements.txt    # Python 依赖
├── frontend/
│   └── index.html          # 前端页面
├── README.md               # 说明文档
└── run.bat                 # Windows 启动脚本
```

## 扩展说明

### 添加新传感器

编辑 `backend/data/sensors.json`，按照现有格式添加传感器数据：

```json
{
  "id": 11,
  "model": "新型号传感器",
  "type": "传感器类型",
  "vendor": "供应商",
  "level": "工业级",
  "specs": {"关键指标": "值"},
  "price": "价格区间",
  "url": "官网链接",
  "contact": "联系方式"
}
```

### 添加新场景方案

编辑 `backend/data/scenarios.json`，添加新的应用场景：

```json
{
  "id": 6,
  "name": "方案名称",
  "tags": ["标签1", "标签2"],
  "sensor_ids": [1, 2],
  "description": "方案描述",
  "rationale": "选型理由",
  "test_suggestion": {
    "items": ["测试项1", "测试项2"],
    "standard": "参考标准",
    "equipment": ["设备1", "设备2"]
  },
  "vendor_contact": "联系方式",
  "case": {"name": "客户案例", "amount": "金额", "year": 2026}
}
```

### 启用实时检索功能

当前版本预留了实时检索接口。如需启用，需要：

1. 申请必应搜索 API 密钥
2. 申请 OpenAI API 密钥（或使用国产LLM）
3. 在 `backend/app.py` 中实现实时检索逻辑

## 版本信息

- **版本**: 1.0
- **发布日期**: 2026-03-21
- **状态**: 演示版

## 许可证

MIT License

## 联系方式

如有问题，请联系：info@guoganzhi.com
