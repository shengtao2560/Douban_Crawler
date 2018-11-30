from urllib import request
from aip import AipNlp
from bs4 import BeautifulSoup
import re
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import jieba
import requests
import random
import urllib
import os
import time
from PIL import Image
import emoji

now_movie_list = []
emotion_list = []
jieba.add_word('任素汐')
APP_ID = '14963270'
API_KEY = 'DzcClKytSKKGpbTxdSFUcyif'
SECRET_KEY = 'IIIiZbKyHdFDqA7xq17kb8wS3elRVF7a'


def login_douban():
    login_url = "https://accounts.douban.com/login"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64)\
    AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.118 Safari/537.36', }

    my_post = {'redir': 'https://movie.douban.com',
               'form_email': '1505466304@qq.com',
               'form_password': '6305318ST',
               'login': '登录',
               }
    r = requests.post(login_url, data=my_post, headers=headers)
    html = r.text
    if html.__contains__('try'):
        print(html)
    if r.url == 'https://movie.douban.com':
        return html
    reg = r'<img id="captcha_image" src="(.*?)" alt="captcha" class="captcha_image"/>'
    imglist = re.findall(reg, html)
    pic = 'captchas\\%d.jpg' % random.randint(1,100)
    urllib.request.urlretrieve(imglist[0], pic)
    img = Image.open(pic)
    plt.figure("captcha")
    plt.imshow(img)
    plt.show()
    captcha = input('captcha is: ')
    regid = r'<input type="hidden" name="captcha-id" value="(.*?)"/>'
    ids = re.findall(regid, html)

    my_post["captcha-solution"] = captcha
    my_post["captcha-id"] = ids[0]
    q = requests.post(login_url, data=my_post, headers=headers)
    print(q.url)
    return q.text


def jieba_split(txt):
    text = open(txt, "rb").read()
    words_list = []
    word_generator = jieba.cut(text, cut_all=False)
    with open('chineseStopWords.txt') as f:
        str_text = f.read()
        # unicode_text = str_text.encode("utf-8")
        f.close()
    for word in word_generator:
        if word.strip() not in str_text:
            words_list.append(word)
    return ' '.join(words_list)


def get_sentiments(text):
    try:
        sitems=client.sentimentClassify(text)['items'][0]# 情感分析
        print(sitems)
        print('\n')
        positive = sitems['positive_prob']# 积极概率
        confidence = sitems['confidence']# 置信度
        sentiment = sitems['sentiment']# 0表示消极，1表示中性，2表示积极
        return sitems
    except Exception as e:
        print(e)


def get_now_movie(html):
    soup = BeautifulSoup(html)
    div_list = soup.body.find(id='screening')
    print(soup.body)
    now_movie_taglist = div_list.find_all('li', class_=re.compile(r'^ui-slide-item\s?s?'))

    for item in now_movie_taglist:
        now_movie_dict = {'name': item.get('data-title'), 'id': item.get('data-trailer'), 'score': item.get('data-rate')}
        if now_movie_dict['name'] is None:
            pass
        else:
            now_movie_list.append(now_movie_dict)
    # print(now_movie_list)

    for movie in now_movie_list:
        movie['name'] = re.findall(r'\w+', movie['name'])[0]
        movie['id'] = re.findall(r'\d+', movie['id'])[0]
        print(movie['name'] + '_' + movie['score'] + '分')


def getcomment(comment_url_list, filename):
    comments_list = []
    n = 0
    sum = 0
    for url in comment_url_list:
        comment_res = urllib.request.urlopen(url)
        comment_soup = BeautifulSoup(comment_res, 'html.parser')
        comments = [item.string for item in comment_soup.find_all('span', class_='short')]
        # ranks = [item for item in comment_soup.findAll('span', class_='allstar40 rating')]
        comments_list.append(comments)

    with open('comments\\'+ filename + '.txt', 'w', encoding='utf-8') as file:
        print('\n'+filename+'\n')
        for com_list in comments_list:
            for com in com_list:
                print(com)
                pattern = re.compile(r'[\u4e00-\u9fa5]+')
                filterdata = re.findall(pattern, str(com))
                cleaned_comments = ''.join(filterdata)
                sitems = get_sentiments(emoji.demojize(com))
                try:
                    sum = sum + sitems['positive_prob']*sitems['confidence']
                    n = n + sitems['confidence']
                except:
                    print('pass')
                file.write(cleaned_comments + '\n')

    emotion = {'movie': filename,
               'emotion': round(sum / n, 2),
               }
    print(emotion)
    emotion_list.append(emotion)
    create_wordcloud(jieba_split('comments\\' + filename + '.txt'), filename)


def create_wordcloud(wl, filename):
    wc = WordCloud(background_color="white",
                   max_words=2000,
                   scale=16,
                   font_path = "C:\Windows\Fonts\sourcehansans.ttf",
                   max_font_size=60,
                   random_state=30,
        )
    try:
        myword = wc.generate(wl)
        wc.to_file('wordclouds\\' + filename + '.jpg')
        plt.imshow(myword)
        plt.axis("off")
        plt.show()
    except BaseException as e:
        print(e)


if __name__ == '__main__':
    if not os.path.exists('comments\\'):
        os.makedirs('comments\\')
    if not os.path.exists('wordclouds\\'):
        os.makedirs('wordclouds\\')
    if not os.path.exists('captchas\\'):
        os.makedirs('captchas\\')

    client = AipNlp(APP_ID, API_KEY, SECRET_KEY)

    while True:
        html = login_douban()
        if BeautifulSoup(html).title.get_text() == '登录豆瓣':
            print('登录失败，请等待3秒')
            time.sleep(3)
        else:
            print('登录成功')
            break

    get_now_movie(html)

    comment_url_list = []
    for item in now_movie_list:
        for page in range(11):
            comment_url_list.append('https://movie.douban.com/subject/' + item['id'] + '/comments?start=' + str(
                20 * page) + '&limit=20&sort=new_score&status=P')
        getcomment(comment_url_list, item['name'] + '_'+ item['score'] + '分')
        comment_url_list = []

    for i in emotion_list:
        print(i)
