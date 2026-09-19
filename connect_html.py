# HTMLアクセスの汎用メソッド群

from urllib import request
from urllib.error import URLError, HTTPError

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.common.exceptions import WebDriverException

from webdriver_manager.chrome import ChromeDriverManager


def GetDriver(url, headless=True):
    """
    Chromeを起動して指定URLを開く。
    """

    options = Options()

    if headless:
        options.add_argument('--headless=new')

    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--lang=ja-JP')

    # webdriver-managerでChromeDriverを準備
    service = ChromeService(
        ChromeDriverManager().install()
    )

    try:
        driver = webdriver.Chrome(
            service=service,
            options=options
        )

        driver.set_page_load_timeout(120)
        driver.get(url)

        return driver

    except Exception:
        # 起動に失敗した場合、取得したドライバーを
        # 残したままにしないための処理
        raise


def GetBeautifulSoupFromDriver(driver):
    """
    Seleniumで表示中のページHTMLを
    BeautifulSoupで扱える形式に変換する。
    """

    html = driver.page_source

    return BeautifulSoup(
        html,
        'html.parser'
    )


def ReleaseDriver(driver):
    """
    Seleniumのブラウザーを安全に終了する。
    """

    if driver is None:
        return

    try:
        driver.quit()
    except Exception:
        pass


def GetBeautifulSoupFromHTML(url):
    """
    Seleniumを使わず、URLからHTMLを取得する。
    """

    try:
        with request.urlopen(
            url,
            timeout=120
        ) as response:
            html = response.read()

        return BeautifulSoup(
            html,
            'html.parser'
        )

    except HTTPError as error:
        print('HTTPエラー:', error.code)
        raise

    except URLError as error:
        print('URL接続エラー:', error.reason)
        raise
