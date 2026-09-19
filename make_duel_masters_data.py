# デュエルマスターズのカードデータをスクレイピング
import connect_html
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.select import Select
import configparser
import os
import csv
import re
import duel_masters_card_box

headless_mode = True
export_path = 'master'
thread_count = -1


def LoadEnviormentVariables(enviorment_path):
    global headless_mode
    global export_path
    global thread_count

    if os.path.exists(enviorment_path):
        config = configparser.ConfigParser()
        config.read(enviorment_path, encoding='utf-8')
        try:
            headless_mode = config.getboolean('settings', 'headless_mode')
        except Exception:
            pass
        try:
            export_path = config.get('settings', 'export_path')
        except Exception:
            pass
        try:
            thread_count = config.getint('settings', 'thread_count')
        except Exception:
            pass

    # 元コードではこのフォルダーを作成していなかったため、
    # 初回実行時に FileNotFoundError になる問題を修正。
    export_path = os.path.abspath(os.path.expanduser(export_path))
    os.makedirs(export_path, exist_ok=True)

    print('CSV保存先:', export_path)
    duel_masters_card_box.SettingEnviorment(
        headless_mode, export_path, thread_count
    )


def IsLatestData(driver, first_card, card_count):
    html = connect_html.GetBeautifulSoupFromDriver(driver)
    card_list = duel_masters_card_box.GetCardList(html)
    del card_list[1:]
    card_box = duel_masters_card_box.CardPageProcedure(card_list)
    print('top card : ' + card_box[0].name)
    print('data top card : ' + first_card)
    count = html.select_one('#total_count').text
    print('card count : ' + count)
    print('data card count : ' + str(card_count))
    return card_box[0].name == first_card and card_count == int(count)


def safe_filename(value):
    value = re.sub(r'[\\/:*?"<>|\r\n]+', '_', str(value)).strip()
    return value or 'unknown_product'


def PageCroll(driver, file_path):
    row_count = 1
    first_card = None

    if os.path.exists(file_path):
        with open(file_path, 'r', newline='', encoding='utf-8') as file:
            matrix = list(csv.reader(file))
            row_count = len(matrix) - 1
            if row_count > 1:
                first_card = matrix[1][1]
                if not IsLatestData(driver, first_card, row_count):
                    print('更新が必要です')
                    row_count = 1
                else:
                    print('データは最新です:', file_path)
                    return

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    print('CSV作成中:', file_path)
    with open(file_path, 'w', newline='', encoding='utf-8') as file:
        duel_masters_card_box.DuelMastersCardBox(driver, row_count, file)
    print('complete:', file_path)


if __name__ == '__main__':
    LoadEnviormentVariables('enviorment.ini')
    print('作業フォルダー:', os.getcwd())

    driver = connect_html.GetDriver(
        'https://dm.takaratomy.co.jp/card/', headless_mode
    )
    try:
        html = connect_html.GetBeautifulSoupFromDriver(driver)
        products = driver.find_element(
            'xpath', '//*[@id="search_cond"]/div[1]/div[2]/select'
        )
        select_products = Select(products)

        for option in select_products.options:
            if option.get_attribute('value') == '':
                continue

            product_id = option.get_attribute('value')
            select_products.select_by_value(product_id)
            search_button = driver.find_element(
                'xpath', '//*[@id="search_cond"]/div[3]/input[1]'
            )
            search_button.click()

            wait = WebDriverWait(driver, 100)
            wait.until(lambda d: d.execute_script('return jQuery.active') == 0)
            wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')

            product_name = safe_filename(option.get_attribute('text'))
            PageCroll(driver, os.path.join(export_path, product_name + '.csv'))
            print(product_name + ' complete')
    finally:
        connect_html.ReleaseDriver(driver)

    print('全てのプロセスを完了しました')
