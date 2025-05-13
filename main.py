import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


# Функция для запуска браузера
def start_browser():
    # Используем Chrome WebDriver; убедитесь, что chromedriver в PATH
    options = webdriver.ChromeOptions()
    #    options.add_argument('--headless')  # без окна браузера
    options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(5)
    return driver


# Функция поиска и перехода по запросу
def search_wikipedia(driver, query):
    driver.get('https://ru.wikipedia.org')
    search_input = driver.find_element(By.ID, 'searchInput')
    search_input.clear()
    search_input.send_keys(query)
    time.sleep(1)
    search_input.send_keys(Keys.ENTER)
    time.sleep(1)


# Получение списка параграфов статьи
def get_paragraphs(driver):
    content = driver.find_element(By.ID, 'mw-content-text')
    # Находим все теги p внутри основного контента
    paragraphs = content.find_elements(By.TAG_NAME, 'p')
    # Фильтруем пустые или короткие
    return [p.text for p in paragraphs if p.text.strip()]


# Получение списка внутренних ссылок статьи
def get_internal_links(driver):
    content = driver.find_element(By.ID, 'mw-content-text')
    # CSS: href начинается с "/wiki/" и в нём нет ":"
    anchors = content.find_elements(By.CSS_SELECTOR, 'a[href^="/wiki/"]:not([href*=":"])')
    seen = set()
    internal = []
    for a in anchors:
        href = a.get_attribute('href')
        title = a.get_attribute('title') or a.text
        if title and href not in seen:
            seen.add(href)
            internal.append((title, href))
    return internal

# Главная логика программы
def main():
    driver = start_browser()
    try:
        query = input('Введите запрос для поиска в Википедии: ')
        search_wikipedia(driver, query)

        while True:
            paragraphs = get_paragraphs(driver)
            links = get_internal_links(driver)

            print('\nЧто вы хотите сделать дальше?')
            print('1. Листать параграфы текущей статьи')
            print('2. Перейти на одну из связанных страниц')
            print('3. Выйти из программы')
            choice = input('Ваш выбор (1/2/3): ')

            match choice:
                case '1':
                    # Листаем параграфы по одному
                    for i, p in enumerate(paragraphs, start=1):
                        print(f"\nПараграф {i}:\n{p}\n")
                        cont = input('Показать следующий параграф? (y/n): ').strip().lower()
                        if cont not in {'y', ''}:
                            break
                case '2':
                    # Показать список ссылок и перейти
                    print('\nДоступные связанные страницы:')
                    for idx, (title, href) in enumerate(links[:10], start=1):
                        print(f"{idx}. {title}")
                    sel = input('Введите номер страницы или отмена (c): ')
                    if sel.lower() == 'c':
                        continue
                    try:
                        sel_i = int(sel) - 1
                        if 0 <= sel_i < len(links[:10]):
                            _, href = links[sel_i]
                            driver.get(href)
                            time.sleep(1)
                            continue
                        else:
                            print('Неверный номер')
                    except ValueError:
                        print('Нужно ввести число')
                case '3':
                    print('Выход из программы.')
                    break
                case _:
                    print('Неверный выбор, попробуйте снова.')
    finally:
        driver.quit()


if __name__ == '__main__':
    main()
