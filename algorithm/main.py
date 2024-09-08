from flask import Flask, request, jsonify
from flask_cors import CORS
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from tqdm import tqdm
import re
import time

app = Flask(__name__)
CORS(app)
options = webdriver.ChromeOptions()
options.page_load_strategy = 'none'
options.add_argument('--no-sandbox')
options.add_argument('--disable-gpu')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--headless')
options.add_argument('--start-maximized')

stages = [
    "check_keyboard_navigation",
    "check_screen_reader_labels",
    "check_accessible_captcha",
    "check_headings_and_links",
    "check_scalability",
    "check_image_alt_text"
]



def get_element_styles(driver, element):
    script = "var s = ''; var o = getComputedStyle(arguments[0]); for(var i = 0; i < o.length; i++){s+=o[i] + ':' + o.getPropertyValue(o[i])+';';} return s;"
    styles = driver.execute_script(script, element)
    return styles


def check_keyboard_navigation(driver):
    tags = ['a', 'button', 'input', 'select', 'textarea']
    recommendations = []

    try:
        elements = [element for tag in tags for element in driver.find_elements(By.TAG_NAME, tag)]
        elements.extend(driver.find_elements(By.CSS_SELECTOR, '[tabindex]'))

        if not elements:
            return 1, recommendations
        
        working_elements = 0
        for element in elements:
            driver.execute_script("arguments[0].focus();", element)
            driver.switch_to.active_element.send_keys(Keys.TAB)

            focused_element = driver.switch_to.active_element
            if focused_element == element and focused_element.is_displayed():
                working_elements += 1
            else:
                outer_html = str(element)
                recommendations.append({
                    'html': outer_html,
                    'recom': 'Элемент не доступен для клавиатурной навигации. Добавьте атрибуты tabindex.'
                })

        return 1 if working_elements > 0 else 0, recommendations
    except Exception as e:
        print(f"Ошибка в check_keyboard_navigation: {e}")
        return 0, recommendations


def check_screen_reader_labels(driver):
    tags = ['button', 'a', 'input', 'div', 'span', 'img', 'label', 'section', 'article']
    recommendations = []

    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        elements = soup.find_all(tags)
        
        if not elements:
            return 1, recommendations

        correctly_labeled = sum(1 for elem in elements if elem.get('aria-label') 
                                or elem.get('role') 
                                or elem.name == 'img' and elem.get('alt') 
                                or elem.name == 'input' and elem.get('aria-labelledby'))

        for element in elements:
            if not (element.get('aria-label') or element.get('role')):
                outer_html = str(element)
                recommendations.append({
                    'html': outer_html,
                    'recom': 'Элемент не имеет aria-label или role. Добавьте aria-label или role.'
                })

        return 1 if correctly_labeled > 0 else 0, recommendations
    except Exception as e:
        print(f"Ошибка в check_screen_reader_labels: {e}")
        return 0, recommendations


def check_accessible_captcha(driver):
    recommendations = []

    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        captcha_elements = soup.find_all(string=re.compile(r'captcha', re.IGNORECASE))

        if not captcha_elements:
            return 1, recommendations
        
        has_accessible_captcha = any(re.search(r'(audio|alt|accessible|text)', captcha_element, re.IGNORECASE) for captcha_element in captcha_elements)
        if not captcha_elements or not has_accessible_captcha:
                recommendations.append({
                    'html': soup.prettify(),
                    'recom': 'Капча недоступна для пользователей с ограниченными возможностями. Добавьте аудиовариант или альтернативный текст.'
                })

        return 1 if has_accessible_captcha else 0, recommendations
    except Exception as e:
        print(f"Ошибка в check_accessible_captcha: {e}")
        return 0, recommendations


def check_headings_and_links(driver):
    recommendations = []

    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        headings = soup.find_all(re.compile('^h[1-6]$'))
        all_links = soup.find_all('a')

        if not all_links and not headings:
            return 1, recommendations
        
        valid_links_count = 0
        for link in all_links:
            if not (link.text.strip() or link.get('aria-label')):
                outer_html = str(link)
                recommendations.append({
                    'html': outer_html,
                    'recom': 'Ссылка не содержит текст или aria-label.'
                })
            else:
                valid_links_count += 1
        
        return valid_links_count / len(all_links)
    
    except Exception as e:
        print(f"Ошибка в check_headings_and_links: {e}")
        return 0, recommendations


def check_scalability(driver):
    test_sizes = [(320, 480), (768, 1024)]
    recommendations = []

    try:
        original_size = driver.get_window_size()
        results = []

        for width, height in test_sizes:
            driver.set_window_size(width, height)
            time.sleep(1)
            
            body = driver.find_element(By.TAG_NAME, 'body')
            body_width = body.size['width']
            
            if body_width == width:
                results.append(1)
            else:
                results.append(0)
                if width == 320:
                    recommendations.append({
                        'html': driver.page_source,
                        'recom': 'Страница не масштабируется до размеров мобильного экрана. Добавьте тег viewport для улучшения масштабирования.'
                    })

        driver.set_window_size(original_size['width'], original_size['height'])

        return 1 if sum(results)/len(results) == 1 else sum(results)/len(results), recommendations
    
    except Exception as e:
        print(f"Ошибка в check_scalability: {e}")
        return 0, recommendations


def check_image_alt_text(driver):
    recommendations = []

    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        images = soup.find_all('img')

        if not images:
            return 1, recommendations
        
        for img in images:
            if not img.get('alt'):
                outer_html = str(img)
                recommendations.append({
                    'html': outer_html,
                    'recom': 'Изображение не имеет alt-текста. Добавьте alt-тег.'
                })

        valid_alts = sum(1 for img in images if img.get('alt'))
        return 1 if valid_alts == len(images) else 0, recommendations
    except Exception as e:
        print(f"Ошибка при проверке alt-текста: {e}")
        return 0, recommendations


def proc(url):
    driver = webdriver.Chrome(options=options)

    print(f"Проверка сайта: {url}")
    try:
        driver.set_page_load_timeout(10)
        start_time = time.time()
        driver.get(url)
        load_time = time.time() - start_time
        
        if load_time > 10:
            print(f"Сайт {url} не загрузился за 10 секунд")
            
        time.sleep(1)

        results = {}
        with tqdm(total=len(stages), desc="Прогресс проверки") as pbar:
            for stage in stages:
                if stage == "check_keyboard_navigation":
                    results['keyboard_score'], results['keyboard_recom'] = check_keyboard_navigation(driver)
                elif stage == "check_screen_reader_labels":
                    results['screen_reader_score'], results['screen_reader_recom'] = check_screen_reader_labels(driver)
                elif stage == "check_accessible_captcha":
                    results['captcha_score'], results['captcha_recom'] = check_accessible_captcha(driver)
                elif stage == "check_headings_and_links":
                    results['headings_links_score'], results['headings_links_recom'] = check_headings_and_links(driver)
                elif stage == "check_scalability":
                    results['scalability_score'], results['scalability_recom'] = check_scalability(driver)
                elif stage == "check_image_alt_text":
                    results['alt_text_score'], results['alt_text_recom'] = check_image_alt_text(driver)
                
                pbar.update(1)
        
        total_score = ((results['keyboard_score'] + results['screen_reader_score'] + results['captcha_score'] +
                        results['headings_links_score'] + results['scalability_score'] + results['alt_text_score']) / 6)
        
        entry = {
            'url': url,
            'total_score': total_score,
            'keyboard_functionality': results['keyboard_score'],
            'keyboard_functionality_recom': results['keyboard_recom'],
            'screen_reader_accessibility': results['screen_reader_score'],
            'screen_reader_accessibility_recom': results['screen_reader_recom'],
            'captcha_accessibility': results['captcha_score'],
            'captcha_accessibility_recom': results['captcha_recom'],
            'headings_links_description': results['headings_links_score'],
            'headings_links_description_recom': results['headings_links_recom'],
            'contrast': 0,
            'contrast_recom': [],
            'scalability': results['scalability_score'],
            'scalability_recom': results['scalability_recom'],
            'alt_text': results['alt_text_score'],
            'alt_text_recom': results['alt_text_recom']
        }

        return entry
        
    except Exception as e:
        print(f"Ошибка при проверке сайта {url}: {e}")
    
    finally:
        driver.quit()



@app.route('/review', methods=['POST'])
def review():
    data = request.json
    urls = data.get('urls', [])
    
    results = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(proc, url): url for url in urls}
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"Ошибка при проверке сайта {url}: {e}")

    return jsonify(results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
