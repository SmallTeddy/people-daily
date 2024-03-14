import os
import PyPDF2
import random
import time
from urllib.parse import urljoin
import re
import requests
from lxml import etree
import shutil
 
url = "http://paper.people.com.cn/rmrb/paperindex.htm"
headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36 SE 2.X MetaSr 1.0"
}
 
resp_init = requests.get(url, headers=headers)
resp_init.encoding = "UTF-8"
resp_content = resp_init.text
resp_init.close()
 
skip_url = re.compile(r'HTTP-EQUIV="REFRESH".*?URL=(?P<skip_url>.*?)"></head>', re.S)
obj_list = skip_url.finditer(resp_content)
 
for element in obj_list:
    ul = element.group("skip_url")
    skip_url = urljoin(url, ul)
print(skip_url)
 
resp_index = requests.get(skip_url, headers=headers)
resp_index.encoding = "UTF-8"
tree = etree.HTML(resp_index.text)
resp_index.close()
 
pdf_name = tree.xpath("//*[@id='main']/div[2]/div[1]/p[1]/text()")[0].strip().replace("\r\n", "")
pdf_name = re.sub(r'\s+', ' ', pdf_name)
print(pdf_name)
 
pdf_href = tree.xpath("//*[@id='main']/div[1]/div[2]/p[2]/a/@href")[0]
download_pdf_href = urljoin(skip_url, pdf_href)
print(download_pdf_href)
hrefs = tree.xpath("//*[@id='main']/div[2]/div[2]/div/div/a/@href")
 
 
def save_pdf(download_path, pdf_href, pdf_detail_name):
    resp_download_pdf = requests.get(pdf_href, headers=headers)
    resp_download_pdf.close()
 
    # 创建文件夹，不存在就创建
    path = f"{download_path}/temp_file"
    if not os.path.exists(path):
        os.mkdir(rf"{download_path}/temp_file")
 
    with open(f"{download_path}/temp_file/{pdf_detail_name}", mode="wb") as f:
        f.write(resp_download_pdf.content)
    print(f"{pdf_detail_name} 下载完成")
 
 
def init_download(download_path):
    for href in hrefs:
        detail_page = urljoin(skip_url, href)
        resp_detail = requests.get(detail_page, headers=headers)
        resp_detail.encoding = "UTF-8"
        tree = etree.HTML(resp_detail.text)
        resp_detail.close()
 
        pdf_href = tree.xpath("//*[@id='main']/div[1]/div[2]/p[2]/a/@href")[0]
        download_pdf_href = urljoin(skip_url, pdf_href)
        pdf_detail_name = pdf_href.split("/")[-1]
        num = random.randint(1, 5)
        print(f"{detail_page}, {pdf_detail_name}, 随机暂停时间：{num}秒")
        save_pdf(download_path, download_pdf_href, pdf_detail_name)
        time.sleep(num)
 
 
def merge_pdfs(file_list, output):
    pdf_merger = PyPDF2.PdfMerger()
    for file in file_list:
        with open(file, 'rb') as f:
            pdf_merger.append(f)
    with open(output, 'wb') as f:
        pdf_merger.write(f)
 
 
if __name__ == '__main__':
    current_directory = os.getcwd()
    dir_path = current_directory
    init_download(dir_path)
 
    # 获取文件夹下pdf文件
    pdf_lst = [f for f in os.listdir(f"{dir_path}/temp_file") if f.endswith('.pdf')]
    # 合成绝对路径
    file_list = [os.path.join(f"{dir_path}/temp_file", filename) for filename in pdf_lst]
    print(file_list)
 
    output = f'{dir_path}/{pdf_name}.pdf'
    merge_pdfs(file_list, output)
    if os.path.exists(f"{dir_path}/temp_file"):
        shutil.rmtree(f"{dir_path}/temp_file")
    print(f"下载已完成：{output}")
