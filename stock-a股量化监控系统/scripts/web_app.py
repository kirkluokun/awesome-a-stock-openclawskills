#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股量化监控系统 - Web界面
Flask + ECharts
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime
from stock_cache_db import StockCache
from backtest_engine import BacktestEngine
import json
import hashlib

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'  # 生产环境请修改

# 登录管理器
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '请先登录'

# 角色定义
ROLES = {
    'admin': {
        'name': '管理员',
        'permissions': ['read', 'create', 'update', 'delete', 'manage_users', 'change_all_passwords']
    },
    'developer': {
        'name': '开发者',
        'permissions': ['read', 'create', 'update', 'change_own_password']
    },
    'viewer': {
        'name': '访客',
        'permissions': ['read', 'change_own_password']
    }
}

# 用户模型
class User(UserMixin):
    def __init__(self, id, username, role='viewer'):
        self.id = id
        self.username = username
        self.role = role
    
    def has_permission(self, permission):
        """检查是否有某个权限"""
        return permission in ROLES.get(self.role, {}).get('permissions', [])
    
    def can_delete(self):
        """是否可以删除"""
        return self.has_permission('delete')
    
    def can_create(self):
        """是否可以新增"""
        return self.has_permission('create')
    
    def can_update(self):
        """是否可以修改"""
        return self.has_permission('update')
    
    def can_manage_users(self):
        """是否可以管理用户"""
        return self.has_permission('manage_users')
    
    def can_change_password(self, target_user=None):
        """是否可以修改密码"""
        if self.has_permission('change_all_passwords'):
            return True  # 管理员可以改所有人
        if self.has_permission('change_own_password') and target_user == self.username:
            return True  # 可以改自己的
        return False

# 用户数据（生产环境应该存储在数据库）
USERS = {
    'admin': {
        'password': hashlib.sha256('admin123'.encode()).hexdigest(),  # 默认密码: admin123
        'id': 1,
        'role': 'admin'
    },
    'developer': {
        'password': hashlib.sha256('dev123'.encode()).hexdigest(),  # 默认密码: dev123
        'id': 2,
        'role': 'developer'
    },
    'viewer': {
        'password': hashlib.sha256('view123'.encode()).hexdigest(),  # 默认密码: view123
        'id': 3,
        'role': 'viewer'
    }
}

@login_manager.user_loader
def load_user(user_id):
    for username, data in USERS.items():
        if data['id'] == int(user_id):
            return User(user_id, username, data.get('role', 'viewer'))
    return None

# 权限装饰器
from functools import wraps

def permission_required(permission):
    """权限检查装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            if not current_user.has_permission(permission):
                return jsonify({'status': 'error', 'message': '权限不足'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# 监控的核心股票
WATCHED_STOCKS = [
    # 高波动股票（新增）
    '600276',  # 恒瑞医药
    '601012',  # 隆基绿能
    '000858',  # 五粮液
    '601888',  # 中国中免
    # 原有优质股票（保留）
    '600036',  # 招商银行
    '601318',  # 中国平安
    '600519',  # 贵州茅台
    # 移除低波动电力股，保留1只代表
    '601985',  # 中国核电（代表）
]


# ============== 登录路由 ==============

@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in USERS:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if password_hash == USERS[username]['password']:
                user = User(USERS[username]['id'], username, USERS[username].get('role', 'viewer'))
                login_user(user, remember=True)
                next_page = request.args.get('next')
                return redirect(next_page or url_for('index'))
        
        return render_template('login.html', error='用户名或密码错误')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """登出"""
    logout_user()
    return redirect(url_for('login'))


# ============== 页面路由 ==============

@app.route('/')
@login_required
def index():
    """首页 - 仪表盘"""
    return render_template('index.html', username=current_user.username)


@app.route('/stock/<code>')
@login_required
def stock_detail(code):
    """股票详情页"""
    return render_template('stock_detail.html', code=code)


@app.route('/backtest')
@login_required
def backtest_page():
    """回测工具页"""
    return render_template('backtest.html')


@app.route('/optimize')
@login_required
def optimize_page():
    """参数优化页"""
    return render_template('optimize.html')


@app.route('/stocks-manage')
@login_required
def stocks_manage_page():
    """股票池管理页"""
    return render_template('stocks_manage.html')


@app.route('/users-manage')
@login_required
def users_manage_page():
    """用户管理页"""
    if not current_user.can_manage_users():
        return redirect(url_for('index'))
    return render_template('users_manage.html')


@app.route('/profile')
@login_required
def profile_page():
    """个人设置页"""
    return render_template('profile.html')


# ============== API接口 ==============

@app.route('/api/stocks')
@login_required
def api_stocks():
    """获取所有监控股票（返回最近一次数据，不论是否过期）"""
    cache = StockCache()
    
    stocks = []
    for code in WATCHED_STOCKS:
        # 直接获取最近一次的数据（不过滤过期）
        stock = cache.get_stock(code)
        
        if stock:
            # 获取资金流
            fund = cache.get_fund_flow(code, max_age_hours=48)
            if fund:
                stock['fund_flow'] = fund
            
            # 获取技术指标
            tech = cache.get_tech_indicators(code, max_age_hours=48)
            if tech:
                stock['tech_indicators'] = tech
            
            stocks.append(stock)
    
    cache.close()
    
    return jsonify({
        'status': 'success',
        'data': stocks,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })


@app.route('/api/stocks/realtime')
@login_required
def api_stocks_realtime():
    """获取监控股票的实时价格（轻量级，仅价格和涨跌）"""
    cache = StockCache()
    
    stocks = []
    for code in WATCHED_STOCKS:
        stock = cache.get_stock(code)
        if stock:
            # 只返回关键字段，减少数据量
            stocks.append({
                'code': stock['code'],
                'name': stock['name'],
                'price': stock['price'],
                'change_pct': stock['change_pct'],
                'update_time': stock.get('update_time')
            })
    
    cache.close()
    
    return jsonify({
        'status': 'success',
        'data': stocks,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })


@app.route('/api/stock/<code>')
@login_required
def api_stock_detail(code):
    """获取单只股票详情"""
    cache = StockCache()
    
    stock = cache.get_stock(code)
    if not stock:
        cache.close()
        return jsonify({'status': 'error', 'message': '股票不存在'})
    
    # 获取资金流
    fund = cache.get_fund_flow(code, max_age_hours=24)
    if fund:
        stock['fund_flow'] = fund
    
    # 获取技术指标
    tech = cache.get_tech_indicators(code, max_age_hours=24)
    if tech:
        stock['tech_indicators'] = tech
    
    cache.close()
    
    return jsonify({
        'status': 'success',
        'data': stock
    })


@app.route('/api/history/<code>')
@login_required
def api_history(code):
    """获取历史K线数据"""
    days = request.args.get('days', 60, type=int)
    
    from tech_indicators import TechIndicatorCalculator
    calc = TechIndicatorCalculator()
    
    history = calc.get_stock_history(code, days=days)
    
    if history is None:
        return jsonify({'status': 'error', 'message': '获取历史数据失败'})
    
    # 转换为ECharts需要的格式
    data = []
    for date, row in history.iterrows():
        data.append({
            'date': date.strftime('%Y-%m-%d'),
            'open': float(row['open']),
            'close': float(row['close']),
            'high': float(row['high']),
            'low': float(row['low']),
            'volume': float(row['volume'])
        })
    
    return jsonify({
        'status': 'success',
        'data': data
    })


@app.route('/api/backtest', methods=['POST'])
@login_required
def api_backtest():
    """回测接口"""
    data = request.json
    
    symbol = data.get('symbol')
    strategy = data.get('strategy')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    initial_capital = data.get('initial_capital', 100000)
    
    if not all([symbol, strategy, start_date, end_date]):
        return jsonify({'status': 'error', 'message': '参数不完整'})
    
    # 执行回测
    engine = BacktestEngine()
    result = engine.backtest(
        symbol=symbol,
        strategy_name=strategy,
        start_date=start_date.replace('-', ''),
        end_date=end_date.replace('-', ''),
        initial_capital=initial_capital
    )
    
    if result is None:
        return jsonify({'status': 'error', 'message': '回测失败'})
    
    # 转换交易记录
    trades = []
    for trade in result['trades']:
        trades.append({
            'date': trade['date'].strftime('%Y-%m-%d'),
            'action': trade['action'],
            'price': trade['price'],
            'qty': trade['qty'],
            'amount': trade['amount'],
            'profit': trade.get('profit', 0)
        })
    
    result['trades'] = trades
    
    return jsonify({
        'status': 'success',
        'data': result
    })


@app.route('/api/cache/stats')
@login_required
def api_cache_stats():
    """获取缓存统计"""
    cache = StockCache()
    stats = cache.get_cache_stats()
    cache.close()
    
    return jsonify({
        'status': 'success',
        'data': stats
    })


@app.route('/api/stock/<code>/refresh', methods=['POST'])
@login_required
def api_refresh_stock(code):
    """刷新单只股票数据（异步）"""
    import threading
    
    def refresh_in_background(stock_code):
        """后台刷新数据"""
        try:
            from tech_indicators import TechIndicatorCalculator
            from stock_async_fetcher import StockAsyncFetcher
            
            # 1. 更新基础数据
            fetcher = StockAsyncFetcher()
            fetcher.fetch_and_cache([stock_code])
            
            # 2. 更新技术指标
            calc = TechIndicatorCalculator()
            result = calc.calculate_indicators(stock_code)
            if result:
                calc.cache.save_tech_indicators(stock_code, result)
            calc.close()
            
            # 3. 更新资金流（使用智能数据源）
            fund = fetcher.fetch_fund_flow(stock_code)
            
            # 关闭连接
            fetcher.close()
                
        except Exception as e:
            print(f"后台刷新{stock_code}失败: {e}")
    
    # 启动后台线程
    thread = threading.Thread(target=refresh_in_background, args=(code,))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'status': 'success',
        'message': f'正在后台刷新 {code} 的数据，请稍后刷新页面查看'
    })


# ============== 股票池管理API ==============

@app.route('/api/watchlist', methods=['GET'])
@login_required
def api_get_watchlist():
    """获取当前监控股票列表（快速版）"""
    # 只返回代码和名称，不查询实时数据
    # 实时数据由前端异步加载
    
    stocks_info = []
    
    # 从缓存快速获取基本信息（不等待实时数据）
    cache = StockCache()
    
    for code in WATCHED_STOCKS:
        stock = cache.get_stock(code)
        
        if stock:
            stocks_info.append({
                'code': code,
                'name': stock['name'],
                'price': stock.get('price', 0),
                'change_pct': stock.get('change_pct', 0)
            })
        else:
            # 如果缓存没有，只返回代码（前端会显示"加载中"）
            stocks_info.append({
                'code': code,
                'name': '加载中...',
                'price': 0,
                'change_pct': 0
            })
    
    cache.close()
    
    return jsonify({
        'status': 'success',
        'data': stocks_info
    })


@app.route('/api/watchlist', methods=['POST'])
@login_required
def api_add_to_watchlist():
    """添加股票到监控列表（快速版）"""
    data = request.json
    code = data.get('code', '').strip()
    
    if not code:
        return jsonify({'status': 'error', 'message': '股票代码不能为空'})
    
    # 验证代码格式（6位数字）
    if not code.isdigit() or len(code) != 6:
        return jsonify({'status': 'error', 'message': '股票代码格式错误（应为6位数字）'})
    
    # 检查是否已存在
    if code in WATCHED_STOCKS:
        return jsonify({'status': 'error', 'message': '该股票已在监控列表中'})
    
    # 简化验证：只检查代码格式，不实时查询
    # 如果股票不存在，首页加载时会显示"未知"
    
    # 添加到列表
    WATCHED_STOCKS.append(code)
    
    # 保存到配置文件
    save_watchlist()
    
    return jsonify({
        'status': 'success',
        'message': f'成功添加 {code}（请刷新首页查看详情）',
        'data': {'code': code, 'name': '待加载'}
    })


@app.route('/api/watchlist/<code>', methods=['DELETE'])
@login_required
def api_remove_from_watchlist(code):
    """从监控列表移除股票"""
    if code not in WATCHED_STOCKS:
        return jsonify({'status': 'error', 'message': '该股票不在监控列表中'})
    
    WATCHED_STOCKS.remove(code)
    
    # 保存到配置文件
    save_watchlist()
    
    return jsonify({
        'status': 'success',
        'message': f'已移除 {code}'
    })


# 搜索缓存（内存缓存，避免重复请求）
_search_cache = {}
_search_cache_time = {}

@app.route('/api/stock/search')
@login_required
def api_search_stock():
    """搜索股票（带缓存）"""
    keyword = request.args.get('q', '').strip()
    
    if not keyword:
        return jsonify({'status': 'error', 'message': '搜索关键词不能为空'})
    
    # 检查缓存（5分钟有效）
    import time
    now = time.time()
    if keyword in _search_cache:
        cache_time = _search_cache_time.get(keyword, 0)
        if now - cache_time < 300:  # 5分钟内使用缓存
            return jsonify({
                'status': 'success',
                'data': _search_cache[keyword],
                'cached': True
            })
    
    try:
        import akshare as ak
        df = ak.stock_zh_a_spot_em()
        
        # 模糊搜索（代码或名称）
        mask = df['代码'].str.contains(keyword, na=False) | df['名称'].str.contains(keyword, na=False)
        results = df[mask].head(10)
        
        stocks = []
        for _, row in results.iterrows():
            stocks.append({
                'code': row['代码'],
                'name': row['名称'],
                'price': float(row['最新价']),
                'change_pct': float(row['涨跌幅'])
            })
        
        # 缓存结果
        _search_cache[keyword] = stocks
        _search_cache_time[keyword] = now
        
        return jsonify({
            'status': 'success',
            'data': stocks
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'搜索失败: {str(e)}'})


def save_watchlist():
    """保存监控列表到配置文件"""
    import os
    config_file = os.path.join(os.path.dirname(__file__), 'watchlist.json')
    
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(WATCHED_STOCKS, f, ensure_ascii=False, indent=2)


def save_users():
    """保存用户到配置文件"""
    import os
    config_file = os.path.join(os.path.dirname(__file__), 'users.json')
    
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(USERS, f, ensure_ascii=False, indent=2)


def load_watchlist():
    """从配置文件加载监控列表"""
    import os
    config_file = os.path.join(os.path.dirname(__file__), 'watchlist.json')
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                stocks = json.load(f)
                return stocks
        except:
            pass
    
    return None


# ============== 启动应用 ==============

@app.route('/api/users', methods=['GET'])
@login_required
def api_get_users():
    """获取用户列表"""
    if not current_user.can_manage_users():
        return jsonify({'status': 'error', 'message': '权限不足'}), 403
    
    users_list = []
    for username, data in USERS.items():
        users_list.append({
            'username': username,
            'role': data.get('role', 'viewer'),
            'role_name': ROLES.get(data.get('role', 'viewer'), {}).get('name', '未知')
        })
    
    return jsonify({
        'status': 'success',
        'data': users_list
    })


@app.route('/api/users', methods=['POST'])
@login_required
def api_create_user():
    """创建新用户"""
    if not current_user.can_manage_users():
        return jsonify({'status': 'error', 'message': '权限不足'}), 403
    
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    role = data.get('role', 'viewer')
    
    if not username or not password:
        return jsonify({'status': 'error', 'message': '用户名和密码不能为空'})
    
    if username in USERS:
        return jsonify({'status': 'error', 'message': '用户已存在'})
    
    if role not in ROLES:
        return jsonify({'status': 'error', 'message': '无效的角色'})
    
    # 创建用户
    new_id = max([u['id'] for u in USERS.values()]) + 1
    USERS[username] = {
        'password': hashlib.sha256(password.encode()).hexdigest(),
        'id': new_id,
        'role': role
    }
    
    # 保存到文件
    save_users()
    
    return jsonify({
        'status': 'success',
        'message': f'用户 {username} 创建成功'
    })


@app.route('/api/users/<username>', methods=['DELETE'])
@login_required
def api_delete_user(username):
    """删除用户"""
    if not current_user.can_delete():
        return jsonify({'status': 'error', 'message': '权限不足'}), 403
    
    if username not in USERS:
        return jsonify({'status': 'error', 'message': '用户不存在'})
    
    if username == 'admin':
        return jsonify({'status': 'error', 'message': '不能删除admin用户'})
    
    if username == current_user.username:
        return jsonify({'status': 'error', 'message': '不能删除自己'})
    
    del USERS[username]
    save_users()
    
    return jsonify({
        'status': 'success',
        'message': f'用户 {username} 已删除'
    })


@app.route('/api/change-password', methods=['POST'])
@login_required
def api_change_password():
    """修改密码"""
    data = request.json
    target_user = data.get('username', current_user.username)
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')
    confirm_password = data.get('confirm_password', '')
    
    # 权限检查
    if not current_user.can_change_password(target_user):
        return jsonify({'status': 'error', 'message': '权限不足'})
    
    # 验证新密码
    if not new_password:
        return jsonify({'status': 'error', 'message': '新密码不能为空'})
    
    if len(new_password) < 6:
        return jsonify({'status': 'error', 'message': '密码长度不能少于6位'})
    
    if new_password != confirm_password:
        return jsonify({'status': 'error', 'message': '两次输入的密码不一致'})
    
    # 修改自己的密码需要验证旧密码
    if target_user == current_user.username and not current_user.has_permission('change_all_passwords'):
        old_hash = hashlib.sha256(old_password.encode()).hexdigest()
        if old_hash != USERS[target_user]['password']:
            return jsonify({'status': 'error', 'message': '原密码错误'})
    
    # 修改密码
    if target_user not in USERS:
        return jsonify({'status': 'error', 'message': '用户不存在'})
    
    USERS[target_user]['password'] = hashlib.sha256(new_password.encode()).hexdigest()
    save_users()
    
    return jsonify({
        'status': 'success',
        'message': '密码修改成功'
    })


@app.route('/api/roles', methods=['GET'])
@login_required
def api_get_roles():
    """获取角色列表"""
    roles_list = []
    for role_id, role_data in ROLES.items():
        roles_list.append({
            'id': role_id,
            'name': role_data['name'],
            'permissions': role_data['permissions']
        })
    
    return jsonify({
        'status': 'success',
        'data': roles_list
    })


# ============== 中长线选股API ==============

@app.route('/long-term-select')
@login_required
def long_term_select_page():
    """中长线选股页面"""
    return render_template('long_term_select.html')


@app.route('/api/long-term-select', methods=['POST'])
@login_required
def api_long_term_select():
    """中长线选股API"""
    from long_term_selector import LongTermSelector
    
    data = request.json
    top_n = data.get('top_n', 5)
    
    try:
        selector = LongTermSelector()
        stocks = selector.select_top_stocks(top_n=top_n)
        selector.close()
        
        return jsonify({
            'status': 'success',
            'data': stocks
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })


@app.route('/api/long-term-report', methods=['POST'])
@login_required
def api_long_term_report():
    """生成中长线选股报告"""
    from long_term_selector import LongTermSelector
    
    data = request.json
    stocks = data.get('stocks', [])
    
    if not stocks:
        return jsonify({
            'status': 'error',
            'message': '无数据'
        })
    
    try:
        selector = LongTermSelector()
        report = selector.generate_report(stocks)
        selector.close()
        
        return jsonify({
            'status': 'success',
            'report': report
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })


# ============== 选股中心API (仅管理员) ==============

@app.route('/stock-selector')
@login_required
def stock_selector_page():
    """选股中心页面（仅管理员）"""
    if not current_user.can_manage_users():
        flash('仅管理员可访问选股中心', 'danger')
        return redirect('/')
    return render_template('stock_selector.html')


@app.route('/api/selector/run', methods=['POST'])
@login_required
def api_run_selector():
    """运行选股器（仅管理员）"""
    if not current_user.can_manage_users():
        return jsonify({
            'status': 'error',
            'message': '权限不足'
        }), 403
    
    data = request.json
    selector_type = data.get('type', 'long')  # short/long
    top_n = data.get('top_n', 5)
    
    try:
        if selector_type == 'short':
            from short_term_selector import ShortTermSelector
            selector = ShortTermSelector()
            stocks = selector.select_top_stocks(top_n=top_n)
            selector.close()
        else:
            from long_term_selector import LongTermSelector
            selector = LongTermSelector()
            stocks = selector.select_top_stocks(top_n=top_n)
            selector.close()
        
        return jsonify({
            'status': 'success',
            'data': stocks
        })
        
    except Exception as e:
        import traceback
        print(f"❌ 选股失败: {e}")
        print(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': str(e)
        })


@app.route('/api/selector/report', methods=['POST'])
@login_required
def api_get_selector_report():
    """获取选股报告（仅管理员）"""
    if not current_user.can_manage_users():
        return jsonify({
            'status': 'error',
            'message': '权限不足'
        }), 403
    
    data = request.json
    selector_type = data.get('type', 'long')
    stocks = data.get('stocks', [])
    
    if not stocks:
        return jsonify({
            'status': 'error',
            'message': '无数据'
        })
    
    try:
        if selector_type == 'short':
            from short_term_selector import ShortTermSelector
            selector = ShortTermSelector()
            report = selector.generate_report(stocks)
            selector.close()
        else:
            from long_term_selector import LongTermSelector
            selector = LongTermSelector()
            report = selector.generate_report(stocks)
            selector.close()
        
        return jsonify({
            'status': 'success',
            'report': report
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })


@app.route('/api/market/overview', methods=['GET'])
@login_required
def api_market_overview():
    """市场总览API"""
    try:
        from market_analysis import MarketAnalysis
        cache = StockCache()
        stocks = []
        for code in WATCHED_STOCKS:
            stock = cache.get_stock(code)
            if stock:
                stocks.append(stock)
        analyzer = MarketAnalysis()
        overview = analyzer.get_market_overview(stocks)
        cache.close()
        return jsonify({'status': 'success', 'data': overview})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/market/sentiment')
def api_market_sentiment():
    """全市场情绪API - 基于所有A股数据"""
    try:
        from market_sentiment import calculate_market_sentiment
        # 先尝试获取真实数据
        sentiment = calculate_market_sentiment(use_demo_data=False)
        # 如果没有有效数据，使用演示数据
        if sentiment['stats']['total'] == 0:
            sentiment = calculate_market_sentiment(use_demo_data=True)
            sentiment['demo_mode'] = True  # 标记为演示模式
        return jsonify({'status': 'success', 'data': sentiment})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)})


# ============== 增强版选股API ==============

@app.route('/api/enhanced-selector/run', methods=['POST'])
@login_required
def api_run_enhanced_selector():
    if not current_user.can_manage_users():
        return jsonify({'status': 'error', 'message': '权限不足'}), 403
    try:
        from enhanced_long_term_selector import EnhancedLongTermSelector
        selector = EnhancedLongTermSelector()
        stocks = selector.select_top_stocks(top_n=request.json.get('top_n', 5))
        selector.close()
        return jsonify({'status': 'success', 'data': stocks})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)})


if __name__ == '__main__':
    # 启动时加载监控列表
    saved_list = load_watchlist()
    if saved_list:
        WATCHED_STOCKS.clear()
        WATCHED_STOCKS.extend(saved_list)
        print(f"✅ 已加载 {len(WATCHED_STOCKS)} 只监控股票")
    
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║       📊 A股量化监控系统 Web界面                        ║
║                                                          ║
║       访问: http://localhost:5000                       ║
║       默认账号: admin / admin123                        ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
