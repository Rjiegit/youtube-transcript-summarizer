#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from file_manager import FileManager


def test_truncate_filename():
    """測試檔名截斷功能"""

    # 測試案例 1: 正常長度的檔名
    normal_filename = "_summarized_20250719222701_正常長度的標題.md"
    result1 = FileManager.truncate_filename(normal_filename)
    print(f"測試1 - 正常檔名: {result1}")

    # 測試案例 2: 過長的檔名（模擬原始錯誤）
    long_filename = "_summarized_20250719222701_🚀彻底改写Claude Code编程方式！从提示词工程到上下文工程！AI编程能力提升百倍！从需求分析到代码生成全自动化！保姆级实战教程！支持Windows！零基础用Claude Code开发AI智能体.md"
    result2 = FileManager.truncate_filename(long_filename)
    print(f"測試2 - 過長檔名: {result2}")
    print(f"截斷後長度: {len(result2.encode('utf-8'))} bytes")

    # 測試案例 3: 不同的副檔名
    long_filename_txt = "_summarized_20250719222701_超級長的標題" * 10 + ".txt"
    result3 = FileManager.truncate_filename(long_filename_txt, max_length=50)
    print(f"測試3 - 不同副檔名: {result3}")

    # 測試案例 4: 包含特殊字符的長檔名
    special_filename = "_summarized_20250719222701_📝🚀💻這是一個包含emoji和中文的超級長標題用來測試檔名截斷功能是否正常運作.md"
    result4 = FileManager.truncate_filename(special_filename)
    print(f"測試4 - 特殊字符: {result4}")
    print(f"截斷後長度: {len(result4.encode('utf-8'))} bytes")


if __name__ == "__main__":
    test_truncate_filename()
