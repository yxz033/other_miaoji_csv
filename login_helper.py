from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time
import os

def save_cookies(url):
    """
    打开浏览器访问指定URL，等待用户登录，然后保存cookies
    
    Args:
        url: 要访问的URL
    """
    # 设置Chrome选项
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    
    # 初始化WebDriver
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # 访问URL
        print(f"正在打开浏览器并访问: {url}")
        driver.get(url)
        
        # 等待用户扫码登录
        print("请在打开的浏览器中扫码登录...")
        print("系统将等待您完成登录...")
        
        # 等待登录成功（检测到会议纪要页面加载）
        max_wait_time = 300  # 最多等待5分钟
        polling_interval = 2  # 每2秒检查一次
        waited_time = 0
        
        # 循环检查是否已成功加载会议纪要内容
        while waited_time < max_wait_time:
            # 查找页面上的会议纪要特征元素
            paragraphs = driver.find_elements(By.CLASS_NAME, "paragraph-editor-wrapper")
            
            if len(paragraphs) > 0:
                print("检测到登录成功并加载了会议纪要内容！")
                break
                
            # 检查是否还在登录页面
            login_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '登录') or contains(text(), 'Login')]")
            if len(login_elements) > 0:
                print(f"请完成登录... (已等待 {waited_time} 秒)")
            else:
                print(f"正在等待会议纪要加载... (已等待 {waited_time} 秒)")
            
            time.sleep(polling_interval)
            waited_time += polling_interval
        
        if waited_time >= max_wait_time:
            print("等待超时，请确认是否已成功登录并加载了会议纪要。")
            return False
        
        # 获取所有cookies
        cookies = driver.get_cookies()
        
        # 获取localStorage
        local_storage = driver.execute_script("return Object.keys(localStorage).reduce((obj, key) => { obj[key] = localStorage.getItem(key); return obj; }, {});")
        
        # 保存cookies和localStorage到文件
        config = {
            'cookies': cookies,
            'localStorage': local_storage,
            'url': url
        }
        
        config_dir = os.path.dirname(os.path.abspath(__file__))
        config_file = os.path.join(config_dir, 'feishu_config.json')
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
            
        print(f"成功保存登录凭证到 {config_file}")
        return True
        
    except Exception as e:
        print(f"出现错误: {e}")
        return False
    finally:
        # 等待用户确认后关闭浏览器
        input("按回车键关闭浏览器...")
        driver.quit()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("用法: python login_helper.py <会议纪要URL>")
        print("示例: python login_helper.py https://shengcaiyoushu01.feishu.cn/minutes/obcnh9cy43l7hi2gtw9g52tb")
        sys.exit(1)
        
    url = sys.argv[1]
    
    if not (url.startswith('http://') or url.startswith('https://')):
        print("请提供有效的URL，包含http://或https://前缀")
        sys.exit(1)
        
    success = save_cookies(url)
    
    if success:
        print("\n您现在可以使用以下命令直接提取会议记录:")
        print(f"python transcript_parser.py {url}")
    else:
        print("\n获取登录凭证失败，请重试。")
