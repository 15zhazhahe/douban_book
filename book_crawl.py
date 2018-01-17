# _*_ coding: utf-8 _*_
import time
from urllib.error import HTTPError, URLError
import re
from bs4 import BeautifulSoup
import requests
import numpy
from openpyxl import Workbook

"""
爬取豆瓣2017年度读书榜单
"""

headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/63.0.3239.108 Safari/537.36'}


def get_book_detail(book_id):
    """
    根据book_id进一步访问链接https://book.douban.com/subject/+book_id
    获取需要的作者、出版社、出版年月、定价等详细信息
    param
        book_id(str): douban的书籍编号
    return
        (author,press,publish_date,price)(tuple)
        author: 作者
        press: 出版社
        publish_date: 出版年月
        price: 定价
    """
    url = 'https://book.douban.com/subject/'+book_id
    try:
        req = requests.get(url, headers=headers)
        page_code = req.text
        # print(resulut)
    except (HTTPError, URLError) as e:
        print(e)
    soup = BeautifulSoup(page_code, "lxml")
    info = soup.find('div', {'id': 'info'})
    # print(info)
    '''
    <div id="info" class="">
        <span class="pl">作者:</span>&nbsp;
        <a href="https://book.douban.com/author/2081294/">
                [意]
            埃莱娜·费兰特</a>
        <br>
        <span class="pl">出版社:</span> 人民文学出版社<br>
        <span class="pl">出版年:</span> 2017-4<br>
        <span class="pl">定价:</span> 59.00元<br>
    </div>
    '''
    author_pattern = re.compile(r'\s*作者[:]*')
    author_info = info.find(text=author_pattern).next_element.next_element.string
    author = ''
    for detail in author_info:      # 清洗格式
        author += detail.strip()
    press = info.find(text='出版社:').next_element.string.strip()
    publish_date = info.find(text='出版年:').next_element.string.strip()
    price = info.find(text='定价:')
    if price is None:
        price = '-'
    else:
        price = price.next_element.string.strip()
    # print(author, press, publish_date, price)
    return (author, press, publish_date, price)


def book_spider():
    """
    get请求访问2017豆瓣年度书单内容
    清洗获得的的json数据，拿到需要的信息
    return(tuple)
        page_tag(list): 每页的标签
        page_dict(dict): 存放2017年年度书单的列表
            key(str):
                page_tag(list) 年度书单有多页，每页设置一个tag，便于索引
            value(list)：
                每一个部分的书单排行，包括如下信息
                    0. 书号
                    1. 书名
                    2. 作者
                    3. 出版社
                    4. 出版年月
                    5. 评分
                    6. 评价人数
                    7. 定价
    """
    page_dict = {}  # 存放2017年度书单具体信息
    page_tag = []   # 存放2017年度书单每步种类
    pagenum = 1
    while True:
        book_list = []
        url = 'https://book.douban.com/ithil_j/activity/book_annual2017/widget/'+str(pagenum)
        pagenum += 1
        try:
            req = requests.get(url, headers=headers)
            resulut = req.json()
            # print(resulut)
        except (HTTPError, URLError) as e:
            print(e)
        if req.status_code == 400:
            break
        infos = resulut['res']
        kind_cn = infos['kind_cn']
        if kind_cn in ['书摘', '人物', '逝者', '结束页', '留言板']:              # 跳过书摘
            continue
        tag = infos['payload']['title']   # 该页的标签
        # print(tag)
        info_list = infos['subjects']
        for info in info_list:
            '''
            cover: 封面图片地址
            id: 书本id号
            url: 书记详细信息地址
            title: 书本名字
            rating：评分
            rating_count：评价人数
            '''
            book_info = []
            book_info.append(info['id'])
            book_info.append(info['title'])
            (author, press, publish_date, price) = get_book_detail(book_info[0])
            book_info.append(author)
            book_info.append(press)
            book_info.append(publish_date)
            book_info.append(info['rating'])
            book_info.append(info['rating_count'])
            book_info.append(price)
            book_list.append(book_info)
            print(book_info)

        page_tag.append(tag)
        page_dict.update({tag: book_list})
        print(tag)
        time.sleep(numpy.random.rand()*2)
    # print(page_dict)
    return (page_tag, page_dict)


def book_info_save_execl(page_tag, book_annual2017):
    """
    将爬取的信息存成excel形式
    param
        page_tag(list): 每页标签
        book_annual2017(dict): 每页详细信息
    """
    wb = Workbook()
    ws = wb.active
    for tag in page_tag:
        ws.append([tag, ])
        ws.append(['书号', '书名', '作者', '出版社', '出版年月', '评分', '评价人数', '定价'])
        for book in book_annual2017[tag]:
                ws.append(book)
        ws.append([])
        ws.append([])        
    wb.save("2017年度书单.xlsx")


if __name__ == "__main__":
    (page_tag, book_annual2017) = book_spider()
    print('数据爬取完毕！')
    book_info_save_execl(page_tag, book_annual2017)
    print('数据存储完毕！')
