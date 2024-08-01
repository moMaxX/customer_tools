import requests
import argparse
from bs4 import BeautifulSoup
from tabulate import tabulate
import json
import chardet


class ComPanyAction:
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument('-c', '--company', help='企业名称')
        self.parser.add_argument('-f', '--file', help='企业名称文件')
        self.parser.add_argument('-n', '--noname', help='模糊查询模式')
        self.parser.add_argument('-i', '--init', help='初始化')
        self.args = self.parser.parse_args()

    #创建get方法，供外部函数调用内部定义参数
    def get_args(self):
        return self.args
    
    def parse_argument(self):
        if all(v is None for v in vars(self.args).values()):
            self.parser.print_help()
            exit()

    #初始化函数，写入cookie值信息
    def init(self):

        import configparser
        from urllib.parse import quote
        cookie = input('请输入cookie值(网站地址：https://www.riskbird.com):')
        cookie = quote(cookie)

        config = configparser.ConfigParser(interpolation=None)
        #引入错误处理机制
        try:
            config.read('config.ini')
        except configparser.MissingSectionHeaderError:
            #如果文件格式不正确或为空，创建一个新的配置文件并添加default
            with open('config.ini', 'w') as configfile:
                config.add_section('default')
                config.write(configfile)

        config.read('config.ini')
        if not config.has_section('default'):
            config.add_section('default')
        
        config.set('default', 'cookie', cookie)

        with open('config.ini', 'w') as configfile:
            config.write(configfile)

    #获取cookie信息
    def get_cookie(self):
        import configparser
        from urllib.parse import unquote
        config = configparser.ConfigParser(interpolation=None)
        config.read('config.ini')
        cookie = config.get('default', 'cookie')
        cookie = unquote(cookie)

        return cookie

    def fengniao_query_res(self, company):
        cookie = self.get_cookie()
        url = 'https://www.riskbird.com/ent/'
        headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
        'cookie': cookie,
        'referer': 'https://www.riskbird.com/center/record'
    }

        url = url + company
        res = requests.get(url, headers=headers)
        # 解析HTML文档
        soup = BeautifulSoup(res.text, 'html.parser')

        try:
            # 定位到最外层的div
            outer_div = soup.find('div', id='__nuxt')

            # 然后在该div下查找下一个div
            root_box_div = outer_div.find('div', class_='root-box')

            # 接着在root_box_div下查找下一个div
            content_box_div = root_box_div.find('div', class_='content-box')

            # 继续在content_box_div下查找下一个div
            xs_route_page_div = content_box_div.find('div', class_='xs-route-page')

            # 再次在xs_route_page_div下查找下一个div
            ent_content_page_div = xs_route_page_div.find('div', class_='ent-content-page')

            # 最后在ent_content_page_div下查找所有的div，其中class为'info-basic-box'
            info_basic_boxes = ent_content_page_div.find_all('div', class_='info-basic-box')

            # 在每个info_basic_box中查找a标签
            for box in info_basic_boxes:
                a_tags = box.find_all('a', href=True)  # 查找所有包含href属性的a标签
                if a_tags:
                    for a_tag in a_tags:
                        if a_tag['href'].startswith('http'):  # 如果href属性以http开头，则认为是一个完整的链接
                            print(f'Found a complete link: {a_tag["href"]}')
                            self.write_res(company, a_tag['href'])
                else:
                    print('该企业可能不存在官网，可点击\n{0}\n进行人工查询'.format("https://www.riskbird.com/"))
                    # print(f'Found an <a> tag with href="{a_tag["href"]}"')
        except Exception as e:
            print(f'Error occurred: {e}')

    def fengniao_query_comname(self, pageNo = 1):
        cookie = self.get_cookie()
        url = 'https://www.riskbird.com/riskbird-api/newSearch'
        headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
        'cookie': cookie
    }
        data = {
        "queryType": "1", 
        "searchKey": self.args.noname,
        "pageNo": pageNo, 
        "range": 10,
        "selectConditionData": "{\"regionid\":\"\",\"status\":\"\",\"nicid\":\"\",\"sort_field\":\"\"}"
    }

        response_data = requests.post(url, headers=headers, json=data)
        response_data = json.loads(response_data.text)

        #判断是否查询到公司参数
        found = False

        try:
            if response_data['code'] == 20000:
                data_list = response_data['data']['list']

                table_data = []

                for company_info in data_list:
                    if company_info['ENTNAME']:
                        found = True
                        entname = company_info['ENTNAME']
                        tels = company_info['tels']
                        emails = company_info['emails']
                        zijin = company_info['REGCAP'] + company_info['REGCAPCUR']
                        table_data.append([entname, tels, emails, zijin])
                    else:
                        exit('未查询到公司参数')
                    # print(entname)
                headers = ['公司名称', '联系电话', '联系邮箱', '注册资金']
                print(tabulate(table_data, headers=headers, tablefmt='grid'))
                self.fanye_query_res(found)
            else:
                print(f'遇到错误，代码为：{response_data["code"]}')
        
            # if found:
            #     print('1.查询结果翻页        2.查询具体公司')
            #     num = input('请输入要查询的选项:')
            #     if num == '1':
            #     company_name = input('请输入要具体查询的公司名称:')
            #     fengniao_query_res(company_name)
            #     exit()#阻止闭环查询出现，直接调用函数之后强制退出执行
        except Exception as e:
            print(f'Error occurred: {e}')

    def fanye_query_res(self, found):
        if found:
            print('1.查询结果翻页        2.查询具体公司')
            num = input('请输入要查询的选项:')
            if num == '1':
                pageno = input('请输入要查询的页码:')
                self.fengniao_query_comname(pageno)
            if num == '2':
                company_name = input('请输入要具体查询的公司名称:')
                self.fengniao_query_res(company_name)
                exit()#阻止闭环查询出现，直接调用函数之后强制退出执行


    def write_res(self, company, url):
        with open(f'{company}.txt', 'w') as w:
            w.write(url)

def main():
    a = ComPanyAction()
    a.parse_argument()
    args = a.get_args()

    if args.init:
        print('初始化模式启动中.....')
        a.init()

    if args.noname:
        print(f'模糊查询模式启动中......')
        while True:
            company = args.noname
            a.fengniao_query_comname()
    elif args.company:
        print(f'查询企业：{args.company}主域名中.....')
        a.fengniao_query_res(args.company)
    elif args.file:
        print(f'根据文件批量查询企业主域名中：{args.file}')
        with open(args.file, 'rb') as i:
            result = chardet.detect(i.read(1000))
        with open(args.file, 'r', encoding=result['encoding']) as f:
            for line in f.readlines():
                a.fengniao_query_res(line.strip())

if __name__ == '__main__':
    banner = '''
-------------------------------------
    ______    _____
   / ____/   / ___/_________ _____
  / __/______\__ \/ ___/ __ `/ __ \\
 / /__/_____/__/ / /__/ /_/ / / / /
/_____/    /____/\___/\__,_/_/ /_/
-------------------------------------
简易自用企业官网查询工具
-------------------------------------
'''
    print(banner)
    main()
