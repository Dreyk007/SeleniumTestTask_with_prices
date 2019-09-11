import argparse
import random
import re
from time import sleep

from selenium import webdriver
from selenium.webdriver.common import keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class new_items(object):
    """Ожидаем прогрузки новых товаров на странице"""

    def __init__(self, new_item_locator, current_items_count):
        self.new_item_locator = new_item_locator
        self.current_items_count = current_items_count

    def __call__(self, driver):
        # Ожидаем пока новые товары загрузятся
        # Проверка путем сравнения со старым количеством товаров на странице
        new_items_count = len(driver.find_elements(*self.new_item_locator))
        if new_items_count > self.current_items_count:
            print(f'Was items on page: {self.current_items_count}')
            print(f'Became items on page: {new_items_count}')
            return True
        else:
            return False


def random_sleep():
    """ Имитируем случайные задержки (на всякий случай) """
    sleep(random.uniform(*RANDOM_SLEEP_RANGE))


def interaction_with(selector, clickable=False, scroll=False, click=False):
    """ Функция взаимодействия с элементомами. Возвращает запрошенные элементы """
    # try:
    # Дожидаемся появления элемента на странице
    elems = WebDriverWait(DRIVER, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector)))

    # Проверяем сколько элементов обнаружено
    if len(elems) > 1:
        # Если найдена группа элементов, то просто возвращаем их
        return elems
    else:
        # Иначе - начинаем взаимодействие
        elem = elems[0]

    if clickable:
        # Дожидаемся кликабельности элемента
        WebDriverWait(DRIVER, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))

    if scroll:
        # Скроллим элемент в пределы видимости:
        elem.location_once_scrolled_into_view

    if click:
        # Нажимаем на элемент
        elem.click()

    return elem

    # except Exception as Error:
    #    print(f"ОШИБКА: {Error}. Повтор...")
    #    return interaction_with(selector, clickable, scroll, click)


def prepare():
    """ Подготавливаем страницу для взаимодействия с ней """
    # Находим поле поиска
    search_field_elem = interaction_with(CSS_SEARCH_FIELD, clickable=True, scroll=True)
    # Вводим искомую фразу
    search_field_elem.send_keys(PHRASE)
    random_sleep()
    # Нажимаем Enter
    search_field_elem.send_keys(keys.Keys.ENTER)
    random_sleep()


def main():
    """ Основная часть скрипта """
    # Прогружаем запрошенное количество страниц
    for page in range(1, PAGES_TO_LOAD + 1):
        # Запоминаем текущее количество товаров на странице
        current_elements_count = len(interaction_with(CSS_ITEMS))
        # Нажимаем на кнопку "More"
        interaction_with(CSS_MORE_BUTTON, clickable=True, scroll=True, click=True)
        # Ожидаем прогрузки новых товаров
        WebDriverWait(DRIVER, 120).until(new_items((By.CSS_SELECTOR, CSS_ITEMS), current_elements_count))
        random_sleep()

    # Сохраняем списки с элементами товаров и цен
    item_elems = interaction_with(CSS_ITEMS)
    price_elems = interaction_with(CSS_PRICE)

    # Добываем текст и цены из элементов
    item_names = [elem.text for elem in item_elems]
    item_prices = [int(re.sub(r'\D', '', price.get_attribute('innerHTML'))) for price in price_elems]

    # Из общего списка товаров подсчитываем, забираем и обрабатываем только подходящие
    word_count = 0
    trademarks = []
    prices = []
    for i, name in enumerate(item_names):
        # Получаем название бренда из имени товара
        trademark = re.findall(MANUFACTURER_PATTERN, name)

        if PHRASE_FOR_COUNT in name:
            word_count += 1

        # Сохраняем бренды и их цены в отдельные списки
        if trademark:
            trademarks.append(trademark[0])
            prices.append(item_prices[i])

    # Объединяем цены с брендами
    trademarks_with_prices = tuple(zip(trademarks, prices))

    # Получаем итоговый список из объектов брендов
    trademarks_dicts = []
    for trademark in sorted(set(trademarks)):
        # Находим цены для позиций текущего бренда
        prices = [price for _trademark, price in trademarks_with_prices if _trademark == trademark]

        trademark_dict = {'Name': trademark,
                          'count_on_pages': trademarks.count(trademark),
                          'min_price': min(prices),
                          'max_price': max(prices)}

        trademarks_dicts.append(trademark_dict)

    # Выводим результаты на экран
    print(f'\nResults with word "{PHRASE_FOR_COUNT}": {word_count}')
    print(f'\nTV by trademark on first {PAGES_TO_LOAD + 1} pages:')
    for trademark in trademarks_dicts:
        print(f"{trademark['Name']}: {trademark['count_on_pages']}")
        if trademark['count_on_pages'] > 1:
            print(f"Minimal price = {trademark['min_price']}\n"
                  f"Maximal price = {trademark['max_price']}\n"
                  f"{'-' * 6}")
        else:
            print(f"Price = {trademark['min_price']}\n"
                  f"{'-' * 6}")


if __name__ == '__main__':
    # Парсим аргументы
    parser = argparse.ArgumentParser(description='Show trademarks from website.')
    parser.add_argument('pages_to_load', metavar='p', type=int, help='Pages to load')
    args = parser.parse_args()

    # Задаём параметры работы скрипта
    DRIVER = webdriver.Chrome()
    URL = 'https://rozetka.com.ua/'
    CSS_SEARCH_FIELD = 'input.search-form__input'
    CSS_ITEMS = 'div.g-i-tile-i-title > a'
    CSS_MORE_BUTTON = 'a.g-i-more-link'
    CSS_PRICE = 'div.g-price-uah > span:first-child'

    MANUFACTURER_PATTERN = re.compile(r'^Телевизор ([\w\.-]+) [\w\.\s-]+')
    RANDOM_SLEEP_RANGE = (0.1, 1.6)
    PHRASE = 'Телевизор 26'
    PHRASE_FOR_COUNT = 'Телевизор'
    PAGES_TO_LOAD = args.pages_to_load

    # Запуск
    DRIVER.get(URL)
    prepare()
    main()

    # Завершение
    DRIVER.quit()
