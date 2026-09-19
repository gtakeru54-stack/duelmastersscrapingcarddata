# デュエル・マスターズのカードデータをスクレイピング

import os
import csv
import re
import configparser

import connect_html
import duel_masters_card_box

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.select import Select


# 初期設定
headless_mode = True
export_path = 'master'
thread_count = -1


def LoadEnviormentVariables(enviorment_path):
    """
    enviorment.iniを読み込み、
    CSV保存先フォルダーを作成する。
    """

    global headless_mode
    global export_path
    global thread_count

    if os.path.exists(enviorment_path):
        config = configparser.ConfigParser()
        config.read(
            enviorment_path,
            encoding='utf-8'
        )

        try:
            headless_mode = config.getboolean(
                'settings',
                'headless_mode'
            )
        except Exception:
            pass

        try:
            export_path = config.get(
                'settings',
                'export_path'
            ).strip()
        except Exception:
            pass

        try:
            thread_count = config.getint(
                'settings',
                'thread_count'
            )
        except Exception:
            pass

    # 相対パスを絶対パスに変換
    export_path = os.path.abspath(
        os.path.expanduser(export_path)
    )

    # 保存フォルダーを自動作成
    os.makedirs(
        export_path,
        exist_ok=True
    )

    print('現在の作業フォルダー:')
    print(os.getcwd())

    print('CSV保存先:')
    print(export_path)

    duel_masters_card_box.SettingEnviorment(
        headless_mode,
        export_path,
        thread_count
    )


def IsLatestData(driver, first_card, card_count):
    """
    既存CSVが最新データか確認する。
    """

    html = connect_html.GetBeautifulSoupFromDriver(driver)

    if html is None:
        print('HTMLを取得できませんでした')
        return False

    card_list = duel_masters_card_box.GetCardList(html)

    if not card_list:
        print('カード一覧を取得できませんでした')
        return False

    # 先頭カードだけを確認
    first_card_list = card_list[:1]

    card_box = duel_masters_card_box.CardPageProcedure(
        first_card_list
    )

    if not card_box:
        print('カードデータを処理できませんでした')
        return False

    top_card = card_box[0].name

    print('top card : ' + str(top_card))
    print('data top card : ' + str(first_card))

    total_element = html.select_one('#total_count')

    if total_element is None:
        print('#total_count が見つかりません')
        return False

    total_text = total_element.get_text(
        strip=True
    )

    # 数字だけを取得
    total_match = re.search(
        r'\d[\d,]*',
        total_text
    )

    if not total_match:
        print('カード枚数を数値に変換できません:', total_text)
        return False

    total_count = int(
        total_match.group().replace(',', '')
    )

    print('card count : ' + str(total_count))
    print('data card count : ' + str(card_count))

    return (
        top_card == first_card
        and int(card_count) == total_count
    )


def safe_filename(value):
    """
    ファイル名に使用できない文字を置き換える。
    """

    value = str(value)

    # Windowsでファイル名に使用できない文字を置換
    value = re.sub(
        r'[\\/:*?"<>|\r\n]+',
        '_',
        value
    )

    # 末尾のピリオドや空白も削除
    value = value.strip().rstrip('.')

    if not value:
        return 'unknown_product'

    return value


def PageCroll(driver, file_path):
    """
    指定された商品ページのカードデータをCSVへ保存する。
    """

    print('保存処理開始:')
    print(file_path)

    # 保存先フォルダーを作成
    parent_dir = os.path.dirname(file_path)

    if parent_dir:
        os.makedirs(
            parent_dir,
            exist_ok=True
        )

    row_count = 1
    first_card = None

    # 既存ファイルがある場合
    if os.path.exists(file_path):
        print('既存CSVを確認中:', file_path)

        try:
            with open(
                file_path,
                'r',
                newline='',
                encoding='utf-8'
            ) as file:
                matrix = list(
                    csv.reader(file)
                )

            # ヘッダーを除いたカード枚数
            row_count = max(
                1,
                len(matrix) - 1
            )

            # データ行がある場合
            if len(matrix) > 1 and len(matrix[1]) > 1:
                first_card = matrix[1][1]

                if IsLatestData(
                    driver,
                    first_card,
                    row_count
                ):
                    print('データは最新です:')
                    print(file_path)
                    return

                print('データが古いため更新します')
                row_count = 1

        except Exception as error:
            print('既存CSVの確認に失敗しました:')
            print(error)
            print('新規作成として処理します')
            row_count = 1

    print('CSV作成中:')
    print(file_path)

    # wモードでCSVを作成・上書き
    with open(
        file_path,
        'w',
        newline='',
        encoding='utf-8'
    ) as file:
        duel_masters_card_box.DuelMastersCardBox(
            driver,
            row_count,
            file
        )

    print('CSV保存完了:')
    print(file_path)


def wait_for_search_complete(driver):
    """
    検索後の読み込み完了を待つ。
    """

    wait = WebDriverWait(
        driver,
        100
    )

    # jQueryを使用しているページ用
    try:
        wait.until(
            lambda current_driver:
            current_driver.execute_script(
                """
                return typeof jQuery === 'undefined'
                    || jQuery.active === 0;
                """
            )
        )
    except Exception as error:
        print('jQueryの待機をスキップしました:', error)

    # HTMLの読み込み完了を待つ
    wait.until(
        lambda current_driver:
        current_driver.execute_script(
            'return document.readyState'
        ) == 'complete'
    )


def main():
    """
    メイン処理。
    """

    global export_path

    LoadEnviormentVariables(
        'enviorment.ini'
    )

    driver = None

    try:
        print('ブラウザーを起動します')

        driver = connect_html.GetDriver(
            'https://dm.takaratomy.co.jp/card/',
            headless_mode
        )

        print('カードページを開きました')

        # 商品選択用selectを取得
        products = driver.find_element(
            By.XPATH,
            '//*[@id="search_cond"]/div[1]/div[2]/select'
        )

        select_products = Select(
            products
        )

        # optionをコピーしておく
        # 検索後にページが更新されるため、
        # 元のリストを直接使い続けない
        options = list(
            select_products.options
        )

        print('商品数:', len(options))

        for option_index, option in enumerate(options, start=1):
            product_id = option.get_attribute(
                'value'
            )

            if not product_id:
                continue

            product_name = option.get_attribute(
                'text'
            )

            product_name = safe_filename(
                product_name
            )

            print()
            print(
                f'[{option_index}/{len(options)}]'
            )
            print('商品ID:', product_id)
            print('商品名:', product_name)

            # 検索条件selectを再取得
            products = driver.find_element(
                By.XPATH,
                '//*[@id="search_cond"]/div[1]/div[2]/select'
            )

            select_products = Select(
                products
            )

            select_products.select_by_value(
                product_id
            )

            # 検索ボタンを取得
            search_button = driver.find_element(
                By.XPATH,
                '//*[@id="search_cond"]/div[3]/input[1]'
            )

            search_button.click()

            # AjaxとHTMLの読み込み完了を待つ
            wait_for_search_complete(
                driver
            )

            # 商品名.csvの保存先を作成
            file_path = os.path.join(
                export_path,
                product_name + '.csv'
            )

            print('作成予定ファイル:')
            print(file_path)

            PageCroll(
                driver,
                file_path
            )

            print(
                product_name + ' complete'
            )

    except Exception as error:
        print()
        print('エラーが発生しました:')
        print(type(error).__name__)
        print(error)
        raise

    finally:
        if driver is not None:
            print('ブラウザーを終了します')

            try:
                connect_html.ReleaseDriver(
                    driver
                )
            except Exception as error:
                print('ブラウザー終了時のエラー:')
                print(error)

    print('全てのプロセスを完了しました')


if __name__ == '__main__':
    main()
