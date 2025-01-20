import json
import requests
from bs4 import BeautifulSoup
import os

def get_pxmart_data_url():
  url = 'https://www.pxmart.com.tw/campaign/life-will'
  first_res = requests.get(url)
  first_soup = BeautifulSoup(first_res.text, 'html.parser')

  # 初始化data
  data = []

  # 抓取第一層分類
  first_layer = first_soup.find_all('a', class_='Tab_tab__2uJAk')
  for first in first_layer[:4]:
      first_name = first.find('span').text
      first_url = 'https://www.pxmart.com.tw' + first.get('href')
      data.append({
          'first_layer': first_name,
          'first_layer_url': first_url
      })

      # 進入first_url，抓取第二層分類
      second_res = requests.get(first_url)
      second_soup = BeautifulSoup(second_res.text, 'html.parser')
      
      # 在第一分類中新增second_layer，並初始化為空list
      data[-1]['second_layer'] = []
      
      # 抓取第二層分類
      second_layer = second_soup.find_all('a', class_='Button_button__OFOdO')
      for second in second_layer:
          if second.find('span') is None:
              continue
          else:
            second_name = second.find('span').text

            second_url = f"https://www.pxmart.com.tw/_next/data/XoKPkcZ1hAThbvqw6F671{second.get('href')}.json?type={second.get('href').split('/')[-2]}&parentCategory={second.get('href').split('/')[-1]}"

            data[-1]['second_layer'].append({
                'second_layer': second_name,
                'second_layer_url': second_url
            })
  
  # 生成資料夾
  if not os.path.exists('pxmart'):
    os.makedirs('pxmart')
  
  # 寫入 JSON 文件
  with open('pxmart/pxmart_data_url.json', mode="w", encoding="utf-8") as json_file:
      json.dump(data, json_file, indent=4, ensure_ascii=False)
  print(f"已成功從網頁產生 JSON 並保存到 pxmart/pxmart_data_url.json")
  
def get_pxmart_data():
  # 取得 pxmart_data_url.json
  get_pxmart_data_url()

  # 定義output資料結構
  output = [
    {
      "category": "精肉類",
      "items": []
    },
    {
      "category": "鮮魚類",
      "items": []
    },
    {
      "category": "蔬菜類",
      "items": []
    },
    {
      "category": "罐頭食品",
      "items": []
    },
    {
      "category": "冷藏食品",
      "items": []
    },
    {
      "category": "麵製品",
      "items": []
    },    
    {
      "category": "南北貨",
      "items": []
    },
    {
      "category": "冷凍食品",
      "items": []
    },
    {
      "category": "食用油",
      "items": []
    },
  ]

  # 讀取 pxmart_data_url.json
  with open('pxmart/pxmart_data_url.json', mode="r", encoding="utf-8") as url_file:
      url_data = json.load(url_file)
  
  # for迴圈抓取第二層分類的url內的資料
  for i in range(len(url_data)):
      for j in range(len(url_data[i]['second_layer'])):
          file_name = {url_data[i]['second_layer'][j]['second_layer']}
          second_url = url_data[i]['second_layer'][j]['second_layer_url']

          response = requests.get(second_url)
          second_url_data = response.json()

          # 遍歷second_url_data中的key-value
          for key, value in second_url_data['pageProps'].items():
            # print(key, value)
            if key == "categories":
              for k in range(len(value)):
                #  遍歷data中的category尋找匹配的資料
                for l in range(len(output)):
                  if value[k]['category'] == output[l]['category']:
                    for m in range(len(value[k]['group'])):
                      p_name = value[k]['group'][m]['name']
                      p_price = value[k]['group'][m]['price']

                      # 檢查是否已有相同商品
                      check = False
                      for n in range(len(output[l]['items'])):
                        if output[l]['items'][n]['name'] == p_name:
                          check = True
                          break

                      # 檢查後不存在相同商品，則新增商品進output
                      if check == False:
                        output[l]['items'].append({
                          'name': p_name,
                          'price': p_price,
                        })

  # 生成資料夾
  if not os.path.exists('pxmart'):
    os.makedirs('pxmart')

  # 將output存成json檔
  with open(f"pxmart/data_for_ai.json", "w", encoding="utf-8") as file:
    json.dump(output, file, ensure_ascii=False, indent=4)

  print(f"已成功透過 JSON 抓取資料，並已保存到 pxmart/data_for_ai.json")


# 執行程式
if __name__ == '__main__':
# target_url = 'https://www.pxmart.com.tw/campaign/life-will'
  get_pxmart_data()

