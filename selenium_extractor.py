from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time
import os
import sys
import hashlib

def extract_transcript_with_selenium(url, output_file):
    """
    使用Selenium打开URL，点击文字记录标签，然后提取会议记录
    
    Args:
        url: 会议纪要URL
        output_file: 输出文件路径
    """
    # 设置Chrome选项
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 启用无头模式
    chrome_options.add_argument("--window-size=1920,1080")  # 设置窗口大小
    chrome_options.add_argument("--start-maximized")
    
    # 添加以下选项来解决SSL错误
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--ignore-ssl-errors")
    chrome_options.add_argument("--allow-insecure-localhost")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--reduce-security-for-testing")
    
    # 尝试使用较低的TLS版本兼容性
    chrome_options.add_argument("--ssl-version-min=tls1")
    chrome_options.add_argument("--disable-site-isolation-trials")
    
    # 如果还有问题，可以尝试完全禁用SSL验证(仅用于测试)
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    # 初始化WebDriver
    print("正在初始化无头浏览器...")
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # 访问URL
        print(f"正在访问: {url}")
        driver.get(url)
        
        # 等待页面加载
        print("等待页面加载...")
        time.sleep(5)
        
        # 查找并点击"文字记录"标签
        print("尝试点击文字记录标签...")
        try:
            # 等待元素可点击
            text_record_tab = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'ud__tabs__tab') and contains(text(), '文字记录')]"))
            )
            # 点击元素
            text_record_tab.click()
            print("已点击文字记录标签")
            # 等待内容加载
            time.sleep(2)
        except Exception as e:
            print(f"点击文字记录标签时出错: {e}")
            # 尝试使用JavaScript点击
            try:
                driver.execute_script("Array.from(document.querySelectorAll('div.ud__tabs__tab')).find(el => el.textContent.includes('文字记录')).click();")
                print("已使用JavaScript点击文字记录标签")
                time.sleep(2)
            except Exception as js_error:
                print(f"使用JavaScript点击失败: {js_error}")
                print("继续尝试提取内容...")
        
        # 等待会议记录内容加载
        print("等待会议记录内容加载...")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "paragraph-editor-wrapper"))
        )
        
        # 向下滚动加载所有内容
        print("开始滚动加载所有会议记录内容...")
        transcript = scroll_and_load_all_content(driver, output_file)
        
        print(f"已成功提取会议记录并保存到 {output_file}")
        print(f"共提取了 {len(transcript)} 条对话")
        return True
    
    except Exception as e:
        print(f"提取过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 截图保存，便于调试
        try:
            screenshot_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'screenshot.png')
            driver.save_screenshot(screenshot_path)
            print(f"已保存页面截图到 {screenshot_path}")
        except:
            pass
            
        # 在无头模式下不需要等待用户确认
        print("处理完成，自动关闭浏览器...")
        driver.quit()

def scroll_and_load_all_content(driver, output_file):
    """
    滚动页面直到所有内容都被加载，并在每次发现新内容时保存
    
    Args:
        driver: Selenium WebDriver对象
        output_file: 输出文件路径
        
    Returns:
        list: 完整的会议记录列表
    """
    print("开始加载内容...")
    
    # 等待初始内容完全加载
    print("等待初始内容加载...")
    time.sleep(5)  # 增加初始等待时间
    
    # 初始化存储结构
    saved_transcript = []
    processed_texts = set()
    
    def extract_and_save_content(paragraphs, current_content=None):
        """
        从段落中提取内容并保存
        返回新增内容数量
        """
        if current_content is None:
            current_content = []
            
        new_items_count = 0
        updated_items_count = 0
        content_updated = False
        
        # 使用字典来临时存储最新的内容
        latest_content = {}
        
        for paragraph in paragraphs:
            # 提取说话人
            try:
                speaker_element = paragraph.find_element(By.CSS_SELECTOR, "div.p-user-name")
                speaker = speaker_element.get_attribute("user-name-content")
            except:
                speaker = "未知说话人"
            
            # 提取时间
            try:
                time_element = paragraph.find_element(By.CSS_SELECTOR, "div.p-time")
                timestamp = time_element.get_attribute("time-content")
            except:
                timestamp = ""
            
            # 提取内容
            content = ""
            try:
                content_spans = paragraph.find_elements(By.CSS_SELECTOR, "span[data-string='true'][data-leaf='true']")
                for span in content_spans:
                    # 排除换行符
                    if span.get_attribute("data-enter") != "true":
                        content += span.text
            except:
                content = ""
            
            # 只处理有说话人、时间和内容的段落
            if speaker and timestamp and content:
                # 使用说话人和时间作为唯一标识
                dialog_key = f"{speaker}_{timestamp}"
                
                # 将当前内容添加到latest_content字典
                if dialog_key in latest_content:
                    # 如果新内容比已存储的长，更新它
                    if len(content) > len(latest_content[dialog_key]['content']):
                        latest_content[dialog_key] = {
                            'speaker': speaker,
                            'time': timestamp,
                            'content': content
                        }
                        content_updated = True
                else:
                    latest_content[dialog_key] = {
                        'speaker': speaker,
                        'time': timestamp,
                        'content': content
                    }
        
        # 更新saved_transcript
        for dialog_key, dialog_data in latest_content.items():
            # 检查是否已存在这段对话
            existing_dialog = None
            for i, item in enumerate(saved_transcript):
                if item['speaker'] == dialog_data['speaker'] and item['time'] == dialog_data['time']:
                    existing_dialog = item
                    existing_index = i
                    break
            
            if existing_dialog:
                # 如果新内容比现有内容长，更新它
                if len(dialog_data['content']) > len(existing_dialog['content']):
                    saved_transcript[existing_index] = dialog_data
                    updated_items_count += 1
                    content_updated = True
            else:
                # 这是一段新对话
                saved_transcript.append(dialog_data)
                new_items_count += 1
                current_content.append(dialog_key)
        
        # 如果有新增或更新的内容，保存到文件
        if new_items_count > 0 or updated_items_count > 0:
            print(f"发现 {new_items_count} 条新对话，更新 {updated_items_count} 条已存在的对话")
            # 按时间排序
            saved_transcript.sort(key=lambda x: x['time'])
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(saved_transcript, f, ensure_ascii=False, indent=2)
        
        return new_items_count + (1 if content_updated else 0), current_content
    
    # 获取初始内容
    print("读取初始内容...")
    initial_paragraphs = driver.find_elements(By.CLASS_NAME, "paragraph-editor-wrapper")
    initial_count = len(initial_paragraphs)
    print(f"初始段落数: {initial_count}")
    
    # 先处理初始内容
    initial_new_items, current_content = extract_and_save_content(initial_paragraphs)
    print(f"初始内容中发现 {initial_new_items} 条对话")
    
    # 初始化滚动相关变量
    prev_count = initial_count
    current_count = initial_count
    no_change_count = 0
    max_no_change = 5
    scroll_attempts = 0
    last_content_hash = hashlib.md5(str(current_content).encode()).hexdigest()
    
    # 尝试多种可能的滚动容器
    scroll_containers = [
        # 1. 文字记录区域的主内容容器
        "document.querySelector('.transcript-content .rc-virtual-list-holder-inner')",
        # 2. 文字记录内容区域
        "document.querySelector('.transcript-content .paragraphs-container')",
        # 3. 文字记录标签内容
        "document.querySelector('.transcript-tab .transcript-content')",
        # 4. 右侧tab内容区
        "document.querySelector('.transcript-tab.right-tab-visible')",
        # 5. 如果以上都没找到，才尝试原来的容器
        "document.querySelector('.rc-virtual-list-holder-inner')",
        "document.querySelector('.rc-virtual-list-holder')",
        "document.querySelector('.rc-virtual-list')",
        # 6. 如果以上都没找到，就使用整个文档
        "document.scrollingElement || document.documentElement"
    ]
    
    # 尝试直接定位transcript容器和RC虚拟列表
    primary_containers = [
        ".transcript-content .rc-virtual-list-holder",
        ".transcript-content .rc-virtual-list",
        ".transcript-tab .rc-virtual-list-holder",
        ".rc-virtual-list-holder",
        ".paragraphs-container",
        ".transcript-content"
    ]
    
    target_container = None
    for selector in primary_containers:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for element in elements:
                if element.is_displayed():
                    target_container = element
                    print(f"找到可见的虚拟列表容器: {selector}")
                    break
            if target_container:
                break
        except Exception as e:
            print(f"定位容器 {selector} 时出错: {e}")
            continue
    
    # 尝试每个可能的滚动容器
    container_js = None
    for container_query in scroll_containers:
        if driver.execute_script(f"return {container_query} !== null"):
            container_js = container_query
            print(f"找到可滚动容器: {container_query}")
            break
    
    if not container_js:
        print("未找到可滚动容器，将尝试滚动整个页面")
        container_js = "document.scrollingElement || document.documentElement"
    
    # 循环滚动直到所有内容都被加载
    pause_between_wheel_events = 0.3  # 减少滚动间隔
    scroll_step = 100  # 减小滚动步长到100像素
    scroll_batch = 3  # 每批次滚动次数
    
    # 开始滚动加载更多内容
    print("开始滚动加载更多内容...")
    
    while True:
        scroll_attempts += 1
        prev_count = current_count
        
        # 方法0: 使用鼠标滚轮事件
        if target_container:
            try:
                print(f"尝试鼠标滚轮滚动... (尝试 {scroll_attempts})")
                from selenium.webdriver.common.action_chains import ActionChains
                
                # 移动到容器并点击
                ActionChains(driver).move_to_element(target_container).click().perform()
                time.sleep(0.3)
                
                # 分批次执行滚动，每批次后检查内容
                for batch in range(4):  # 4个批次
                    # 每批次执行3次小幅度滚动
                    for i in range(scroll_batch):
                        driver.execute_script("""
                            var element = arguments[0];
                            var deltaY = arguments[1];
                            var event = new WheelEvent('wheel', {
                                deltaY: deltaY,
                                deltaMode: 0,
                                bubbles: true,
                                cancelable: true
                            });
                            element.dispatchEvent(event);
                        """, target_container, scroll_step)
                        time.sleep(pause_between_wheel_events)
                    
                    # 每批次滚动后等待内容加载并检查
                    time.sleep(0.2)  # 从0.5减少到0.2秒
                    batch_paragraphs = driver.find_elements(By.CLASS_NAME, "paragraph-editor-wrapper")
                    batch_count = len(batch_paragraphs)
                    
                    if batch_count > current_count:
                        print(f"批次 {batch + 1} 发现新内容，从 {current_count} 增加到 {batch_count}")
                        # 提取并保存新内容
                        new_items_count, current_content = extract_and_save_content(batch_paragraphs, current_content)
                        current_count = batch_count
                        
                        if new_items_count > 0:
                            # 发现新内容，重置计数器
                            no_change_count = 0
                            last_content_hash = hashlib.md5(str(current_content).encode()).hexdigest()
                            break  # 跳出当前批次循环，开始新的滚动尝试
            except Exception as e:
                print(f"鼠标滚轮滚动失败: {e}")
        
        # 等待新内容加载
        time.sleep(0.2)  # 从0.5减少到0.2秒
        
        # 提取当前所有段落
        paragraphs = driver.find_elements(By.CLASS_NAME, "paragraph-editor-wrapper")
        current_count = len(paragraphs)
        print(f"当前段落数: {current_count}")
        
        # 提取并保存新内容
        new_items_count, current_content = extract_and_save_content(paragraphs, current_content)
        
        # 计算当前内容的哈希值
        current_content_hash = hashlib.md5(str(current_content).encode()).hexdigest()
        
        if new_items_count > 0:
            no_change_count = 0
            last_content_hash = current_content_hash
        else:
            if current_content_hash != last_content_hash:
                print("内容发生变化，继续滚动...")
                no_change_count = 0
                last_content_hash = current_content_hash
            else:
                no_change_count += 1
                print(f"未发现新内容，尝试再次滚动... ({no_change_count}/{max_no_change})")
                
                # 如果多次尝试未发现新内容，尝试更小的滚动步长
                if no_change_count >= 2:
                    temp_scroll_step = scroll_step // 2
                    print(f"尝试使用更小的滚动步长: {temp_scroll_step}像素")
                    
                    for i in range(scroll_batch * 2):  # 使用更多次数的小步长滚动
                        driver.execute_script("""
                            var element = arguments[0];
                            var deltaY = arguments[1];
                            var event = new WheelEvent('wheel', {
                                deltaY: deltaY,
                                deltaMode: 0,
                                bubbles: true,
                                cancelable: true
                            });
                            element.dispatchEvent(event);
                        """, target_container, temp_scroll_step)
                        time.sleep(pause_between_wheel_events)  # 使用相同的间隔时间
                    
                    # 检查是否发现新内容
                    time.sleep(0.2)  # 从0.5减少到0.2秒
                    retry_paragraphs = driver.find_elements(By.CLASS_NAME, "paragraph-editor-wrapper")
                    if len(retry_paragraphs) > current_count:
                        print("使用更小步长滚动发现新内容")
                        new_items_count, current_content = extract_and_save_content(retry_paragraphs, current_content)
                        if new_items_count > 0:
                            no_change_count = 0
                            current_count = len(retry_paragraphs)
                            last_content_hash = hashlib.md5(str(current_content).encode()).hexdigest()
        
        # 如果连续多次没有发现新内容，且内容哈希值也没有变化，则认为已经加载完成
        if no_change_count >= max_no_change:
            print(f"连续{max_no_change}次未发现新内容，认为已加载完成")
            break
    
    # 最后再次检查是否有新内容
    final_paragraphs = driver.find_elements(By.CLASS_NAME, "paragraph-editor-wrapper")
    final_new_items, _ = extract_and_save_content(final_paragraphs, current_content)
    
    if final_new_items > 0:
        print(f"最终检查发现 {final_new_items} 条新对话")
    
    # 汇报最终结果
    print(f"提取完成，共找到 {len(saved_transcript)} 条对话")
    print(f"最终保存结果到 {output_file}")
    
    return saved_transcript

def convert_to_csv(json_file, csv_file):
    """
    将JSON格式转换为CSV格式
    """
    import csv
    
    # 读取JSON文件
    with open(json_file, 'r', encoding='utf-8') as f:
        transcript = json.load(f)
    
    # 写入CSV文件
    with open(csv_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        # 写入表头
        writer.writerow(['说话人', '时间', '内容'])
        # 写入数据
        for item in transcript:
            writer.writerow([
                item['speaker'],
                item['time'],
                item['content']
            ])
    
    print(f"已成功将 {json_file} 转换为 {csv_file}")
    print(f"共转换了 {len(transcript)} 条对话")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python selenium_extractor.py <会议纪要URL> [输出文件.json]")
        print("示例: python selenium_extractor.py https://shengcaiyoushu01.feishu.cn/minutes/obcnh9cy43l7hi2gtw9g52tb")
        sys.exit(1)
        
    url = sys.argv[1]
    
    if not (url.startswith('http://') or url.startswith('https://')):
        print("请提供有效的URL，包含http://或https://前缀")
        sys.exit(1)
    
    # 如果只提供一个参数，默认输出到output.json
    if len(sys.argv) == 2:
        output_file = "output.json"
    else:
        output_file = sys.argv[2]
    
    # 提取会议记录
    success = extract_transcript_with_selenium(url, output_file)
    
    if success:
        # 提供CSV转换选项
        csv_file = output_file.replace('.json', '.csv')
        convert = input(f"是否要将结果转换为CSV格式并保存到 {csv_file}？(y/n): ")
        if convert.lower() == 'y':
            convert_to_csv(output_file, csv_file)
