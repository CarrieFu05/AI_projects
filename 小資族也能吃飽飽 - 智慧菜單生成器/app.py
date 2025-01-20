import os
from flask import Flask, request, abort, url_for, render_template
import json
import google.generativeai as genai

# set flask
app = Flask(__name__)


@app.route("/")
def formPage():
    return render_template("index.html")


@app.route("/submit", methods=["POST"])
def submit():
    if request.method == "POST":
        form_data = request.form

        # set input data
        pxmart_special = get_ref_data('pxmart/data_for_ai.json')
        pxmart = get_ref_data('pxmart/pxmart_2.json')
        person = form_data.get("person", "0")
        price = form_data.get("price", "0")
        budget = int(person) * int(price)
        dishes = form_data.get("dishes", "0")
        soup = form_data.get("soup", "0")  # default is no soup
        beef = form_data.get("beef", "off")
        shrimp = form_data.get("shrimp", "off")
        fish = form_data.get("fish", "off")
        spicy = form_data.get("spicy", "off")
        other_limit = form_data.get("other_limit", "")

        # make limit list and set form mark
        beef_mark = ""
        shrimp_mark = ""
        fish_mark = ""
        spicy_mark = ""
        other_limit_mark = ""
        limit = []
        if beef == "on":
            limit.append("牛肉")
            beef_mark = "checked"
        if shrimp == "on":
            limit.append("蝦蟹")
            shrimp_mark = "checked"
        if fish == "on":
            limit.append("魚肉")
            fish_mark = "checked"
        if spicy == "on":
            limit.append("辣椒")
            spicy_mark = "checked"
        if other_limit != "":
            limit.append(other_limit)
            other_limit_mark = form_data.get("other_limit")

        # mark soup slecetion
        soup_yes = ""
        soup_no = ""
        if soup == "1":
            soup_yes = "checked"
        elif soup == "0":
            soup_no = "checked"

        # prompt Gemini model and get response
        prompt = f'''
            你是一位精打細算且擅長煮台灣家常菜的人，
            請只使用{pxmart_special}、{pxmart}中的食材，
            並將其以主食、肉類、海鮮、蔬菜、調味料、辛香料幾項進行分類，
            但不要使用{limit}中的食材，
            為{person}位成人設計一份{dishes}菜{soup}湯的午晚餐菜單，
            總預算絕對不能超過{budget}元，
            
            **菜單需滿足以下要求**
            1. 菜品與菜品不得重複(例如：不能同時出現「炒青菜」和「清炒小白菜」)
            2. 菜品與湯品不得重複(例如：不能同時出現「番茄炒蛋」和「番茄蛋湯」)
            3. 菜品可由單一種食材製成(例如：清炒蔬菜、涼拌小黃瓜)。
            4. 食材可以分散使用在菜單上的菜色及湯品中。
            5. 菜單中的菜品與湯品數量必須完全符合{dishes}菜{soup}湯規定。

            **必須嚴格控管預算**
            1. 調味料及辛香料不在採購食材總金額內，僅計算食材金額。
            1. 採購食材總金額絕對不能超過 {budget} 元，若超過則重新設計菜單直到採購食材總金額小於等於{budget}元。
            2. 上述提及的重新設計菜單的方式建議為: 
                * 使用更多蔬菜類食材來降低肉類、海鮮的比例。
                * 選擇低價食材替換掉高價食材。
                * 將使用多樣食材的菜品改為使用單一食材的菜品。
            
            **輸出格式**
            用 HTML 格式輸出，範例格式如下：

            <h3>這是今天的菜單：</h3> 
            <ul> 
            <li>菜品1：xxx</li> 
            <li>菜品2：xxx</li> 
            <li>湯品：xxx</li> 
            </ul> 
            <h3>需要採購的食材如下：</h3> 
            <ul> 
            <li>xxx：xxx元</li> 
            <li>xxx：xxx元</li> 
            <li>總共：xxx元</li> 
            </ul>
            
            輸出前請確保：
            1. 採購食材總金額小於等於{budget}元。
            2. 只顯示最後的方案，絕對不要將生成菜單過程顯示出來。
            3. 輸出的菜單簡潔清晰，絕對不能顯示備註說明。           
        '''

        output = get_google_gemini_response(prompt)
        # output = get_vertexai_gemini_response(prompt)

        return render_template(
            "index.html",
            output=output,
            person=form_data.get("person"),
            price=form_data.get("price"),
            dishes=form_data.get("dishes"),
            soup_yes=soup_yes,
            soup_no=soup_no,
            beef_mark=beef_mark,
            shrimp_mark=shrimp_mark,
            fish_mark=fish_mark,
            spicy_mark=spicy_mark,
            other_limit=other_limit,
            other_limit_mark=other_limit_mark
        )


def get_google_gemini_response(prompt):
    # read env.json file
    with open('env.json', encoding='utf-8') as f:
        env = json.load(f)

    # set gemini key
    genai.configure(api_key=env.get('GOOGLE_GEMINI_KEY'))
    # connect GEMINI model
    model = genai.GenerativeModel('gemini-1.5-flash')

    response = model.generate_content(prompt)
    output = response.text.replace("```", "").replace('html', '').strip()
    return output


def get_ref_data(file_route):
    with open(file_route, 'r', encoding='utf-8') as f:
        ref_data = json.load(f)
    return ref_data


# run flask
if __name__ == "__main__":
    app.run(debug=True)
