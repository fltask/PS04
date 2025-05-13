import logging
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s %(levelname)s: %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def start_browser(headless: bool = False, timeout: int = 10) -> webdriver.Chrome:
    """Запускает Chrome WebDriver с заданными опциями."""
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(timeout)
    logger.info("Браузер запущен")
    return driver


def search_wikipedia(driver: webdriver.Chrome, query: str, timeout: int = 10) -> None:
    """Осуществляет поиск в Википедии и ждёт результатов."""
    driver.get('https://ru.wikipedia.org')
    wait = WebDriverWait(driver, timeout)
    search_input = wait.until(EC.element_to_be_clickable((By.ID, 'searchInput')))
    search_input.clear()
    search_input.send_keys(query)
    time.sleep(0.5)  # небольшая задержка перед нажатием Enter
    search_input.send_keys(Keys.ENTER)
    logger.info("Поиск по запросу '%s' выполнен", query)
    wait.until(EC.presence_of_element_located((By.ID, 'mw-content-text')))


def get_paragraphs(driver: webdriver.Chrome) -> list[str]:
    """Возвращает непустые параграфы текущей статьи."""
    content = driver.find_element(By.ID, 'mw-content-text')
    paragraphs = content.find_elements(By.TAG_NAME, 'p')
    return [p.text for p in paragraphs if p.text.strip()]


def get_internal_links(driver: webdriver.Chrome, limit: int = 10) -> list[tuple[str, str]]:
    """Возвращает до `limit` уникальных внутренних ссылок."""
    content = driver.find_element(By.ID, 'mw-content-text')
    anchors = content.find_elements(
        By.CSS_SELECTOR,
        'a[href^="/wiki/"]:not([href*=":"])'
    )
    seen = set()
    internal = []
    for a in anchors:
        href = a.get_attribute('href')
        title = a.get_attribute('title') or a.text
        if title and href not in seen:
            seen.add(href)
            internal.append((title, href))
            if len(internal) >= limit:
                break
    return internal


def main():
    # Спрашиваем запрос до запуска браузера, чтобы лог не мешал вводу
    query = input('Запрос для поиска (Enter для выхода): ').strip()
    if not query:
        logger.info("Пустой запрос, выходим.")
        return

    driver = start_browser()
    try:
        search_wikipedia(driver, query)

        while True:
            paras = get_paragraphs(driver)
            links = get_internal_links(driver)

            print('\nВыберите действие:')
            print(' 1 — читать статью построчно')
            print(' 2 — перейти по ссылке')
            print(' 3 — выход')
            choice = input('Ваш выбор: ').strip()

            match choice:
                case '1':
                    # Листаем параграфы по одному
                    for i, p in enumerate(paras, start=1):
                        print(f"\nПараграф {i}:\n{p}\n")
                        cont = input('Показать следующий параграф? (y/n): ').strip().lower()
                        if cont not in {'y', ''}:
                            break

                case '2':
                    print('\nСсылки:')
                    for idx, (title, _) in enumerate(links, 1):
                        print(f" {idx}: {title}")
                    sel = input('Номер или Enter для отмены: ').strip()
                    if sel.isdigit():
                        idx = int(sel) - 1
                        if 0 <= idx < len(links):
                            driver.get(links[idx][1])
                            WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.ID, 'mw-content-text'))
                            )
                        else:
                            logger.error("Индекс вне диапазона")

                case '3':
                    logger.info("Завершение работы по запросу пользователя")
                    break

                case _:
                    logger.warning("Неверный ввод: %r", choice)

    finally:
        driver.quit()
        logger.info("Браузер закрыт")


if __name__ == '__main__':
    main()
