import pickle
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

FROM = '上海'
TO = '徐州'
PASSENGER_NAME = '刘冰'
COOKIE_FILE = '12306_cookies.pkl'
today_str = datetime.today().strftime('%Y-%m-%d')

def init_browser():
    options = webdriver.ChromeOptions()
    options.add_argument('--start-minimized')  # 最小化启动
    driver = webdriver.Chrome(options=options)
    return driver

def save_cookie(driver):
    cookies = driver.get_cookies()
    with open(COOKIE_FILE, "wb") as f:
        pickle.dump(cookies, f)
    print("✅ Cookie 已保存")

def load_cookie(driver):
    driver.get("https://kyfw.12306.cn/otn/view/index.html")
    with open(COOKIE_FILE, "rb") as f:
        cookies = pickle.load(f)
        for cookie in cookies:
            driver.add_cookie(cookie)
    driver.refresh()
    time.sleep(2)
    if "我的12306" in driver.page_source:
        print("✅ 自动登录成功")
    else:
        raise Exception("❌ Cookie 失效，请删除 cookie 文件后重新扫码")

def manual_login(driver):
    driver.get('https://kyfw.12306.cn/otn/resources/login.html')
    print("🚨 请扫码登录12306账号")
    while True:
        if "我的12306" in driver.page_source:
            print("✅ 登录成功！")
            save_cookie(driver)
            break
        time.sleep(1)

def search_ticket(driver):
    driver.get("https://kyfw.12306.cn/otn/leftTicket/init")
    time.sleep(1)

    driver.find_element(By.ID, "fromStationText").send_keys(Keys.CONTROL, 'a', FROM, Keys.ENTER)
    driver.find_element(By.ID, "toStationText").send_keys(Keys.CONTROL, 'a', TO, Keys.ENTER)
    driver.find_element(By.ID, "train_date").send_keys(Keys.CONTROL, 'a', today_str, Keys.ENTER)
    driver.find_element(By.ID, "query_ticket").click()

    print(f"🎯 开始刷票：{FROM} → {TO}（{today_str}）")

    while True:
        time.sleep(0.8)
        try:
            buttons = driver.find_elements(By.XPATH, "//a[text()='预订']")
            if buttons:
                print("🎉 抢到票啦！点击预订...")
                buttons[0].click()
                break
            else:
                print("🔄 没票，刷新中...")
                driver.find_element(By.ID, "query_ticket").click()
        except Exception as e:
            print("⚠️ 报错：", e)

    confirm_and_submit(driver)

def confirm_and_submit(driver):
    time.sleep(2)
    try:
        checkbox = driver.find_element(By.XPATH, f"//label[contains(text(), '{PASSENGER_NAME}')]/preceding-sibling::input")
        driver.execute_script("arguments[0].click();", checkbox)
        time.sleep(0.5)

        submit_btn = driver.find_element(By.ID, 'submitOrder_id')
        submit_btn.click()

        print(f"✅ 已自动勾选乘客“{PASSENGER_NAME}”，并提交订单，请尽快付款！")

    except Exception as e:
        print("⚠️ 自动提交失败，请手动完成下单", e)

    input("👉 抢票完成。按 Enter 键关闭程序，或手动关闭窗口。")

if __name__ == '__main__':
    driver = init_browser()

    try:
        try:
            load_cookie(driver)
        except:
            manual_login(driver)

        search_ticket(driver)

    except Exception as e:
        print("❌ 程序出错：", e)
