import os
import PyPDF2
import re
import requests
import shutil
from urllib.parse import urljoin
from lxml import etree
from tqdm import tqdm

# 初始化url
url = "http://paper.people.com.cn/rmrb/paperindex.htm"
# 设置请求头
headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36 SE 2.X MetaSr 1.0"
}

# 发送请求
resp_init = requests.get(url, headers=headers)
# 设置编码
resp_init.encoding = "UTF-8"
# 获取响应内容
resp_content = resp_init.text
# 关闭请求
resp_init.close()

# 匹配跳转链接
skip_url = re.compile(r'HTTP-EQUIV="REFRESH".*?URL=(?P<skip_url>.*?)"></head>', re.S)
# 匹配跳转链接
obj_list = skip_url.finditer(resp_content)

# 遍历跳转链接
for element in obj_list:
    # 获取跳转链接
    ul = element.group("skip_url")
    # 拼接跳转链接
    skip_url = urljoin(url, ul)
# print(skip_url)

# 发送跳转链接请求
resp_index = requests.get(skip_url, headers=headers)
# 设置编码
resp_index.encoding = "UTF-8"
# 解析html
tree = etree.HTML(resp_index.text)
# 关闭请求
resp_index.close()

# 获取pdf文件名
pdf_name = tree.xpath("//*[@id='main']/div[2]/div[1]/p[1]/text()")[0].strip().replace("\r\n", "")
# 去除空格
pdf_name = re.sub(r'\s+', ' ', pdf_name)
# 打印pdf文件名
print(pdf_name)

# 获取pdf文件链接
pdf_href = tree.xpath("//*[@id='main']/div[1]/div[2]/p[2]/a/@href")[0]
# 拼接pdf文件链接
download_pdf_href = urljoin(skip_url, pdf_href)
# print(download_pdf_href)
# 获取pdf文件链接列表
hrefs = tree.xpath("//*[@id='main']/div[2]/div[2]/div/div/a/@href")


def clear_current_line():
    # 清空当前行
    print("\x1c", end="")


def init_download(download_path):
    # for href in tqdm(hrefs, desc='Downloading PDFs', dynamic_ncols=True, leave=True):  # 设置dynamic_ncols为True，leave为True
    for href in tqdm(hrefs, desc='Downloading PDFs'):  # 使用tqdm包装hrefs
    # 遍历pdf文件链接列表
    for href in tqdm(hrefs, desc='Downloading PDFs', dynamic_ncols=True, leave=True):  # 设置dynamic_ncols为True，leave为True
        # 获取pdf文件详情页链接
        detail_page = urljoin(skip_url, href)
        # 发送pdf文件详情页链接请求
        resp_detail = requests.get(detail_page, headers=headers)
        # 设置编码
        resp_detail.encoding = "UTF-8"
        # 解析html
        tree = etree.HTML(resp_detail.text)
        # 关闭请求
        resp_detail.close()

        # 获取pdf文件链接
        pdf_href = tree.xpath("//*[@id='main']/div[1]/div[2]/p[2]/a/@href")[0]
        # 拼接pdf文件链接
        download_pdf_href = urljoin(skip_url, pdf_href)
        # 获取pdf文件名
        pdf_detail_name = pdf_href.split("/")[-1]
        # 保存pdf文件
        save_pdf(download_path, download_pdf_href, pdf_detail_name)


def save_pdf(download_path, pdf_href, pdf_detail_name):
    # 发送pdf文件链接请求
    resp_download_pdf = requests.get(pdf_href, headers=headers)
    # 关闭请求
    resp_download_pdf.close()

    # 创建文件夹，不存在就创建
    path = f"{download_path}/temp_file"
    if not os.path.exists(path):
        os.mkdir(rf"{download_path}/temp_file")

    # 保存pdf文件
    with open(f"{path}/{pdf_detail_name}", mode="wb") as f:
        for data in tqdm(resp_download_pdf.iter_content(chunk_size=1024), desc=f'Saving {pdf_detail_name}'):
            f.write(data)  # 写入数据

    # 打印保存状态
    print(f"{pdf_detail_name} 下载完成")


def merge_pdfs(file_list, output):
    # 创建pdf合并对象
    pdf_merger = PyPDF2.PdfMerger()
    # 遍历pdf文件列表
    for file in file_list:
        # 打开pdf文件
        with open(file, 'rb') as f:
            # 添加pdf文件到pdf合并对象
            pdf_merger.append(f)
    # 保存pdf文件
    with open(output, 'wb') as f:
        # 写入pdf文件
        pdf_merger.write(f)


if __name__ == '__main__':
    # 获取当前路径
    current_directory = os.getcwd()
    # 设置文件夹路径
    dir_path = current_directory
    # 下载pdf文件
    init_download(dir_path)

    # 获取文件夹下pdf文件
    pdf_lst = [f for f in os.listdir(f"{dir_path}/temp_file") if f.endswith('.pdf')]
    # 合成绝对路径
    # 拼接绝对路径
    file_list = [os.path.join(f"{dir_path}/temp_file", filename) for filename in pdf_lst]
    # print(file_list)

    # 设置输出文件名
    output = f'{dir_path}/{pdf_name}.pdf'
    # 合并pdf文件
    merge_pdfs(file_list, output)
    # 删除临时文件夹
    if os.path.exists(f"{dir_path}/temp_file"):
        shutil.rmtree(f"{dir_path}/temp_file")
    # 打印保存状态
    print(f"下载已完成：{output}")
