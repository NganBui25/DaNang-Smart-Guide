import csv
import json
import os
import re
import time
import requests
import unicodedata
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(CURRENT_DIR), "data")
IMAGE_DIR = os.path.join(DATA_DIR, "image")
JSON_PATH_COFFEE = os.path.join(DATA_DIR, "places_coffee.json")
JSON_PATH_FOOD = os.path.join(DATA_DIR, "places_food.json")
JSON_PATH_PLAY = os.path.join(DATA_DIR, "places_play.json")
CSV_PATH_USERS = os.path.join(DATA_DIR, "users.csv")

def extract_lat_lng(url):
    """Trích xuất tọa độ từ URL của Google Maps"""
    pin_regex = r"!3d([-0-9.]+)!4d([-0-9.]+)"
    match = re.search(pin_regex, url)
    if match:
        return match.group(1), match.group(2)
    
    center_regex = r"@([-0-9.]+),([-0-9.]+)"
    match = re.search(center_regex, url)
    if match:
        return match.group(1), match.group(2)
        
    return None, None

def get_and_download_image(driver, save_folder=IMAGE_DIR):
    """Tải ảnh và trả về đường dẫn tương đối"""
    try:
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)

        wait = WebDriverWait(driver, 10)
        place_name = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1.DUwDvf"))).text
        safe_name = re.sub(r'[\\/*?:"<>|]', "", place_name).replace(" ", "_")

        img_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.aoRNLd img")))
        img_url = img_element.get_attribute("src")
        
        if not img_url:
            return None

        file_name = f"{safe_name}.jpg"
        absolute_file_path = os.path.join(save_folder, file_name)
        relative_file_path = f"data/image/{file_name}"

        response = requests.get(img_url, stream=True, timeout=10)
        if response.status_code == 200:
            with open(absolute_file_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            return relative_file_path 
        else:
            print(f"Lỗi tải ảnh: {response.status_code}")
            return None

    except Exception as e:
        print(f"Không thể xử lý ảnh: {e}")
        return None

def scroll_sidebar(driver, max_places):
    """Cuộn danh sách bên trái để load đủ số lượng quán mong muốn"""
    try:
        sidebar = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='feed']"))
        )
        last_height = driver.execute_script("return arguments[0].scrollHeight", sidebar)
        
        print(f"🔄 Đang cuộn danh sách để tìm đủ {max_places} quán...")
        while len(driver.find_elements(By.CSS_SELECTOR, "div[role='article']")) < max_places:
            driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', sidebar)
            time.sleep(2) 
            new_height = driver.execute_script("return arguments[0].scrollHeight", sidebar)
            if new_height == last_height: 
                print("Đã cuộn đến cuối danh sách.")
                break
            last_height = new_height
    except Exception as e:
        print(f"⚠️ Không tìm thấy sidebar cuộn: {e}")

def get_all_place_links(driver, search_query, max_places):
    """Tìm kiếm và trả về danh sách các link địa điểm"""
    search_box = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "q")))
    search_box.clear()
    search_box.send_keys(search_query)
    search_box.send_keys(Keys.ENTER)
    time.sleep(5) 
    scroll_sidebar(driver, max_places)

    full_articles = driver.find_elements(By.CSS_SELECTOR, "div[role='article']")
    print(f"✅ Đã tìm thấy {len(full_articles)} địa điểm. Đang trích xuất link...")
    
    place_links = []
    for article in full_articles:
        try:
            link_element = article.find_element(By.TAG_NAME, "a")
            href = link_element.get_attribute("href")
            name = link_element.get_attribute("aria-label")
            if href:
                place_links.append({"name": name, "url": href})
        except Exception as e:
            continue
            
    return place_links

def create_email_from_name(name):
    """Bỏ dấu tiếng Việt, xóa khoảng trắng và thêm @gmail.com"""
    clean_name = ''.join(c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn')
    email_prefix = clean_name.replace(" ", "").lower()
    return f"{email_prefix}@gmail.com"

def crawl_reviews(driver, extracted_users, max_reviews=3):
    """Chuyển sang tab Đánh giá và cào thông tin"""
    reviews_data = []
    try:
        tab_xpath = "//button[@role='tab' and (contains(., 'đánh giá') or contains(., 'Reviews'))]"
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, tab_xpath))).click()
        time.sleep(3) 

        review_blocks = driver.find_elements(By.CSS_SELECTOR, "div.jftiEf")
        
        for block in review_blocks[:max_reviews]:
            try:
                more_btn = block.find_element(By.CSS_SELECTOR, "button.w8nwRe.kyuRq")
                driver.execute_script("arguments[0].click();", more_btn)
                time.sleep(0.5)
            except:
                pass
                
            try:
                name = block.find_element(By.CSS_SELECTOR, "div.d4r55").text
            except:
                name = "Ẩn danh"
                
            try:
                time_str = block.find_element(By.CSS_SELECTOR, "span.rsqaWe").text
            except:
                time_str = ""
                
            try:
                star_elem = block.find_element(By.CSS_SELECTOR, "span.kvMYJc")
                stars = star_elem.get_attribute("aria-label")
            except:
                stars = ""
                
            try:
                text = block.find_element(By.CSS_SELECTOR, "span.wiI7pd").text
            except:
                text = ""
                
            if name != "Ẩn danh":
                reviews_data.append({
                    "reviewer_name": name,
                    "review_time": time_str,
                    "rating": stars,
                    "content": text
                })
                
                # Thêm vào danh sách user
                extracted_users.append({
                    "username": name,
                    "email": create_email_from_name(name),
                    "pass": "mkhau123@",
                    "is_admin": "false"
                })

    except Exception as e:
        print(f"  ⚠️ Không thể lấy review (quán có thể không có review): {e}")
        
    return reviews_data

def crawl_detailed_position(url, driver, extracted_users):
    """Cào thông tin chi tiết của 1 quán từ link Google Maps"""
    driver.get(url)
    data = {}

    try:
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'h1.DUwDvf')))
        
        url = driver.current_url
        data['url'] = url
        data['coordinate'] = extract_lat_lng(url)
        data['name'] = driver.find_element(By.CSS_SELECTOR, 'h1.DUwDvf').text

        try:
            data['rating'] = driver.find_element(By.CSS_SELECTOR, "div.F7nice span[aria-hidden='true']").text
        except:
            data['rating'] = None
            
        try:
            address_element = driver.find_element(By.CSS_SELECTOR, 'button[data-item-id="address"]')
            data['address'] = address_element.get_attribute("aria-label").replace("Địa chỉ: ", "").strip()
        except:
            data['address'] = None

        try:
            phone_element = driver.find_element(By.CSS_SELECTOR, 'button[data-item-id^="phone:"] div.Io6YTe')
            data['phone'] = phone_element.text.strip()
        except:
            data['phone'] = None
            
        try:
            website_element = driver.find_element(By.CSS_SELECTOR, 'a[data-item-id="authority"]')
            data['website'] = website_element.get_attribute("href")
        except:
            data['website'] = None
            
        data['image_path'] = get_and_download_image(driver)

        # Cào thêm review và bổ sung vào data dictionary
        data['reviews'] = crawl_reviews(driver, extracted_users, max_reviews=3)

        return data
    except Exception as e:
        print(f"❌ Lỗi khi cào chi tiết link: {e}")
        return None

def save_to_json(data, file_path):
    """Lưu dữ liệu thành file JSON"""
    try:
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        with open(file_path, mode='w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        print(f"✅ Đã lưu dữ liệu JSON thành công vào: {file_path}")
    except Exception as e:
        print(f"❌ Lỗi khi lưu file JSON: {e}")

def save_users_to_csv(users, file_path):
    """Lưu danh sách user vào file CSV (lọc trùng lặp)"""
    try:
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            
        # Dùng dictionary để lọc các username bị trùng
        unique_users = {u['username']: u for u in users}.values()
        
        with open(file_path, mode='w', encoding='utf-8', newline='') as file:
            fieldnames = ['username', 'email', 'pass', 'is_admin']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            
            writer.writeheader()
            writer.writerows(unique_users)
            
        print(f"✅ Đã lưu {len(unique_users)} users vào CSV: {file_path}")
    except Exception as e:
        print(f"❌ Lỗi khi lưu file CSV: {e}")

def main(start_url,query):
    SEARCH_QUERY = query
    MAX_PLACES = 50
    full_position = []
    extracted_users = [] 


    options = webdriver.ChromeOptions()
    options.headless = False
    options.add_argument("--lang=vi-VN")
    options.add_experimental_option('prefs', {'intl.accept_languages': 'vi,vi_VN'})
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.get(start_url)
        places_list = get_all_place_links(driver, SEARCH_QUERY, MAX_PLACES)
        print("-" * 40)
        print(f"🚀 Bắt đầu cào chi tiết {len(places_list)} quán...")
        
        for idx, place in enumerate(places_list):
            print(f"[{idx+1}/{len(places_list)}] Đang cào: {place['name']}")
            detailed_data = crawl_detailed_position(place['url'], driver, extracted_users)
            
            if detailed_data:
                full_position.append(detailed_data)
                
            time.sleep(2) 

        print("-" * 40)
        print("✅ ĐÃ HOÀN THÀNH!")
        print(f"Tổng số quán thu thập thành công: {len(full_position)}")
        
    finally:
        driver.quit()
    return full_position, extracted_users

if __name__ == "__main__":
    MAPS_URL = "https://www.google.com/maps"
    
    tasks = [
        {
            "query": "Cà phê chụp ảnh đẹp đà nẵng",
            "json_path": JSON_PATH_COFFEE 
        },
        {
            "query": "Quán ăn ngon đà nẵng",
            "json_path": JSON_PATH_FOOD 
        },
         {
            "query": "địa điểm vui chơi ở đà nẵng cho giới trẻ",
            "json_path": JSON_PATH_PLAY
        }
    ]

    total_extracted_users = [] 
    for task in tasks:
        print(f"\n🚀 --- ĐANG BẮT ĐẦU CÀO TỪ KHÓA: {task['query']} ---")
        final_data, extracted_users = main(MAPS_URL, task['query'])
        if extracted_users:
            total_extracted_users.extend(extracted_users)
        if final_data:
            dict_format_data = {index: item for index, item in enumerate(final_data, start=1)}
            save_to_json(dict_format_data, task['json_path'])
    if total_extracted_users:
        print(f"\nTổng hợp được {len(total_extracted_users)} users. Đang lưu vào CSV...")
        save_users_to_csv(total_extracted_users, CSV_PATH_USERS)