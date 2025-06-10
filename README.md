# JPSQL
sql注数据天上来

# 小日子SQL注入扫描工具

一个用于自动化发现和扫描日本网站SQL注入漏洞的工具集。

## 功能特点

- 多渠道目标收集（Google、FOFA）
- 自动参数提取和分析
- 基于SQLMap API的自动化扫描
- 异步并发处理提高效率
- 完善的日志和通知系统
- 模块化设计，易于扩展

## 目录结构

```
.
├── config.py                 # 配置文件
├── main.py                   # 主程序
├── collectors/               # 收集器模块
│   ├── __init__.py
│   ├── google_collector.py   # Google搜索收集器
│   ├── fofa_collector.py     # FOFA搜索收集器
│   └── param_extractor.py    # 参数提取器
├── scanners/                 # 扫描器模块
│   ├── __init__.py
│   └── sqlmap_scanner.py     # SQLMap扫描器
├── utils/                    # 工具模块
│   ├── __init__.py
│   ├── logger.py             # 日志工具
│   ├── http_client.py        # HTTP客户端
│   ├── url_tools.py          # URL处理工具
│   ├── file_utils.py         # 文件操作工具
│   ├── sqlmap_client.py      # SQLMap API客户端
│   └── notifier.py           # 通知工具
└── output/                   # 输出目录
    ├── logs/                 # 日志文件
    ├── google_urls.txt       # Google收集的URL
    ├── fofa_urls.txt         # FOFA收集的URL
    └── extracted_urls.txt    # 提取的参数URL
```

## 环境要求

- Python 3.7+
- SQLMap API服务
- 相关API密钥（Google、FOFA）

## 安装

1. 克隆仓库：

```bash
git clone https://github.com/yourusername/jpsql.git
cd jpsql
```

2. 安装依赖：

```bash
pip install -r requirements.txt
```

3. 创建 `.env` 文件，设置API密钥：

```
GOOGLE_API=your_google_api_key
SEARCH_ENGINE_ID=your_search_engine_id
FOFA_EMAIL=your_fofa_email
FOFA_KEY=your_fofa_key
EMAIL_USER=your_email
EMAIL_PASS=your_email_password
EMAIL_TO=recipient_email
```

## 使用方法

### 运行完整工作流

```bash
python main.py workflow
```

### 仅收集目标

```bash
# 使用Google收集
python main.py collect google

# 使用FOFA收集
python main.py collect fofa

# 提取参数
python main.py collect extract -i input_file.txt -o output_file.txt
```

### 仅扫描目标

```bash
# 同步扫描
python main.py scan -i targets.txt

# 异步扫描
python main.py scan -i targets.txt -a -w 10
```

### 命令行参数

- `-sg`, `--skip-google`: 跳过Google收集
- `-sf`, `--skip-fofa`: 跳过FOFA收集
- `-se`, `--skip-extract`: 跳过参数提取
- `-ss`, `--skip-scan`: 跳过SQLMap扫描
- `-a`, `--async-mode`: 使用异步模式
- `-r`, `--max-requests`: 每个关键词最大请求次数
- `-w`, `--max-workers`: 最大并发数

## 注意事项

- 使用前请确保已启动SQLMap API服务：`sqlmapapi -s`
- 请合法合规使用本工具，仅用于授权的安全测试
- 建议使用代理或VPN避免IP被封

## 许可证

本项目采用 MIT 许可证

