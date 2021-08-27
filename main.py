import feedparser
import time
import os
import re
import pytz
from datetime import datetime
import yagmail
import requests
import markdown
import json
import shutil
from urllib.parse import urlparse


def get_rss_info(feed_url):
    result = {"result": []}
    # 如果请求出错，则重新请求，最多五次
    for i in range(5):
        try:
            headers = {
                # 设置用户代理头(为狼披上羊皮)
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36",
                "Content-Encoding": "gzip"
            }
            # 设置15秒钟超时
            feed_url_content = requests.get(feed_url,  timeout= 15 ,headers = headers).content
            feed = feedparser.parse(feed_url_content)
            feed_entries = feed["entries"]
            feed_entries_length = len(feed_entries)
            print("==feed_url=>>", feed_url, "==len=>>", feed_entries_length)
            for entrie in feed_entries[0: feed_entries_length-1]:
                title = entrie["title"]
                link = entrie["link"]
                date = time.strftime("%Y-%m-%d", entrie["published_parsed"])

                title = title.replace("\n", "")
                title = title.replace("\r", "")
                result["result"].append({
                    "title": title,
                    "link": link,
                    "date": date
                })
            break
        except Exception as e:
            print(feed_url+"第+"+str(i)+"+次请求出错==>>",e)
            pass


    return result["result"]
    


def send_mail(email, title, contents):
    # 判断secret.json是否存在
    user = ""
    password = ""
    host = ""
    try:
        if(os.environ["USER"]):
            user = os.environ["USER"]
        if(os.environ["PASSWORD"]):
            password = os.environ["PASSWORD"]
        if(os.environ["HOST"]):
            host = os.environ["HOST"]
    except:
        print("无法获取 github 的 secrets 配置信息，开始使用本地变量")
        if(os.path.exists(os.path.join(os.getcwd(),"secret.json"))):
            with open(os.path.join(os.getcwd(),"secret.json"),'r') as load_f:
                load_dict = json.load(load_f)
                user = load_dict["user"]
                password = load_dict["password"]
                host = load_dict["host"]
                # print(load_dict)
        else:
            print("无法获取发件人信息")
    
    # 连接邮箱服务器
    # yag = yagmail.SMTP(user=user, password=password, host=host)
    yag = yagmail.SMTP(user = user, password = password, host=host)
    # 发送邮件
    yag.send(email, title, contents)

def replace_readme():
    new_edit_readme_md = [""]
    current_date_news_index = [""]
    
    # 读取EditREADME.md
    print("replace_readme")
    new_num = 0
    with open(os.path.join(os.getcwd(),"EditREADME.md"),'r') as load_f:
        edit_readme_md = load_f.read();
        new_edit_readme_md[0] = edit_readme_md
        before_info_list =  re.findall(r'\{\{latest_content\}\}.*\[订阅地址\]\(.*\)' ,edit_readme_md);
        # 填充统计RSS数量
        new_edit_readme_md[0] = new_edit_readme_md[0].replace("{{rss_num}}", str(len(before_info_list)))
        # 填充统计时间
        ga_rss_datetime = datetime.fromtimestamp(int(time.time()),pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
        new_edit_readme_md[0] = new_edit_readme_md[0].replace("{{ga_rss_datetime}}", str(ga_rss_datetime))
        


        for before_info in before_info_list:
            # 获取link
            link = re.findall(r'\[订阅地址\]\((.*)\)', before_info)[0]
            # 生成超链接
            rss_info = get_rss_info(link)
            latest_content = ""
            parse_result = urlparse(link)
            scheme_netloc_url = str(parse_result.scheme)+"://"+str(parse_result.netloc)
            latest_content = "[暂无法通过爬虫获取信息，点击进入源网站主页]("+ scheme_netloc_url +")"

            # 加入到索引
            try:
                for rss_info_atom in rss_info:
                    if (rss_info_atom["date"] == datetime.today().strftime("%Y-%m-%d")):
                        new_num = new_num + 1
                        current_date_news_index[0] = current_date_news_index[0] + "<br/>"+ "🌈 " +"[" + "‣ " + rss_info_atom["title"] + "| 第" + str(new_num) +"篇"  +"](" + rss_info_atom["link"] +")"  
            except:
                print("An exception occurred")
                
            if(len(rss_info) > 0):
                rss_info[0]["title"] = rss_info[0]["title"].replace("|", "\|")
                rss_info[0]["title"] = rss_info[0]["title"].replace("[", "\[")
                rss_info[0]["title"] = rss_info[0]["title"].replace("]", "\]")
                print("===date===>>", rss_info[0]["date"])
                latest_content = "[" + "‣ " + rss_info[0]["title"] + ( " 🌈 " + rss_info[0]["date"] if (rss_info[0]["date"] == datetime.today().strftime("%Y-%m-%d")) else " \| " + rss_info[0]["date"] ) +"](" + rss_info[0]["link"] +")"  

            if(len(rss_info) > 1):
                rss_info[1]["title"] = rss_info[1]["title"].replace("|", "\|")
                rss_info[1]["title"] = rss_info[1]["title"].replace("[", "\[")
                rss_info[1]["title"] = rss_info[1]["title"].replace("]", "\]")
                print("===date===>>", rss_info[0]["date"])
                latest_content = latest_content + "<br/>[" + "‣ " +  rss_info[1]["title"] + ( " 🌈 " + rss_info[0]["date"] if (rss_info[0]["date"] == datetime.today().strftime("%Y-%m-%d")) else " \| " + rss_info[0]["date"] ) +"](" + rss_info[1]["link"] +")"

            # 生成after_info
            after_info = before_info.replace("{{latest_content}}", latest_content)
            print("====latest_content==>", latest_content)
            # 替换edit_readme_md中的内容
            new_edit_readme_md[0] = new_edit_readme_md[0].replace(before_info, after_info)
    
    # 替换 EditREADME 中的索引
    new_edit_readme_md[0] = new_edit_readme_md[0].replace("{{news}}", current_date_news_index[0])
    # 替换 EditREADME 中的新文章数量索引
    new_edit_readme_md[0] = new_edit_readme_md[0].replace("{{new_num}}", str(new_num))
    # 添加 CDN
    new_edit_readme_md[0] = new_edit_readme_md[0].replace("./_media", "https://cdn.jsdelivr.net/gh/zhaoolee/garss/_media")
        
    # 将新内容
    with open(os.path.join(os.getcwd(),"README.md"),'w') as load_f:
        load_f.write(new_edit_readme_md[0])
    
    return new_edit_readme_md

# 将 README.md 复制到 docs 中

def cp_readme_md_to_docs():
    shutil.copyfile(os.path.join(os.getcwd(),"README.md"), os.path.join(os.getcwd(), "docs","README.md"))
    
def cp_media_to_docs():
    if os.path.exists(os.path.join(os.getcwd(), "docs","_media")):
        shutil.rmtree(os.path.join(os.getcwd(), "docs","_media"))	
    shutil.copytree(os.path.join(os.getcwd(),"_media"), os.path.join(os.getcwd(), "docs","_media"))

def get_email_list():
    email_list = []
    with open(os.path.join(os.getcwd(),"tasks.json"),'r') as load_f:
        load_dic = json.load(load_f)
        for task in load_dic["tasks"]:
            email_list.append(task["email"])
    return email_list



def main():
    readme_md = replace_readme()
    content = markdown.markdown(readme_md[0], extensions=['tables', 'fenced_code'])
    cp_readme_md_to_docs()
    cp_media_to_docs()
    email_list = get_email_list()
    send_mail(email_list, "嘎! RSS订阅", content)


main()