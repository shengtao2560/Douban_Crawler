import urllib.request
from bs4 import BeautifulSoup
import re

douban_path = "https://movie.douban.com"
response = urllib.request.urlopen(douban_path)
soup = BeautifulSoup(response, 'html.parser')

div_list = soup.body.find(id='screening')
print(soup.body)
now_movie_taglist = div_list.find_all('li', class_=re.compile(r'^ui-slide-item\s?s?'))
now_movie_list = []

for item in now_movie_taglist:
    now_movie_dict = {'name': item.get('data-title'), 'id': item.get('data-trailer'), 'score': item.get('data-rate')}
    if now_movie_dict['name'] is None:
        pass
    else:
        now_movie_list.append(now_movie_dict)

print(now_movie_list)

for movie in now_movie_list:
    movie['name'] = re.findall(r'\w+', movie['name'])[0]
    movie['id'] = re.findall(r'\d+', movie['id'])[0]

comment_url_list = []
for item in now_movie_list:
    comment_url_list.append('https://movie.douban.com/subject/' + item['id'] + '/comments?start=0&limit=20')

comments_list = []
for url in comment_url_list:
    comment_res = urllib.request.urlopen(url)
    comment_soup = BeautifulSoup(comment_res, 'html.parser')
    comments = [item.string for item in comment_soup.find_all('span', class_='short')]
    comments_list.append(comments)

filename = 'comment.txt'

index = 0
with open(filename, 'w', encoding='utf-8') as file:
    for com_list in comments_list:
        file.write(str(index+1) + '.' + now_movie_list[index]['name']+"  Score:"+now_movie_list[index]['score']+'\n\n')
        file.write("热门评论：\n")
        for com in com_list:
            file.write(com+'\n')
        file.write('\n\n')
        index = index + 1