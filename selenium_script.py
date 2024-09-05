from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import pandas as pd
import os
import time
import re

options = webdriver.ChromeOptions()
options.page_load_strategy = 'none'
driver = webdriver.Chrome(options=options)

df = pd.read_excel("C:/Users/l3wyw/OneDrive/Документы/CODS/case2/final_sites.xlsx")
df.drop('score', axis=1, inplace=True, errors='ignore')

successful_sites = []
failed_sites = []

results_df = pd.DataFrame(columns=['URL', 'Полная функциональность с клавиатуры', 
                                   'Читаемость и управляемость для скринридеров', 
                                   'Доступная капча', 'Описание заголовков и ссылок', 
                                   'Контрастность', 'Масштабируемость', 
                                   'Альтернативный текст для изображений', 'Общий счет', 'HTML Code'])

def save_html_code(html_code, url, folder='saved_html'):
    if not os.path.exists(folder):
        os.makedirs(folder)
    file_name = re.sub(r'[^\w\s]', '_', url) + '.html'
    file_path = os.path.join(folder, file_name)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_code)

def get_color_contrast(color1, color2):
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def luminance(rgb):
        r, g, b = [x/255.0 for x in rgb]
        r = r/12.92 if r <= 0.03928 else ((r + 0.055)/1.055)**2.4
        g = g/12.92 if g <= 0.03928 else ((g + 0.055)/1.055)**2.4
        b = b/12.92 if b <= 0.03928 else ((b + 0.055)/1.055)**2.4
        return 0.2126*r + 0.7152*g + 0.0722*b
    
    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)
    
    lum1 = luminance(rgb1)
    lum2 = luminance(rgb2)
    
    contrast_ratio = (max(lum1, lum2) + 0.05) / (min(lum1, lum2) + 0.05)
    return contrast_ratio

def check_keyboard_navigation():
    try:
        all_focusable_elements = driver.find_elements(By.CSS_SELECTOR, 'a, button, input, select, textarea, [tabindex]')
        working_elements = 0
        for elem in all_focusable_elements:
            elem.send_keys(Keys.TAB)
            focused_element = driver.switch_to.active_element
            if focused_element == elem and elem.is_displayed():
                working_elements += 1
        if not all_focusable_elements:
            return 100
        return int((working_elements / len(all_focusable_elements)) * 100)
    except Exception as e:
        print(f"Ошибка в check_keyboard_navigation: {e}")
        return 0

def check_screen_reader_labels():
    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        all_elements = soup.find_all(['button', 'a', 'input', 'div', 'span'])
        correctly_labeled = sum(1 for elem in all_elements if elem.get('aria-label') or elem.get('role'))
        if not all_elements:
            return 100
        return int((correctly_labeled / len(all_elements)) * 100)
    except Exception as e:
        print(f"Ошибка в check_screen_reader_labels: {e}")
        return 0

def check_accessible_captcha(html_code):
    try:
        has_accessible_captcha = bool(re.search(r'(captcha.*audio|captcha.*alt|captcha.*accessible)', html_code, re.IGNORECASE))
        return 100 if has_accessible_captcha else 0
    except Exception as e:
        print(f"Ошибка в check_accessible_captcha: {e}")
        return 0

def check_headings_and_links():
    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        h1 = soup.find_all(re.compile('^h[1-6]$'))
        all_links = soup.find_all('a')
        valid_links = sum(1 for link in all_links if link.text.strip() or link.get('aria-label'))
        if not all_links:
            return 100 if h1 else 0
        return int(((len(h1) + valid_links) / (1 + len(all_links))) * 100)
    except Exception as e:
        print(f"Ошибка в check_headings_and_links: {e}")
        return 0

def check_contrast():
    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        text_elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        contrast_scores = []
        for elem in text_elements:
            style = elem.get('style', '')
            text_color = re.search(r'color:\s*(#[0-9a-fA-F]{6}|[a-zA-Z]+)', style)
            background_color = re.search(r'background-color:\s*(#[0-9a-fA-F]{6}|[a-zA-Z]+)', style)
            if text_color and background_color:
                contrast_scores.append(get_color_contrast(text_color.group(1), background_color.group(1)))
        if not contrast_scores:
            return 100
        min_ratio = min(contrast_scores)
        if min_ratio >= 7:
            return 100
        elif min_ratio >= 4.5:
            return 50
        return 0
    except Exception as e:
        print(f"Ошибка в check_contrast: {e}")
        return 0

def check_scalability():
    try:
        original_size = driver.get_window_size()
        driver.set_window_size(320, 480)
        time.sleep(1)
        body = driver.find_element(By.TAG_NAME, 'body')
        driver.set_window_size(original_size['width'], original_size['height'])
        return 100 if body.size['width'] == 320 else 0
    except Exception as e:
        print(f"Ошибка в check_scalability: {e}")
        return 0

def check_image_alt_text():
    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        images = soup.find_all('img')
        if not images:
            return 100
        valid_alts = sum(1 for img in images if img.get('alt'))
        return int((valid_alts / len(images)) * 100)
    except Exception as e:
        print(f"Ошибка в check_image_alt_text: {e}")
        return 0

for index, row in df.iterrows():
    url = row['url']
    print(f"Проверка сайта: {url}")
    try:
        driver.set_page_load_timeout(10)
        start_time = time.time()
        driver.get(url)
        load_time = time.time() - start_time
        
        if load_time > 10:
            print(f"Сайт {url} не загрузился за 10 секунд")
            failed_sites.append(url)
            continue
        
        html_code = driver.page_source
        save_html_code(html_code, url)

        keyboard_score = check_keyboard_navigation()
        screen_reader_score = check_screen_reader_labels()
        captcha_score = check_accessible_captcha(html_code)
        headings_links_score = check_headings_and_links()
        contrast_score = check_contrast()
        scalability_score = check_scalability()
        alt_text_score = check_image_alt_text()

        total_score = (keyboard_score + screen_reader_score + captcha_score + 
                      headings_links_score + contrast_score + scalability_score + 
                      alt_text_score) / 7

        new_row = pd.DataFrame({
            'URL': [url],
            'Полная функциональность с клавиатуры': [keyboard_score],
            'Читаемость и управляемость для скринридеров': [screen_reader_score],
            'Доступная капча': [captcha_score],
            'Описание заголовков и ссылок': [headings_links_score],
            'Контрастность': [contrast_score],
            'Масштабируемость': [scalability_score],
            'Альтернативный текст для изображений': [alt_text_score],
            'Общий счет': [total_score],
            'HTML Code': [html_code]
        })
        results_df = pd.concat([results_df, new_row], ignore_index=True)
        successful_sites.append(url)
        
    except Exception as e:
        print(f"Ошибка при проверке сайта {url}: {e}")
        failed_sites.append(url)

results_df.to_excel("C:/Users/l3wyw/OneDrive/Документы/CODS/case2/check_results.xlsx", index=False)
failed_df = pd.DataFrame(failed_sites, columns=['url'])
failed_df.to_excel("C:/Users/l3wyw/OneDrive/Документы/CODS/case2/failed_sites.xlsx", index=False)

print(f"Проверку прошли: {len(successful_sites)}/{len(df)} сайтов")
driver.quit()
