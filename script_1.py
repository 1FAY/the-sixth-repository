from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import requests
import re
import pandas as pd
import time
import json
import warnings
warnings.filterwarnings('ignore')

options = webdriver.ChromeOptions()
options.page_load_strategy = 'none'

df = pd.read_excel("C:/Users/l3wyw/OneDrive/Документы/CODS/case2/final_sites.xlsx")
df.drop('score', axis=1, inplace=True, errors='ignore')

results = []

successful_sites = []
failed_sites = []

def init_driver():
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(10)
    return driver

def quit_driver(driver):
    if driver:
        driver.quit()

def check_keyboard_navigation(driver):
    try:
        all_focusable_elements = driver.find_elements(By.CSS_SELECTOR, 'a, button, input, select, textarea, [tabindex]')
        working_elements = 0
        recommendations = []
        for elem in all_focusable_elements:
            elem.send_keys(Keys.TAB)
            focused_element = driver.switch_to.active_element
            if focused_element == elem and elem.is_displayed():
                working_elements += 1
            else:
                outer_html = elem.get_attribute('outerHTML')
                correct_html = re.sub(r'tabindex="[^"]*"', 'tabindex="0"', outer_html) if 'tabindex' in outer_html else outer_html.replace('<', '<span tabindex="0">')
                recommendations.append({
                    'html': outer_html,
                    'recom': 'Элемент не доступен для клавиатурной навигации. Добавьте атрибуты tabindex. Пример исправленного кода:\n' + correct_html
                })
        print(f"-- Keyboard Navigation: {working_elements}/{len(all_focusable_elements)}")
        return 1 if len(all_focusable_elements) > 0 else 0, recommendations
    except Exception as e:
        print(f"Ошибка при проверке навигации с клавиатуры: {e}")
        return 0, []

def check_screen_reader_labels(driver):
    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        all_elements = soup.find_all(['button', 'a', 'input', 'div', 'span'])
        correctly_labeled = sum(1 for elem in all_elements if elem.get('aria-label') or elem.get('role'))
        recommendations = []
        for elem in all_elements:
            if not (elem.get('aria-label') or elem.get('role')):
                outer_html = str(elem)
                if 'button' in outer_html or 'a' in outer_html:
                    correct_html = re.sub(r'<([a-zA-Z]+)', r'<\1 aria-label="Описание действия"', outer_html)
                else:
                    correct_html = re.sub(r'<([a-zA-Z]+)', r'<\1 role="presentation"', outer_html)
                recommendations.append({
                    'html': outer_html,
                    'recom': 'Элемент не имеет aria-label или role. Добавьте aria-label или role. Пример исправленного кода:\n' + correct_html
                })
        print(f"-- Screen Reader Labels: {correctly_labeled}/{len(all_elements)}")
        return 1 if len(all_elements) > 0 else 0, recommendations
    except Exception as e:
        print(f"Ошибка при проверке скринридеров: {e}")
        return 0, []

def check_accessible_captcha(html_code):
    try:
        has_accessible_captcha = bool(re.search(r'(captcha.*audio|captcha.*alt|captcha.*accessible)', html_code, re.IGNORECASE))
        recommendations = []
        if not has_accessible_captcha:
            correct_html = '<div aria-label="captcha challenge">\n  <audio controls>\n    <source src="audio_captcha.mp3" type="audio/mpeg">\n  </audio>\n</div>'
            recommendations.append({
                'html': html_code,
                'recom': 'Капча недоступна для пользователей с ограниченными возможностями. Добавьте аудиовариант или альтернативный текст. Пример исправленного кода:\n' + correct_html
            })
        print(f"-- Accessible Captcha: {has_accessible_captcha}")
        return 1 if has_accessible_captcha else 0, recommendations
    except Exception as e:
        print(f"Ошибка при проверке капчи: {e}")
        return 0, []

def check_headings_and_links(driver):
    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        h1 = soup.find_all(re.compile('^h[1-6]$'))
        all_links = soup.find_all('a')
        valid_links = sum(1 for link in all_links if link.text.strip() or link.get('aria-label'))
        recommendations = []
        for link in all_links:
            if not (link.text.strip() or link.get('aria-label')):
                outer_html = str(link)
                correct_html = re.sub(r'<a ', '<a aria-label="Описание ссылки" ', outer_html)
                recommendations.append({
                    'html': outer_html,
                    'recom': 'Ссылка не содержит текст или aria-label. Пример исправленного кода:\n' + correct_html
                })
        print(f"-- Valid Headings Links: {valid_links}/{len(all_links)}")
        return 1 if h1 and valid_links > 0 else 0, recommendations
    except Exception as e:
        print(f"Ошибка при проверке заголовков и ссылок: {e}")
        return 0, []

def check_contrast(driver):
    def get_color_contrast(foreground, background):
        try:
            response = requests.get(f"https://webaim.org/resources/contrastchecker/?fcolor={foreground}&bcolor={background}&api")
            contrast_data = response.json()
            return float(contrast_data['ratio'])
        except Exception as e:
            print(f"Ошибка при запросе контрастности: {e}")
            return None

    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        text_elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        contrast_scores = []
        recommendations = []
        for elem in text_elements:
            style = elem.get('style', '')
            text_color_match = re.search(r'color:\s*(#[0-9a-fA-F]{6}|[a-zA-Z]+)', style)
            background_color_match = re.search(r'background-color:\s*(#[0-9a-fA-F]{6}|[a-zA-Z]+)', style)

            if text_color_match and background_color_match:
                text_color = text_color_match.group(1)
                background_color = background_color_match.group(1)
                contrast_result = get_color_contrast(text_color, background_color)
                if contrast_result and contrast_result < 4.5:
                    correct_html = re.sub(r'color:[^;]+', 'color: #000000', style)
                    correct_html = re.sub(r'background-color:[^;]+', 'background-color: #FFFFFF', correct_html)
                    recommendations.append({
                        'html': str(elem),
                        'recom': f'Контраст текста ({contrast_result}) ниже 4.5. Пример исправленного кода:\n' + correct_html
                    })
        min_ratio = min(contrast_scores) if contrast_scores else 0
        if contrast_scores:
            min_ratio = min(contrast_scores)
            print(f"-- Min Contrast Ratio: {min_ratio}")
            return 1 if min_ratio >= 4.5 else 0, recommendations
        else:
            return 0, []
    except Exception as e:
        print(f"Ошибка при проверке контраста: {e}")
        return 0, []

def check_scalability(driver):
    try:
        driver.set_window_size(320, 480)
        body = driver.find_element(By.TAG_NAME, 'body')
        recommendations = []
        if body.size['width'] != 320:
            correct_html = '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
            recommendations.append({
                'html': body.get_attribute('outerHTML'),
                'recom': 'Страница не масштабируется до размеров мобильного экрана. Добавьте тег viewport для улучшения масштабирования. Пример исправленного кода:\n' + correct_html
            })
        return 1 if body.size['width'] == 320 else 0, recommendations
    except Exception as e:
        print(f"Ошибка при проверке масштабируемости: {e}")
        return 0, []

def check_image_alt_text(driver):
    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        images = soup.find_all('img')
        recommendations = []
        for img in images:
            if not img.get('alt'):
                outer_html = str(img)
                correct_html = re.sub(r'<img ', '<img alt="Описание изображения" ', outer_html)
                recommendations.append({
                    'html': outer_html,
                    'recom': 'Изображение не имеет alt-текста. Добавьте alt-тег. Пример исправленного кода:\n' + correct_html
                })
        valid_alts = sum(1 for img in images if img.get('alt'))
        print(f"-- Valid Alt Text: {valid_alts}/{len(images)}")
        return 1 if valid_alts == len(images) else 0, recommendations
    except Exception as e:
        print(f"Ошибка при проверке alt-текста: {e}")
        return 0, []

def process_site(url):
    try:
        driver = init_driver()
        driver.get(url)
        html_code = driver.page_source
        time.sleep(2)
        keyboard_score, keyboard_recom = check_keyboard_navigation(driver)
        time.sleep(2)
        screen_reader_score, screen_reader_recom = check_screen_reader_labels(driver)
        time.sleep(2)
        captcha_score, captcha_recom = check_accessible_captcha(html_code)
        time.sleep(2)
        headings_links_score, headings_links_recom = check_headings_and_links(driver)
        time.sleep(2)
        contrast_score, contrast_recom = check_contrast(driver)
        time.sleep(2)
        scalability_score, scalability_recom = check_scalability(driver)
        time.sleep(2)
        alt_text_score, alt_text_recom = check_image_alt_text(driver)
        time.sleep(2)

        total_score = (keyboard_score + screen_reader_score + captcha_score +
                       headings_links_score + contrast_score + scalability_score +
                       alt_text_score) / 7

        new_entry = {
            'url': url,
            'total_score': total_score,
            'keyboard_functionality': keyboard_score,
            'keyboard_functionality_recom': keyboard_recom,
            'screen_reader_accessibility': screen_reader_score,
            'screen_reader_accessibility_recom': screen_reader_recom,
            'captcha_accessibility': captcha_score,
            'captcha_accessibility_recom': captcha_recom,
            'headings_links_description': headings_links_score,
            'headings_links_description_recom': headings_links_recom,
            'contrast': contrast_score,
            'contrast_recom': contrast_recom,
            'scalability': scalability_score,
            'scalability_recom': scalability_recom,
            'alt_text': alt_text_score,
            'alt_text_recom': alt_text_recom
        }
        results.append(new_entry)
        successful_sites.append(url)

    except Exception as e:
        print(f"Ошибка при проверке сайта {url}: {e}")
        failed_sites.append(url)

    finally:
        quit_driver(driver)

url = input("Введите URL сайта: ")
print(f"Проверка сайта: {url}")
process_site(url)

with open("check_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=4)

failed_df = pd.DataFrame(failed_sites, columns=['url'])
failed_df.to_excel("failed_sites.xlsx", index=False)

print(f"Проверку прошли: {len(successful_sites)}/{len(df)} сайтов")
