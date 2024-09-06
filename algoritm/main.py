from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import requests
import pandas as pd
import re
import time
import json
import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__)



def get_element_styles(driver, element):
    script = "var s = ''; var o = getComputedStyle(arguments[0]); for(var i = 0; i < o.length; i++){s+=o[i] + ':' + o.getPropertyValue(o[i])+';';} return s;"
    styles = driver.execute_script(script, element)
    return styles


# In[288]:

results = []

def check_keyboard_navigation(driver):
    tags = ['a', 'button', 'input', 'select', 'textarea']
    recommendations = []
    try:
        elements = []
        for tag in tags:
            elements.extend(driver.find_elements(By.TAG_NAME, tag))
        
        elements.extend(driver.find_elements(By.CSS_SELECTOR, '[tabindex]'))

        if not elements:
            return 0
        
        working_elements = 0
        for i in range(len(elements)):
            driver.switch_to.active_element.send_keys(Keys.TAB)
            focused_element = driver.switch_to.active_element
            if focused_element == elements[i] and focused_element.is_displayed():
                working_elements += 1
            else:
                outer_html = i.get_attribute('outerHTML')
                correct_html = re.sub(r'tabindex="[^"]*"', 'tabindex="0"', outer_html) if 'tabindex' in outer_html else outer_html.replace('<', '<span tabindex="0">')
                recommendations.append({
                    'html': outer_html,
                    'recom': 'Элемент не доступен для клавиатурной навигации. Добавьте атрибуты tabindex. Пример исправленного кода:\n' + correct_html
                })

        return 1 if working_elements > 0 else 0, recommendations
    except Exception as e:
        print(f"Ошибка в check_keyboard_navigation: {e}")
        return 0


# In[303]:


def check_screen_reader_labels(driver):
    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        all_elements = soup.find_all(['button', 'a', 'input', 'div', 'span', 'img', 'label', 'section', 'article'])
        correctly_labeled = sum(1 for elem in all_elements if elem.get('aria-label') 
                                or elem.get('role') 
                                or elem.name == 'img' and elem.get('alt') 
                                or elem.name == 'input' and elem.get('aria-labelledby'))
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

        if not all_elements:
            return 0

        return 1 if len(all_elements) > 0 else 0, recommendations
    except Exception as e:
        print(f"Ошибка в check_screen_reader_labels: {e}")
        return 0


# In[327]:


def check_accessible_captcha(driver):
    try:
        html_code = driver.page_source
        soup = BeautifulSoup(html_code, 'html.parser')
        captcha_elements = soup.find_all(string=re.compile(r'captcha', re.IGNORECASE))
        recommendations = []
        
        if not captcha_elements:
            correct_html = '<div aria-label="captcha challenge">\n  <audio controls>\n    <source src="audio_captcha.mp3" type="audio/mpeg">\n  </audio>\n</div>'
            recommendations.append({
                'html': html_code,
                'recom': 'Капча недоступна для пользователей с ограниченными возможностями. Добавьте аудиовариант или альтернативный текст. Пример исправленного кода:\n' + correct_html
            })
        
        accessible_keywords = re.compile(r'(audio|alt|accessible|text)', re.IGNORECASE)
        has_accessible_captcha = any(accessible_keywords.search(element) for element in captcha_elements)
        
        return 1 if has_accessible_captcha else 0, recommendations
    except Exception as e:
        print(f"Ошибка в check_accessible_captcha: {e}")
        return 0


# In[342]:


def check_headings_and_links(driver):
    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        headings = soup.find_all(re.compile('^h[1-6]$'))
        
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
        
        return 1 if headings and valid_links > 0 else 0, recommendations
    
    except Exception as e:
        print(f"Ошибка в check_headings_and_links: {e}")
        return 0


def check_scalability(driver):
    try:
        original_size = driver.get_window_size()
        
        test_sizes = [(320, 480), (768, 1024)]
        results = []
        
        for width, height in test_sizes:
            driver.set_window_size(width, height)
            time.sleep(2)
            
            body = driver.find_element(By.TAG_NAME, 'body')
            if body.size['width'] == width:
                results.append(100)
            else:
                results.append(0)
        
        driver.set_window_size(original_size['width'], original_size['height'])

        recommendations = []
        if body.size['width'] != 320:
            correct_html = '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
            recommendations.append({
                'html': body.get_attribute('outerHTML'),
                'recom': 'Страница не масштабируется до размеров мобильного экрана. Добавьте тег viewport для улучшения масштабирования. Пример исправленного кода:\n' + correct_html
            })
        return 1 if body.size['width'] == 320 else 0, recommendations
    
    except Exception as e:
        print(f"Ошибка в check_scalability: {e}")
        return 0



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


options = webdriver.ChromeOptions()
options.page_load_strategy = 'none'
options.add_argument("--headless")


def proc(url):
    successful_sites = []
    failed_sites = []

    driver = webdriver.Chrome(options=options)
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    print(f"Проверка сайта: {url}")
    try:
        driver.set_page_load_timeout(10)
        start_time = time.time()
        driver.get(url)
        load_time = time.time() - start_time
        
        if load_time > 10:
            print(f"Сайт {url} не загрузился за 10 секунд")
            failed_sites.append(url)
            
        time.sleep(3)

        keyboard_score, keyboard_recom = check_keyboard_navigation(driver)
        screen_reader_score, screen_reader_recom = check_screen_reader_labels(driver)
        captcha_score, captcha_recom = check_accessible_captcha(driver)
        headings_links_score, headings_links_recom = check_headings_and_links(driver)
        # contrast_score, contrast_recom = check_contrast(driver)
        scalability_score, scalability_recom = check_scalability(driver)
        alt_text_score, alt_text_recom = check_image_alt_text(driver)

        total_score = ((keyboard_score + screen_reader_score + captcha_score + headings_links_score + scalability_score + alt_text_score) / 6)

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
            'contrast': 0,
            'contrast_recom': [],
            'scalability': scalability_score,
            'scalability_recom': scalability_recom,
            'alt_text': alt_text_score,
            'alt_text_recom': alt_text_recom
        }
        results.append(new_entry)
        
    except Exception as e:
        print(f"Ошибка при проверке сайта {url}: {e}")
        failed_sites.append(url)
    
    driver.quit()

    return results




@app.route('/check_sites', methods=['POST'])
def check_sites():
    data = request.json
    urls = data.get('urls', [])
    results = []

    for url in urls:
        try:
            results.append(proc(url))

        except Exception as e:
            print(f"Ошибка при проверке сайта {url}: {e}")

    return jsonify(results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

