# encoding: utf-8
import re
import json
import time
import gzip
from bs4 import BeautifulSoup


def get_html(line):
    s1 = line.find(r'"html" : "')
    s2 = line.find(r'\n",', s1)
    html_doc = line[s1 + len('"html" : "'): s2]  # 以字符串的方式提取出html文件
    return html_doc


def get_id(soup):
    # 提取百度百科网页的id
    id = ''
    id_edit = soup.find('a', class_=re.compile(r'bk-editable-edit'))  # 查找标签1
    if id_edit:
        id_string = id_edit[r'data-edit-id'].strip(r'\"')
        id = id_string[0: id_string.find(':')]
    id_Body = soup.find('div', class_=re.compile(r'lemmaWgt-promotion-rightPreciseAd'))  # 查找标签2
    if id_Body:
        id = id_Body[r'data-lemmaid'].strip(r'\"')
    return id

    
def get_name(soup):
	# 提取百度词条的名字
	name = ''
	entry_name = soup.title.get_text()
	name_temp = entry_name[0:entry_name.find('_百度百科')]	
	name = re.sub('\（[^\）]*\）$', '', name_temp)
	return name


def get_polyseme(soup):
    # 提取多义词和义项
    polyseme = []
    polysemeTitle = ''
    polysemeBody = soup.find('div', class_=re.compile('polysemeBody'))  # 查找标签1
    if polysemeBody:
        for link in polysemeBody.find_all('li'):
            polyseme.append(link.get_text().strip('▪'))
        try:
            polysemeTitle = polysemeBody.find('span', class_=re.compile('polysemeTitle')).get_text()
        except:
            pass
    polysemantList_wrapper = soup.find(class_=re.compile('polysemantList-wrapper'))  # 查找标签2
    if polysemantList_wrapper:
        for link in polysemantList_wrapper.find_all('li'):
            polyseme.append(link.get_text().strip('▪'))
        try:
            polysemeTitle = polysemantList_wrapper.find('span', class_=re.compile('selected')).get_text()
        except:
            pass
    return polyseme, polysemeTitle


def get_tag(soup):
    # 提取词条标签
    taglist = []
    open_tag = soup.find('dd', id=re.compile('open-tag-item'))
    if open_tag:
        for link in open_tag.find_all(class_=re.compile('taglist')):  # 正则表达式匹配
            taglist.append(link.get_text().replace(r'\n', ''))
    return taglist


def get_basicInfo(soup):
    # 处理infoBox
    basicInfo = {}
    baseInfoWrap = soup.find('div', class_=re.compile(r'baseInfoWrap'))  # 查找标签1
    if baseInfoWrap:
        for link in baseInfoWrap.find_all('div', class_=re.compile('biItemInner')):
            basicInfo[''.join(link.find('span', class_=re.compile('biTitle')).get_text().split())] \
                = ' '.join(link.find('div', class_=re.compile('biContent')).get_text().split())
    basicInfo_block = soup.find(class_=re.compile("basic-info"))  # 查找标签2
    if basicInfo_block:
        k = 0
        basicinfo_list = basicInfo_block.find_all(class_=re.compile('basicInfo-item'))
        try:
            while k < len(basicinfo_list):
                basicInfo[''.join(basicinfo_list[k].get_text().replace(r'\n', '').split())] \
                    = ' '.join(basicinfo_list[k + 1].get_text().replace(r'\n', '').split())
                k = k + 2
        except:
            pass
    return basicInfo


def read_and_write(filename):
    # fin = open(filename + '.json', 'r', encoding='utf-8')
    fin = gzip.open('data/' + filename + '.json.gz', 'r')
    ferror = open('error/' + filename + '-error-result.json', 'w', encoding='utf-8')
    fout = open('result/' + filename + '-result.json', 'w', encoding='utf-8')

    i = 0  # 行号
    j = 0  # html 号
    line = fin.readline().decode('utf8')  # 读取一行文本
    while line:
        i = i + 1
        if i % 5 == 2:  # html文件所在行
            html_doc = get_html(line)
            soup = BeautifulSoup(html_doc, 'lxml')

            if soup.title and not re.match(r'百度百科.*全球最大中文百科全书', soup.title.get_text()):  # 判断是否空页面
                info_dict = {}
                id = get_id(soup)
                info_dict['id'] = id  # 获取百度百科的id
                info_dict['name'] = get_name(soup)   # 获取百度百科的词条名
                info_dict['basicInfo'] = get_basicInfo(soup)  # 获取词条的基本信息框
                info_dict['多义词'], info_dict['义项'] = get_polyseme(soup)  # 获取多义词和义项
                info_dict['词条标签'] = get_tag(soup)  # 获取词条标签

                if id:
                    fout.write(json.dumps(info_dict, ensure_ascii=False))  # 一行一条百科数据的写入文件
                    fout.write('\n')
                else:
                    ferror.write(json.dumps(info_dict, ensure_ascii=False))  # 一行一条百科数据的写入文件
                    ferror.write('\n')

                j = j + 1
                if j % 100 == 0:
                    print('文件 ' + filename + ' 的第 ', j, ' 个 html ...')

        line = fin.readline().decode('utf8')  # 读下一行文本

    fin.close()
    ferror.close()
    fout.close()


if __name__ == "__main__":

    start = time.clock()  # 计时开始

    for n in range(17, 18):
        t1 = time.clock()  # 计时开始1
        read_and_write(str(n))  # 处理每一个文件
        t2 = time.clock()  # 计时结束1
        print('文件 ' + str(n) + '运行时间: %.3f 秒\n' % (t2 - t1))

    end = time.clock()  # 计时结束
    print('总运行时间: %.3f 秒' % (end - start))
