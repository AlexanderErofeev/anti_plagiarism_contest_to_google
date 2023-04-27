from Anti_plagiarism_settings import *
import time
import requests
from bs4 import BeautifulSoup
import multiprocessing
from loader_to_google import connection_to_sheets, update_row, update_value, alignment, clear_table
from urllib import parse
import sys
import pandas as pd
import datetime
sys.setrecursionlimit(10000)


def print_log(log_string):
    print(f"[{datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')}] {log_string}")


def percent(value_count, all_value_count):
    return str(round((value_count / all_value_count) * 100, 2)) + '%'


def start_search(expected_count):
    plagiarism_page = requests_get(f"{DOMAIN}/admin/similar-solution?contestId={CONTEST_ID}&per-page=100")
    csrf_token = BeautifulSoup(plagiarism_page.text, 'html.parser').body\
        .find('form', attrs={'id': 'start-check-frm'})\
        .find('input', attrs={'name': 'csrf-token'})\
        .get('value')

    start_r = requests.get(f"{DOMAIN}/admin/similar-solution/start-search?contestId={CONTEST_ID}&csrf-token={csrf_token}&useSimpleComparator=true&mode=ok-only", cookies=CUSTOM_COOKIE)

    if start_r.status_code == 200:
        print_log("Начата проверка на плагиат в Яндекс.Контест")
    else:
        print_log("Ошибка начала проверки на плагиат в Яндекс.Контест")
        return

    time.sleep(BASIC_TIME_DELAY_SEC)

    while True:
        temp_page = requests_get(f"{DOMAIN}/admin/similar-solution?contestId={CONTEST_ID}&per-page=100")
        table = BeautifulSoup(temp_page.text, 'html.parser').body \
            .find_all('table')[1] \
            .find('tbody').find_all("tr")
        statuses = [el.find_all("td")[0].text for el in table]

        running_count = sum([1 if status == 'running' else 0 for status in statuses])
        print_log(f"Завершено на {percent(expected_count - running_count, expected_count)}")

        if 'running' not in statuses:
            break

        time.sleep(TIME_BETWEEN_CONTEST_CHECKS)

    print_log("Завершена проверка на плагиат в Яндекс.Контест")


def get_problems_names():
    plagiarism_page = requests_get(f"{DOMAIN}/contest/{CONTEST_ID}/problems")
    names = BeautifulSoup(plagiarism_page.text, 'html.parser').body\
        .find('ul', attrs={'class': 'tabs-menu_role_problems'})\
        .find_all('span', attrs={'class': 'tabs-menu__tab-content-text'})
    names = [name.text.split('. ')[1] for name in names]
    return names


def get_problems_id(pr_names):
    plagiarism_page = requests_get(DOMAIN + '/admin/similar-solution?contestId=' + CONTEST_ID + '&per-page=100')
    table = BeautifulSoup(plagiarism_page.text, 'html.parser').body\
        .find_all('table')[1]\
        .find('tbody').find_all("tr")
    table = [el.find_all("td") for el in table]

    ans = {}
    for pr_name in pr_names:
        for row in table:
            if row[0].text == 'completed' and row[2].text == pr_name:
                dict_from_query = parse.urlparse(DOMAIN + row[2].find('a').get('href')).query
                ans[pr_name] = parse.parse_qs(dict_from_query)['jobId'][0]
                break

        if pr_name not in ans:
            ans[pr_name] = None

    return ans


def is_commonality_dictionarys(first_mas, second_mas):
    len_sum = len(set(first_mas + second_mas))
    return len_sum != len(first_mas) + len(second_mas)


def requests_get(url):
    r = None
    while r is None:
        try:
            temp_r = requests.get(url, cookies=CUSTOM_COOKIE, timeout=5)
            if temp_r.status_code != 200:
                print_log(f"Ошибка {temp_r.status_code} с URL: {url}")
            else:
                r = temp_r
        except requests.exceptions.Timeout:
            print_log(f"Ошибка timeout с URL: {url}")
        except requests.exceptions.ConnectionError:
            print_log(f"Ошибка connection с URL: {url}")
    return r


def requests_post(url, post_data):
    r = None
    while r is None:
        try:
            r = requests.post(url, data=post_data, cookies=CUSTOM_COOKIE, timeout=5)
        except requests.exceptions.Timeout:
            print_log(f"Ошибка timeout с URL: {url}")
        except requests.exceptions.ConnectionError:
            print_log(f"Ошибка с URL: {url}")
    return r


def comparison_page_parse(coauthor):
    coauthor_link = coauthor.find_all("a")[1] \
        .get('href')

    comparison_with_coauthor_page = requests_get(DOMAIN + coauthor_link)
    comparison_with_coauthor = BeautifulSoup(comparison_with_coauthor_page.text, 'html.parser') \
        .find('table') \
        .find_all("tr")

    pair_name = comparison_with_coauthor[4].find_all("td")
    pair_time = comparison_with_coauthor[5].find_all("td")

    return {pair_name[1].text: pair_time[1].text, pair_name[2].text: pair_time[2].text}


def coauthors_list_parse(cheater, job_id):
    cheater = cheater.find("a")
    cheater_id = cheater.get('data-participantid')
    post_data = {'contestId': CONTEST_ID, 'jobId': job_id, 'participantId': cheater_id}

    coauthors_page = requests_post(DOMAIN + '/admin/similar-solution/coauthors', post_data)

    coauthors = BeautifulSoup(coauthors_page.text, 'html.parser')\
        .find_all("li")

    cheater_time = comparison_page_parse(coauthors[-1])[cheater.text]

    return cheater.text, cheater_time, [cheater.text] + [coauthor.find("a").text for coauthor in coauthors]


if __name__ == '__main__':
    problems_names = get_problems_names()
    print_log(f"Запрошено задач: {len(problems_names)}")
    print_log(f"Запрошенные задачи: {', '.join(problems_names)}")

    if IS_START_SEARCH_IN_CONTEST:
        start_search(len(problems_names))

    jobs_id = list(get_problems_id(problems_names).values())
    print_log(f"ID страниц плагиата к задачам: {', '.join(jobs_id)}")

    problems_list = {}

    for job_id in jobs_id:
        cheaters_in_problem_page = requests_get(DOMAIN + '/admin/similar-solution/list-similar-pairs?jobId=' + str(job_id) + '&contestId=' + CONTEST_ID)
        cheaters_in_problem_page = BeautifulSoup(cheaters_in_problem_page.text, 'html.parser').body

        problem_name = cheaters_in_problem_page.find('h3').text[24:]
        print_log(f"Начата выгрузка задачи: {problem_name}")
        problem_link = f'=ГИПЕРССЫЛКА("{DOMAIN}/admin/similar-solution/list-similar-pairs?jobId={job_id}&contestId={CONTEST_ID}"; "{problem_name}")'

        if problem_name in IGNORE_PROBLEMS_LIST:
            problems_list[problem_link] = []
            continue

        cheaters_in_problem = cheaters_in_problem_page\
            .find('div', attrs={'id': 'content'})\
            .find_all("li")

        if IS_USES_MULTIPROCESSING:
            with multiprocessing.Pool(PROCESSOR_COUNT) as p:
                list_copy = p.starmap(coauthors_list_parse, zip(cheaters_in_problem, [job_id] * len(cheaters_in_problem)))
        else:
            list_copy = [coauthors_list_parse(el, job_id) for el in cheaters_in_problem]

        cheater_times = {cheater: time for cheater, time, _ in list_copy}
        list_copy = [mas for _, _, mas in list_copy]

        final_list_copy = []
        for i in range(len(list_copy)):
            for j in range(i + 1, len(list_copy)):
                if is_commonality_dictionarys(list_copy[i], list_copy[j]):
                    list_copy[j] = list(set(list_copy[j] + list_copy[i]))
                    list_copy[i] = []
                    break
            if list_copy[i] != []:
                final_list_copy.append(list(sorted(list_copy[i], key=lambda el: cheater_times[el])))

        problems_list[problem_link] = final_list_copy
        # print(list_copy)
        # print(cheater_times)
        # print(final_list_copy)

    df = pd.read_csv(USERS_LOGINS_FILE, index_col='login').dropna()
    dict_fio = df['fio'].to_dict()

    for key in problems_list:
        piple_list = problems_list[key]
        piple_list = sorted(piple_list, key=lambda x: len(x), reverse=True)
        if IS_REMOVE_OTHER_USERS:
            piple_list = [[dict_fio[login] for login in piple_grup if login in dict_fio] for piple_grup in piple_list]  # Удаление ненужнх пользователей
        else:
            piple_list = [pd.Series([dict_fio[login] if login in dict_fio else DEFAULT_NAME_FOR_OTHER_USERS for login in piple_grup]).drop_duplicates(keep='first').tolist() for piple_grup in piple_list]  # Замена ненужных пользователей и удаление их дубликатов
        piple_list = [piple_grup for piple_grup in piple_list if len(piple_grup) > 1]  # Удаление одиночных групп, образовавшихзя из-за удаления пользователей
        piple_list = ['\n'.join(piple_grup) for piple_grup in piple_list]
        problems_list[key] = piple_list

    problems_list = list(problems_list.items())

    service = connection_to_sheets()
    clear_table(service)

    for i in range(len(problems_list)):
        update_row(service, f'A{i + 3}', [str(problems_list[i][0])] + problems_list[i][1])

    max_grups = max([len(el[1]) for el in problems_list])
    update_row(service, 'A2', ['Название задачи'] + [f'Группа {i}'for i in range(1, max_grups + 1)])

    update_value(service, 'A1', f"Обновлено: {datetime.datetime.now().strftime('%d-%m-%Y %H:%M')}")
    alignment(service)

    print_log('Выгрузка успешно завершена')
