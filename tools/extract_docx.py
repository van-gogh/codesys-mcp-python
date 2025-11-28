import sys
import zipfile
import xml.etree.ElementTree as ET

"""
简单的 DOCX 文本提取工具

用途：读取 `word/document.xml` 中的文本节点，拼接为纯文本输出，
方便把测试报告等内容用于需求落实与联调说明。
"""

def extract_text(docx_path: str) -> str:
    # 以 Zip 方式打开 docx 并解析主文档 XML
    with zipfile.ZipFile(docx_path) as z:
        data = z.read('word/document.xml')
        root = ET.fromstring(data)
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        # 提取所有文本节点并合并为多行文本
        texts = [t.text for t in root.findall('.//w:t', ns) if t.text]
        return '\n'.join(texts)

def main():
    # 从命令行参数读取 docx 路径并打印提取结果
    p = sys.argv[1]
    print(extract_text(p))

if __name__ == '__main__':
    main()
