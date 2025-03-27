import json
import csv
import sys
import requests
from transcript_parser import extract_transcript, fetch_from_url

def convert_json_to_csv(json_file, csv_file):
    """
    将JSON格式的会议记录转换为CSV格式
    
    Args:
        json_file: JSON文件路径
        csv_file: 输出的CSV文件路径
    """
    # 读取JSON文件
    with open(json_file, 'r', encoding='utf-8') as f:
        transcript = json.load(f)
    
    # 写入CSV文件
    with open(csv_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        # 写入表头
        writer.writerow(['说话人', '时间', '内容'])
        # 写入数据
        for item in transcript:
            writer.writerow([
                item['speaker'],
                item['time'],
                item['content']
            ])
    
    print(f"已成功将 {json_file} 转换为 {csv_file}")
    print(f"共转换了 {len(transcript)} 条对话")

def convert_transcript_to_csv(transcript, csv_file):
    """
    将会议记录直接转换为CSV格式
    
    Args:
        transcript: 会议记录数据
        csv_file: 输出的CSV文件路径
    """
    # 写入CSV文件
    with open(csv_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        # 写入表头
        writer.writerow(['说话人', '时间', '内容'])
        # 写入数据
        for item in transcript:
            writer.writerow([
                item['speaker'],
                item['time'],
                item['content']
            ])
    
    print(f"已成功将会议记录转换为 {csv_file}")
    print(f"共转换了 {len(transcript)} 条对话")

def main():
    # 检查命令行参数
    if len(sys.argv) == 3:
        # 传统模式：从JSON文件转换为CSV
        json_file = sys.argv[1]
        csv_file = sys.argv[2]
        convert_json_to_csv(json_file, csv_file)
    elif len(sys.argv) == 2:
        # 新模式：从URL直接提取并转换为CSV
        url = sys.argv[1]
        csv_file = "output.csv"
        
        if url.startswith(('http://', 'https://')):
            print(f"从URL获取内容: {url}")
            html_content = fetch_from_url(url)
            transcript = extract_transcript(html_content)
            convert_transcript_to_csv(transcript, csv_file)
        else:
            print("请提供有效的URL或者使用传统模式")
            print("用法1: python csv_converter.py 输入文件.json 输出文件.csv")
            print("用法2: python csv_converter.py URL地址")
            sys.exit(1)
    else:
        print("用法1: python csv_converter.py 输入文件.json 输出文件.csv")
        print("用法2: python csv_converter.py URL地址")
        sys.exit(1)

if __name__ == "__main__":
    main() 