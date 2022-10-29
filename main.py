from threading import Thread
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import random
import time
import datetime

NUM_OF_RESULTS = 50  # после скольких находок остановить сканирование
NUM_OF_THREADS = 10  # количество потоков

header = {'User-Agent': str(UserAgent().chrome)}
all_results = []


class Group:
    def __init__(self, url, name, subs, image_url, posts, last_date):
        self.url = url
        self.name = name
        self.subs = subs
        self.image_url = image_url
        self.posts = posts
        self.last_date = last_date

    def __repr__(self):
        repr_ = 'Group('
        for k, v in self.__dict__.items():
            repr_ += f'{k}={repr(v)}, '
        repr_ += ')'
        return repr_

    def __str__(self):
        return f'Group({self.url} {self.name}, subs: {self.subs}, posts: {self.posts})'


def gen_rand_url():
    id_ = str(random.randint(0, 99999999))
    id_ = '0' * (8 - len(id_)) + id_
    return f'https://vk.com/public{id_}'


def save_result(groups_list):
    with open('result.html', 'a', encoding='UTF8') as file:
        file.write('<br>\n')
        file.write(f'<div class="dateTime">[{datetime.datetime.now().strftime("%Y-%b-%d %H:%M")}]</div>\n')
        for group in groups_list:
            image_url = group.image_url if group.image_url else "https://st3-13.vk.com/images/community_200.png?1"
            # определяем, будет ли подсвечиваться значение
            posts_value_class = 'class="number"' if (group.posts is not None and group.posts != 0) else ""
            subs_value_class = 'class="number"' if (group.subs is not None) else ""
            # date_value_class = 'class="number"' if (group.last_date is not None) else ""
            date_value_class = ""

            file.write(f'\n')
            file.write(f'<div class="line">\n')
            file.write(f'    <span class="hostSpan"><a href="{group.url}">{group.url}</a></span>\n')
            file.write(f'    <span class="postsSpan">posts: <font {posts_value_class}>{group.posts}</font></span>\n')
            file.write(f'    <span class="subsSpan">subs: <font {subs_value_class}>{group.subs}</font></span>\n')
            file.write(
                f'    <span class="lastDate">last date: <font {date_value_class}>{group.last_date}</font></span>\n')
            file.write(f'    <span class="imgSpan"><img src="{image_url}"></span>\n')
            file.write(f'    <span class="nameSpan">{group.name}</span>\n')
            file.write(f'</div>\n')


def save_result_without_format(groups_list):
    with open('result.txt', 'a', encoding='UTF8') as file:
        for group in groups_list:
            file.write(repr(group) + '\n')


def get_info(url):
    r = requests.get(url, headers=header)
    soup = BeautifulSoup(r.text, 'lxml')

    # обработка ошибок
    msg_div = soup.find('div', class_="message_page_body")
    if msg_div:
        if 'Вы попытались загрузить более одной однотипной страницы в секунду' in msg_div.text:
            return
    close_span = soup.find('span', class_="PageActionCell__label")
    if close_span:
        if 'Закрытая группа' in close_span.text:
            return
    blocked_div = soup.find('div', class_="groups_blocked_text")
    if blocked_div:
        if 'Сообщество заблокировано' in blocked_div.text:
            return
    private_div = soup.find('div', class_="group_info_private")
    if private_div:
        if 'Это частное сообщество. Доступ только по приглашениям администраторов' in private_div.text:
            return

    # получение параметров
    name_tag = soup.find('h1', class_="page_name")
    if name_tag:
        name = name_tag.text
    else:
        name = None

    if soup.find('div', id="public_followers"):
        subs = soup.find('div', id="public_followers").find('span', class_="header_count fl_l").text
    elif soup.find('div', id="group_followers"):
        subs = soup.find('div', id="group_followers").find('span', class_="header_count fl_l").text
    else:
        subs = None
    if subs is not None:
        if ' ' in subs:
            subs = subs.replace(' ', '')
        subs = int(subs)

    if soup.find('img', class_="page_avatar_img"):
        tag = soup.find('img', class_="page_avatar_img")
        image_url = tag['src']
    else:
        image_url = None

    if soup.find('div', id="page_wall_posts"):
        posts = soup.find('div', id="page_wall_posts").contents
        posts = list(filter(lambda x: x.name == 'div', posts))
        n_posts = len(posts) - 1
        if n_posts > 0:
            date_last_post = posts[0].find('span', class_="rel_date").text
        else:
            date_last_post = None
        pass
    else:
        return

    result.append(Group(url, name, subs, image_url, n_posts, date_last_post))


def key_sort(group):
    posts = group.posts
    if posts is None:
        posts = 0
    posts = -posts

    subs = group.subs
    if subs is None:
        subs = 0
    subs = -subs

    date = group.last_date
    if date is None:
        date = 9999
    else:
        if date.split()[-1].isdigit():
            date = int(group.last_date.split()[-1])

    return posts, subs, date


while len(all_results) < NUM_OF_RESULTS:
    threads = []
    result = []

    t0 = time.time()
    for i in range(NUM_OF_THREADS):
        threads.append(Thread(target=get_info, args=(gen_rand_url(),)))
        threads[-1].start()
    for t in threads:
        t.join()
    all_results.extend(result)

    print(f'time: {time.time() - t0:.2f} s.')
    for r in result:
        print(r)
    print()

all_results.sort(key=key_sort)

save_result_without_format(all_results)
save_result(all_results)
