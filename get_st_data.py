"""
股票数据获取模块
可被其他Python脚本导入使用
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import requests
import json
import time
import os

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def get_stock_data(
        key='',  # 默认使用你的API key
        codes='603978',
        period='1d',
        start_date='2025-03-23',
        end_date='2025-05-23',
        adjust='0',
        ty='个股',
        use_local=True,
        verbose=True
):
    """
    获取股票数据

    参数:
    - key: API密钥
    - codes: 股票代码
    - period: 周期
    - start_date: 开始日期
    - end_date: 结束日期
    - adjust: 复权类型
    - ty: 类型
    - use_local: 是否使用本地缓存
    - verbose: 是否打印详细信息

    返回:
    - 处理后的DataFrame
    """

    payload = {
        "key": key,
        "codes": codes,
        "period": period,
        "start_date": start_date,
        "end_date": end_date,
        "adjust": adjust,
        "ty": ty
    }

    csv_filename = f'stock_data_{codes}_{start_date}_to_{end_date}.csv'
    time1 = time.time()

    if use_local and os.path.exists(csv_filename):
        if verbose:
            print(f"使用本地数据: {csv_filename}")
        df = pd.read_csv(csv_filename, encoding='utf-8-sig')
    else:
        if verbose:
            print("从网络获取数据...")

        resp = requests.post(
            url='http://39.98.238.239/api_stock_kline_dc/',
            data=payload
        )

        # 解析响应
        data = resp.json()
        if not data['data']:
            if verbose:
                print("返回数据为空:", data)
            return None

        df = pd.DataFrame(data=data['data'], columns=data['columns'])

        # 保存为CSV文件
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        if verbose:
            print(f'数据已保存到: {csv_filename}')

    if verbose:
        print(f"共获取到 {len(df)} 条数据")
        print("\n数据前5行：")
        print(df.head())

    # 重命名列
    df.rename(columns={
        '日期': 'date',
        '代码': 'code',
        '开盘': 'open',
        '最高': 'high',
        '最低': 'low',
        '收盘': 'close',
        '成交额': 'volume'
    }, inplace=True)

    # 转换日期格式
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)

    return df


# 如果直接运行此脚本，执行示例代码
if __name__ == "__main__":
    # 使用示例
    print("直接运行股票数据获取脚本...")
    df = get_stock_data(
        codes='603978',
        start_date='2025-03-23',
        end_date='2025-05-23',
        use_local=True,
        verbose=True
    )

    if df is not None:
        print("\n数据处理完成！")
        print(f"数据形状: {df.shape}")
        print(f"列名: {list(df.columns)}")