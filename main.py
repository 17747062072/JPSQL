#!/usr/bin/env python3
"""
日本网站SQL注入扫描工具
"""

import os
import sys
import time
import asyncio
import argparse
from datetime import datetime

# 导入配置和工具
from config import OUTPUT_DIR
from utils.logger import get_logger
from utils.file_utils import save_progress

# 导入收集器和扫描器
from collectors.google_collector import GoogleCollector, generate_queries as google_queries
from collectors.fofa_collector import FofaCollector, generate_queries as fofa_queries
from collectors.param_extractor import ParamExtractor
from scanners.sqlmap_scanner import SQLMapScanner

# 创建日志记录器
logger = get_logger("main")

async def run_collector(args):
    """运行收集器
    
    Args:
        args: 命令行参数
    """
    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    if args.collector == "google":
        # 运行Google收集器
        logger.info("开始Google收集...")
        collector = GoogleCollector()
        collector.collect(google_queries(), max_requests_per_query=args.max_requests)
    elif args.collector == "fofa":
        # 运行FOFA收集器
        logger.info("开始FOFA收集...")
        collector = FofaCollector()
        collector.collect(fofa_queries(), max_pages=args.max_requests)
    elif args.collector == "extract":
        # 运行参数提取器
        logger.info("开始参数提取...")
        extractor = ParamExtractor(args.input_file, args.output_file)
        await extractor.extract_params_async(max_workers=args.max_workers)
    else:
        logger.error(f"未知的收集器类型: {args.collector}")

async def run_scanner(args):
    """运行扫描器
    
    Args:
        args: 命令行参数
    """
    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 运行SQLMap扫描器
    logger.info("开始SQLMap扫描...")
    scanner = SQLMapScanner(args.input_file)
    
    if args.async_mode:
        # 异步扫描
        stats = await scanner.scan_async(max_workers=args.max_workers)
    else:
        # 同步扫描
        stats = scanner.scan()
    
    # 保存统计信息
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_progress(stats, f"scan_stats_{timestamp}.json")

async def run_workflow(args):
    """运行完整工作流
    
    Args:
        args: 命令行参数
    """
    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 1. 运行Google收集器
    if not args.skip_google:
        logger.info("步骤1: 开始Google收集...")
        collector = GoogleCollector(output_file=os.path.join(OUTPUT_DIR, "google_urls.txt"))
        collector.collect(google_queries(), max_requests_per_query=args.max_requests)
    
    # 2. 运行FOFA收集器
    if not args.skip_fofa:
        logger.info("步骤2: 开始FOFA收集...")
        collector = FofaCollector(output_file=os.path.join(OUTPUT_DIR, "fofa_urls.txt"))
        collector.collect(fofa_queries(), max_pages=args.max_requests)
    
    # 3. 运行参数提取器
    if not args.skip_extract:
        logger.info("步骤3: 开始参数提取...")
        # 从Google和FOFA结果中提取
        google_file = os.path.join(OUTPUT_DIR, "google_urls.txt")
        fofa_file = os.path.join(OUTPUT_DIR, "fofa_urls.txt")
        
        # 合并URL列表
        combined_file = os.path.join(OUTPUT_DIR, "combined_urls.txt")
        with open(combined_file, "w", encoding="utf-8") as outfile:
            if os.path.exists(google_file):
                with open(google_file, "r", encoding="utf-8") as infile:
                    outfile.write(infile.read())
            if os.path.exists(fofa_file):
                with open(fofa_file, "r", encoding="utf-8") as infile:
                    outfile.write(infile.read())
        
        extractor = ParamExtractor(combined_file, os.path.join(OUTPUT_DIR, "extracted_urls.txt"))
        await extractor.extract_params_async(max_workers=args.max_workers)
    
    # 4. 运行SQLMap扫描器
    if not args.skip_scan:
        logger.info("步骤4: 开始SQLMap扫描...")
        scanner = SQLMapScanner(os.path.join(OUTPUT_DIR, "extracted_urls.txt"))
        
        if args.async_mode:
            # 异步扫描
            stats = await scanner.scan_async(max_workers=args.max_workers)
        else:
            # 同步扫描
            stats = scanner.scan()
        
        # 保存统计信息
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_progress(stats, f"scan_stats_{timestamp}.json")
    
    logger.info("工作流程完成！")

def parse_args():
    """解析命令行参数
    
    Returns:
        解析后的参数
    """
    parser = argparse.ArgumentParser(description="日本网站SQL注入扫描工具")
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # 收集器子命令
    collector_parser = subparsers.add_parser("collect", help="运行收集器")
    collector_parser.add_argument("collector", choices=["google", "fofa", "extract"], help="收集器类型")
    collector_parser.add_argument("-i", "--input-file", default="output/fofa_urls.txt", help="输入文件路径")
    collector_parser.add_argument("-o", "--output-file", default="output/extracted_urls.txt", help="输出文件路径")
    collector_parser.add_argument("-r", "--max-requests", type=int, default=5, help="每个关键词最大请求次数")
    collector_parser.add_argument("-w", "--max-workers", type=int, default=10, help="最大并发数")
    
    # 扫描器子命令
    scanner_parser = subparsers.add_parser("scan", help="运行扫描器")
    scanner_parser.add_argument("-i", "--input-file", default="output/extracted_urls.txt", help="输入文件路径")
    scanner_parser.add_argument("-a", "--async-mode", action="store_true", help="使用异步模式")
    scanner_parser.add_argument("-w", "--max-workers", type=int, default=5, help="最大并发数")
    
    # 工作流子命令
    workflow_parser = subparsers.add_parser("workflow", help="运行完整工作流")
    workflow_parser.add_argument("-sg", "--skip-google", action="store_true", help="跳过Google收集")
    workflow_parser.add_argument("-sf", "--skip-fofa", action="store_true", help="跳过FOFA收集")
    workflow_parser.add_argument("-se", "--skip-extract", action="store_true", help="跳过参数提取")
    workflow_parser.add_argument("-ss", "--skip-scan", action="store_true", help="跳过SQLMap扫描")
    workflow_parser.add_argument("-a", "--async-mode", action="store_true", help="使用异步模式")
    workflow_parser.add_argument("-r", "--max-requests", type=int, default=5, help="每个关键词最大请求次数")
    workflow_parser.add_argument("-w", "--max-workers", type=int, default=5, help="最大并发数")
    
    return parser.parse_args()

async def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()
    
    if args.command == "collect":
        await run_collector(args)
    elif args.command == "scan":
        await run_scanner(args)
    elif args.command == "workflow":
        await run_workflow(args)
    else:
        # 默认运行工作流
        await run_workflow(argparse.Namespace(
            skip_google=False,
            skip_fofa=False,
            skip_extract=False,
            skip_scan=False,
            async_mode=True,
            max_requests=5,
            max_workers=5
        ))

if __name__ == "__main__":
    # 运行主函数
    asyncio.run(main()) 