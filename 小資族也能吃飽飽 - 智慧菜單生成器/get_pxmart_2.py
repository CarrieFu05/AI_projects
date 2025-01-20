import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# 如果不做設置，chrome視窗可能會自動關閉
options = webdriver.ChromeOptions()
options.add_experimental_option("detach", True)
prefs = {
    # 禁止通知彈窗
    "profile.default_content_setting_values.notifications": 2,
    # 禁止位置彈窗
    "profile.default_content_setting_values.geolocation": 2,
}
options.add_experimental_option("prefs", prefs)

driver = webdriver.Chrome(options=options, service=Service(
    ChromeDriverManager().install()))

data = []

url = 'https://pxgo.net/444Qp0r'
driver.get(url)
driver.maximize_window()
time.sleep(1)

# 進入商品頁面
driver.find_element(By.CLASS_NAME, "img-text-item").click()
time.sleep(1)

# 點左側分類
firsts = driver.find_elements(By.CLASS_NAME, "left-div-list")
for first in firsts[2:7]:
    first.click()
    time.sleep(1)
    # 進入子分類商品頁面，抓取商品資訊
    seconds = driver.find_elements(By.CLASS_NAME, "left-div-list-children-item")
    for second in seconds:
        data.append({
            'category': second.text,
            'items': []
        })
        second.click()
        time.sleep(1)
        # 滾動頁面到底部
        # 找到滾動的目標元素
        scrollable_div = driver.find_element(By.CLASS_NAME, "right-scroll-div")
        # 使用 JavaScript 滾動該元素
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", scrollable_div)
        time.sleep(3)
        # 取得商品資訊
        products = driver.find_elements(By.CLASS_NAME, "browse-list")
        for product in products:
            data[-1].get('items').append({
                'name': product.find_element(By.CLASS_NAME, "falls-font").text,
                'price': product.find_element(By.CLASS_NAME, "falls-active-price-number").text
            })
        time.sleep(1)
        # 進入子分類的子分類商品頁面，抓取商品資訊
        thirds = driver.find_elements(By.CLASS_NAME, "right-div-category-item2")
        for third in thirds:
            third.click()
            time.sleep(1)
            # 滾動頁面到底部
            # 找到滾動的目標元素
            scrollable_div = driver.find_element(By.CLASS_NAME, "right-scroll-div")
            # 使用 JavaScript 滾動該元素
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", scrollable_div)
            time.sleep(3)
            # 取得商品資訊
            products = driver.find_elements(By.CLASS_NAME, "browse-list")
            for product in products:
                data[-1].get('items').append({
                    'name': product.find_element(By.CLASS_NAME, "falls-font").text,
                    'price': product.find_element(By.CLASS_NAME, "falls-active-price-number").text
                })
            time.sleep(1)

# 匯出 JSON
with open('pxmart/pxmart_2.json', mode='w', encoding='utf-8') as f:
    json.dump(data, f, indent=4, ensure_ascii=False)
print(f"已成功從網頁產生 JSON 並保存到 pxmart/pxmart_2.json")

# 關閉瀏覽器
time.sleep(3)
driver.close()