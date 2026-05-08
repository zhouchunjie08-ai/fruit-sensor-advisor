from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
import requests
import re
from datetime import datetime
from openai import OpenAI

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), '..', 'frontend')

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
BING_API_KEY = os.environ.get("BING_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

def load_sensors():
    with open(os.path.join(DATA_DIR, 'sensors.json'), 'r', encoding='utf-8') as f:
        return json.load(f)

def load_scenarios():
    with open(os.path.join(DATA_DIR, 'scenarios.json'), 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_keywords_from_query(query):
    keywords = []
    query_lower = query.lower()
    
    keyword_map = {
        '草莓': ['草莓', '成熟度', '颜色', '硬度', '采摘', '无损检测', '糖度'],
        '番茄': ['番茄', '西红柿', '目标识别', '定位', '避障'],
        '无人机': ['无人机', '巡检', '飞行', '病虫害', '测绘'],
        '果园': ['果园', '导航', 'slam', '自主', '避障'],
        '蔬菜': ['蔬菜', '温室', '作业', '定位'],
    }
    
    for key, words in keyword_map.items():
        if any(w in query_lower for w in words):
            keywords.append(key)
    
    sensor_keywords = {
        '视觉': ['视觉', '相机', '图像', '识别', 'ai', '深度'],
        '雷达': ['雷达', '激光', 'lidar', '测距'],
        '触觉': ['触觉', '力', '硬度', '压力'],
        'IMU': ['imu', '姿态', '加速度', '陀螺仪'],
        '超声波': ['超声波', '超声', '近距'],
    }
    
    sensor_types = []
    for key, words in sensor_keywords.items():
        if any(w in query_lower for w in words):
            sensor_types.append(key)
    
    return keywords, sensor_types

def generate_search_queries(user_query, sensors):
    keywords, sensor_types = extract_keywords_from_query(user_query)
    
    queries = []
    
    if keywords:
        for kw in keywords:
            queries.append(f"{kw} 农业机器人 传感器 采购")
            queries.append(f"{kw} 传感器 中标公告")
    
    for sensor in sensors[:3]:
        queries.append(f"{sensor['model']} {sensor['vendor']} 最新价格")
        queries.append(f"{sensor['model']} 客户案例")
    
    return list(set(queries))[:8]

def search_web(query):
    global BING_API_KEY
    search_results = []
    
    if BING_API_KEY:
        try:
            url = "https://api.bing.microsoft.com/v7.0/search"
            headers = {"Ocp-Apim-Subscription-Key": BING_API_KEY}
            params = {"q": query, "count": 10, "mkt": "zh-CN"}
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                for item in data.get('webPages', {}).get('value', [])[:10]:
                    search_results.append({
                        'title': item.get('name', ''),
                        'url': item.get('url', ''),
                        'snippet': item.get('snippet', '')[:300],
                        'date': item.get('dateLastCrawled', '')[:10]
                    })
                return search_results
        except Exception as e:
            pass
    
    try:
        url = f"https://ddg-api.vercel.app/search?q={requests.utils.quote(query)}&max_results=8"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            for item in data:
                search_results.append({
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'snippet': item.get('body', '')[:300],
                    'date': ''
                })
    except Exception as e:
        pass
    
    return search_results

def extract_info_with_llm(title, snippet, query):
    try:
        prompt = f"""从以下网页信息中提取与"{query}"相关的关键信息：

标题：{title}
内容摘要：{snippet}

提取以下信息（如果未找到则为空字符串）：
- 产品型号
- 价格（如有，如"999元"）
- 客户名称（如有）
- 订单金额（如有，如"100万"）
- 发布时间

返回纯JSON格式，不要其他文字：
{{"model": "", "price": "", "customer": "", "amount": "", "date": ""}}"""

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=300
        )
        
        result_text = response.choices[0].message.content.strip()
        
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        pass
    
    return None

def get_evidence_level(url):
    if not url:
        return "C"
    
    if any(domain in url for domain in ['.gov.cn', 'gov.cn']):
        return "A"
    if any(domain in url for domain in ['huatengn.com', 'tianyilhanghang.com', 'benewake.com', 
                                         'robosense.cn', 'hesai.com', 'hikrobot.com', 
                                         'bosch-sensortec.com', 'bluedot.cn']):
        return "A"
    if any(domain in url for domain in ['36kr.com', 'ifeng.com', 'sina.com.cn', 'qq.com', '163.com']):
        return "B"
    
    return "C"

def realtime_search(user_query, sensors):
    results = {
        'price_updates': [],
        'bid_notices': [],
        'news': [],
        'search_queries': [],
        'is_demo': True
    }
    
    search_queries = generate_search_queries(user_query, sensors)
    results['search_queries'] = search_queries
    
    try:
        processed_urls = set()
        
        for query in search_queries[:6]:
            search_results = search_web(query)
            
            for item in search_results:
                url = item.get('url', '')
                if not url or url in processed_urls:
                    continue
                processed_urls.add(url)
                
                extracted = extract_info_with_llm(item.get('title', ''), item.get('snippet', ''), query)
                
                info = {
                    'title': item['title'],
                    'url': item['url'],
                    'snippet': item['snippet'][:200],
                    'date': item.get('date', ''),
                    'evidence_level': get_evidence_level(item['url'])
                }
                
                if extracted:
                    if extracted.get('price'):
                        info['price'] = extracted['price']
                        results['price_updates'].append(info)
                    elif extracted.get('customer') or extracted.get('amount'):
                        info['customer'] = extracted.get('customer', '')
                        info['amount'] = extracted.get('amount', '')
                        results['bid_notices'].append(info)
                    else:
                        results['news'].append(info)
                else:
                    results['news'].append(info)
        
        if results['price_updates'] or results['bid_notices'] or results['news']:
            results['is_demo'] = False
    except Exception as e:
        pass
    
    if results['is_demo'] or (not results['price_updates'] and not results['bid_notices'] and not results['news']):
        results['price_updates'] = [
            {'title': '华测 M620 视觉传感器', 'url': 'https://www.huatengn.com', 'snippet': '工业级RGB+Depth双目视觉传感器，适用于农业机器人', 'price': '999元/套', 'evidence_level': 'A'},
            {'title': '速腾聚创 RS-LiDAR-M1', 'url': 'https://www.robosense.cn', 'snippet': '车规级激光雷达，200m测距', 'price': '3999元/套', 'evidence_level': 'A'},
        ]
        results['bid_notices'] = [
            {'title': '某省农业农村厅采购公告', 'url': 'http://www.gov.cn', 'snippet': '采购农业病虫害监测无人机200套', 'customer': '某省农业农村厅', 'amount': '320万元', 'evidence_level': 'A'},
        ]
        results['news'] = [
            {'title': '农业机器人传感器技术研讨会即将召开', 'url': 'https://www.36kr.com', 'snippet': '探讨农业机器人传感器最新技术发展方向', 'evidence_level': 'B'},
            {'title': '智慧农业传感器市场需求持续增长', 'url': 'https://www.sina.com.cn', 'snippet': '农业传感器市场规模预计2026年达到500亿元', 'evidence_level': 'B'},
        ]
    
    results['price_updates'] = results['price_updates'][:5]
    results['bid_notices'] = results['bid_notices'][:3]
    results['news'] = results['news'][:5]
    
    return results

@app.route('/api/sensors', methods=['GET'])
def get_sensors():
    sensors = load_sensors()
    return jsonify({"success": True, "data": sensors})

@app.route('/api/scenarios', methods=['GET'])
def get_scenarios():
    scenarios = load_scenarios()
    return jsonify({"success": True, "data": scenarios})

@app.route('/api/recommend', methods=['POST'])
def recommend():
    user_query = request.json.get('query', '')
    include_realtime = request.json.get('include_realtime', True)
    
    sensors = load_sensors()
    scenarios = load_scenarios()
    
    user_query_lower = user_query.lower()
    
    keywords = []
    if any(word in user_query_lower for word in ['草莓', '成熟度', '果实', '颜色', '硬度', '采摘', '无损检测', '糖度']):
        keywords.append('草莓采摘')
    if any(word in user_query_lower for word in ['番茄', '西红柿', '目标识别', '定位', '避障']):
        keywords.append('番茄采摘')
    if any(word in user_query_lower for word in ['无人机', '巡检', '飞行', '病虫害', '测绘']):
        keywords.append('无人机')
    if any(word in user_query_lower for word in ['果园', '导航', 'slam', '自主', '避障']):
        keywords.append('果园')
    if any(word in user_query_lower for word in ['蔬菜', '温室', '作业', '定位']):
        keywords.append('蔬菜温室')
    if any(word in user_query_lower for word in ['视觉', '相机', '图像', '识别', 'ai']):
        keywords.append('视觉')
    if any(word in user_query_lower for word in ['雷达', '激光', 'lidar', '测距']):
        keywords.append('雷达')
    if any(word in user_query_lower for word in ['触觉', '力', '硬度', '压力']):
        keywords.append('触觉')
    if any(word in user_query_lower for word in ['imu', '姿态', '加速度', '陀螺仪']):
        keywords.append('imu')
    if any(word in user_query_lower for word in ['超声波', '超声', '近距']):
        keywords.append('超声波')
    
    if not keywords:
        keywords = ['通用']
    
    matched_scenarios = []
    for scenario in scenarios:
        for tag in scenario['tags']:
            for keyword in keywords:
                if keyword in tag.lower() or any(keyword in t.lower() for t in scenario['tags']):
                    matched_scenarios.append(scenario)
                    break
    
    if not matched_scenarios:
        matched_scenarios = scenarios[:2]
    
    results = []
    for scenario in matched_scenarios[:2]:
        scenario_sensors = [s for s in sensors if s['id'] in scenario['sensor_ids']]
        
        result = {
            'id': scenario['id'],
            'name': scenario['name'],
            'description': scenario['description'],
            'rationale': scenario['rationale'],
            'sensors': scenario_sensors,
            'test_suggestion': scenario['test_suggestion'],
            'vendor_contact': scenario['vendor_contact'],
            'case': scenario['case']
        }
        results.append(result)
    
    response_data = {
        "recommendations": results,
        "matched_keywords": keywords,
        "total_found": len(results)
    }
    
    if include_realtime:
        try:
            realtime_results = realtime_search(user_query, sensors)
            response_data['realtime_info'] = realtime_results
            response_data['retrieved_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            response_data['realtime_info'] = {
                'error': f'实时检索失败: {str(e)}',
                'price_updates': [],
                'bid_notices': [],
                'news': []
            }
            response_data['retrieved_at'] = None
    
    return jsonify({
        "success": True,
        "data": response_data
    })

@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('q', '').lower()
    sensors = load_sensors()
    
    results = []
    for sensor in sensors:
        if query in sensor['model'].lower() or query in sensor['type'].lower() or query in sensor['vendor'].lower():
            results.append(sensor)
    
    if not results:
        results = sensors[:4]
    
    return jsonify({"success": True, "data": results})

@app.route('/api/realtime', methods=['POST'])
def realtime():
    user_query = request.json.get('query', '')
    sensors = load_sensors()

    try:
        results = realtime_search(user_query, sensors)

        return jsonify({
            "success": True,
            "data": results,
            "retrieved_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "data": {
                'price_updates': [],
                'bid_notices': [],
                'news': []
            }
        })

@app.route('/')
def serve_frontend():
    return send_from_directory(FRONTEND_DIR, 'index.html')

if __name__ == '__main__':
    print("=" * 50)
    print("果感知·智选助手 后端服务")
    print("=" * 50)
    print("服务地址: http://localhost:5000")
    print("实时检索: 已启用 (DeepSeek API)")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)
