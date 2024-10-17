

from typing import Union

from fastapi import FastAPI
import json
import os
from fastapi import FastAPI, Request, Body
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from qwen_agent.llm import get_chat_model
import json
from qwen_agent.llm import get_chat_model
from datetime import datetime, timedelta
import json
from datetime import datetime
import calendar
from fastapi import FastAPI

from pydantic import BaseModel
from typing import Optional, Dict, List





app = FastAPI()

def calc_base(fee_type_and_xinxi, range):
    # 检查输入数据类型
    if isinstance(fee_type_and_xinxi, str):
        try:
            # 尝试解析 JSON 数据
            fee_type_and_xinxi = json.loads(fee_type_and_xinxi)
            print("解析后的数据类型:", type(fee_type_and_xinxi))
            print("解析后的数据内容:", fee_type_and_xinxi)
        except json.JSONDecodeError as e:
            print(f"JSON 解析错误: {e}")
            return
    elif isinstance(fee_type_and_xinxi, dict):
        # 如果输入是字典，转换为包含该字典的列表
        fee_type_and_xinxi = [fee_type_and_xinxi]
        print("输入数据是字典，已转换为列表。")
    elif not isinstance(fee_type_and_xinxi, list):
        print("错误：输入数据类型不正确，期望为字符串、字典或列表。", 'type(fee_type_and_xinxi):', type(fee_type_and_xinxi), 'fee_type_and_xinxi:', fee_type_and_xinxi)
        return
    
    # 继续处理数据
    print("处理的数据类型:", type(fee_type_and_xinxi))
    print("处理的数据内容:", fee_type_and_xinxi)

    # 初始化 xinxis 列表
    xinxis = []

    # 存储结果计算过程
    result = {}
    # 存储计算结果
    final_result = {}
    # 判断数据是否存储全
    Missing_data = {}

    # 将输入数据添加到 xinxis 列表中
    for fee_info in fee_type_and_xinxi:
        if isinstance(fee_info, dict):
            xinxis.append(fee_info)
        else:
            print("错误：fee_info 必须是字典，当前类型:", type(fee_info))

    # 检查时间范围
    if range is None:
        print("错误：时间范围不能为空")
        return

    # 获取起始日期和结束日期
    start_day_str = range.get('start_day', '20230501')  # 默认值
    end_day_str = range.get('end_day', '20230601')  
    monthly_cutoff_date = range.get('monthly_cutoff_day')    # 默认值

    # 检查是否为 None
    if start_day_str is None or end_day_str is None:
        print("错误：起始日期或结束日期不能为空")
        start_day_str = '20230501' # 默认值
        end_day_str = '20230601'
        print('该值为第一个位start,第二个为end',start_day_str,end_day_str)

    # 将日期字符串转换为 datetime 对象
    start_date = datetime.strptime(start_day_str, '%Y%m%d')
    end_date = datetime.strptime(end_day_str, '%Y%m%d')

    if monthly_cutoff_date is not None:
        rangeresult = []
        current_date = start_date

        while current_date <= end_date:
            # 获取当前日期的年月日
            start_period = current_date.strftime('%Y%m%d')

            # 计算当月的基准日
            if current_date.day <= monthly_cutoff_date:
                cutoff_day_this_month = datetime(current_date.year, current_date.month, monthly_cutoff_date)
            else:
                # 如果当前日期已经超过本月的基准日，设置为下个月的基准日
                if current_date.month == 12:
                    cutoff_day_this_month = datetime(current_date.year + 1, 1, monthly_cutoff_date)
                else:
                    cutoff_day_this_month = datetime(current_date.year, current_date.month + 1, monthly_cutoff_date)

            # 确定下一个基准日，作为统计周期的结束日期
            next_cutoff_date = min(cutoff_day_this_month, end_date)

            # 计算当前时间段的天数
            days_in_period = (next_cutoff_date - current_date).days + 1

            # 获取该段结束的年月日
            end_period = next_cutoff_date.strftime('%Y%m%d')
            current_date = next_cutoff_date + timedelta(days=1)
            rangeresult.append({
            "start": start_period,
            "end": end_period,
            "days": days_in_period
        })
    else:

        rangeresult = []
        current_date = start_date

        while current_date <= end_date:
            # 获取当前日期的年月日
            start_period = current_date.strftime('%Y%m%d')

            # 获取当月的最后一天
            last_day_of_month = calendar.monthrange(current_date.year, current_date.month)[1]
            month_end_date = datetime(current_date.year, current_date.month, last_day_of_month)

            # 确定这个时间段的结束日期，不能超过截止日期
            end_of_period = min(month_end_date, end_date)

            # 计算这个时间段的天数
            days_in_period = (end_of_period - current_date).days + 1

            # 获取该段的结束日期
            end_period = end_of_period.strftime('%Y%m%d')

            # 将结果添加到列表中
            rangeresult.append({
                "start": start_period,
                "end": end_period,
                "days": days_in_period
            })

            # 更新当前日期为下个月的第一天
            current_date = end_of_period + timedelta(days=1)


        # 根据月份确定天数
        if start_date.month in [1, 3, 5, 7, 8, 10, 12]:
            days_in_month = 31
        elif start_date.month in [4, 6, 9, 11]:
            days_in_month = 30
        else:
            days_in_month = 29 if (start_date.year % 4 == 0 and start_date.year % 100 != 0) or (start_date.year % 400 == 0) else 28

# 结果变量聚集地
    total_electricity_fee_end_of_month = 0
    total_electricity_fee_to_yingbu = 0
    total_electricity_fee_to_add = 0
    yingtui_elect = 0.0
    error_reading_fee = 0.0
    elect_litiao = 0.0
    elcfee_ero_tb = 0.0
    elc_yingbu = 0.0
    elcfee_yingbu = 0.0
    gl_P1 = 0.0
    gl_P2 = 0.0
    error_current_transformer_yingbu_elc = 0.0
    sys_chang_fee = 0.0
    ero_meter_duo = 0.0
    loss_33yb = 0.0
    jf_33yb = 0.0
    electricity_fee = 0.0
    # ------------------------------------参数变量
    apparent_power = 0
    date = 20230314  # 可以保持原值，如果需要也可以设置为 0
    actual_reading = 0
    previous_reading = 0
    base_price = 0
    max_demand = 0
    private_enddate_byq = None  # 保持原值
    active_power = 0
    reactive_power = 0
    power_adjustment_fee = 0
    unit_price = 0
    unit_jiben = 0
    error_reading = 0
    glys = 0
    error_glys = 0
    glysxs = 0
    error_elc_fee = 0
    elc_use = 0
    elc_error_percentage = 0
    current_ratio_A = 0
    current_ratio_B = 0
    current_ratio_C = 0
    elc_error_meas = 0
    error_sys_elcfee = 0
    elc_SjuseK = 0
    meter_Speed_ero = 0
    elc_33JfuseK = 0
    Data_judgment = 0

    for xinxi in xinxis:
        print("xinxis长什么样：", xinxis,'range内容是：',range)  # 打印 xinxis 的内容

        if xinxi['type'] == 'normal_byq':
            # 获取参数
            apparent_power = float(xinxi.get('apparent_power', 0) or 0)
            unit = float(xinxi.get('unit_jiben', 0) or 0)
            base_price = float(xinxi.get('base_price', 0) or 0)

            # 初始化缺少的参数列表
            Missing_data = []

            # 参数名称与中文含义的映射
            param_translation = {
                "apparent_power": "视在功率",
                "unit_jiben": "度数",
                "base_price": "基本电价"
            }

            # 检查哪些参数为 0 并记录到 Missing_data
            if apparent_power == 0:
                Missing_data.append('apparent_power')
            if unit == 0:
                Missing_data.append('unit_jiben')
            if base_price == 0:
                Missing_data.append('base_price')

            # 判断是否有缺少的参数
            if not Missing_data:  # 如果 Missing_data 为空，说明所有参数都不为 0
                Data_judgment = 0  # 参数齐全
                electricity_fee = apparent_power * unit * base_price  # 假设这里的乘法是简化计算

                # 计算过程
                result['electricity_fee'] = f"计算过程：视在功率: {apparent_power} * 电价: {base_price} * 度数: {unit} = 正常变压器所缴纳电费: {electricity_fee}"

                # 最终结果
                final_result['electricity_fee'] = {
                    "Data_judgment": Data_judgment,
                    "final_result": electricity_fee,
                    "result": result['electricity_fee']
                }

            else:  # 有缺少的参数
                Data_judgment = 1  # 参数不全

                # 将缺少的参数翻译成中文
                missing_params_in_chinese = [param_translation.get(param, param) for param in Missing_data]

                result['electricity_fee'] = f"参数不全，无法进行电费的计算，缺少的参数有: {', '.join(missing_params_in_chinese)}"

                # 最终结果
                final_result['electricity_fee'] = {
                    "Data_judgment": Data_judgment,
                    "final_result": None,
                    "result": result['electricity_fee'],
                    "Missing_data": missing_params_in_chinese  # 缺少的参数（中文）
                }




        
        if xinxi['type'] == 'volume_reduction_byq':
            # 获取参数
            apparent_power = float(xinxi.get('apparent_power', 0) or 0)
            volume_reduction_date = xinxi.get('date', None)
            base_price = float(xinxi.get('base_price', 0))
            max_demand = float(xinxi.get('max_demand', 0))
            # unit = float(xinxi.get('unit_jiben', 0) or 0)  
            
            # 初始化缺少的参数列表
            Missing_data = []
            
            # 检查哪些参数为 0 并记录到 Missing_data
            if apparent_power == 0:
                Missing_data.append('视在功率 (apparent_power)')
            if volume_reduction_date is None:
                Missing_data.append('减容日期 (date)')
            if base_price == 0:
                Missing_data.append('基本电价 (base_price)')
            if max_demand == 0:
                Missing_data.append('最大需量 (max_demand)')
            # if unit == 0:
            #     Missing_data.append('基本电价单位 (unit_jiben)')

            # 判断是否有缺少的参数
            if not Missing_data:  # 如果 Missing_data 为空，说明所有参数都不为 0
                Data_judgment = 0  # 参数齐全
                change_date = datetime.strptime(volume_reduction_date, '%Y%m%d')
                days_no_use = (end_date - change_date).days

                # 计算补缴费用
                total_electricity_fee_to_yingbu = (days_no_use / 30) * base_price * apparent_power

                # 计算过程
                result['total_electricity_fee_to_yingbu'] = (
                    f"视在功率: {apparent_power} * 电价: {base_price} * (没有使用的天数 {days_no_use} / 每个月天数 {30}) = 补缴费用: {total_electricity_fee_to_yingbu}"
                )

                # 最终结果
                final_result['total_electricity_fee_to_yingbu'] = {
                    "Data_judgment": Data_judgment,
                    "final_result": total_electricity_fee_to_yingbu,
                    "result": result['total_electricity_fee_to_yingbu']
                }

            else:  # 有缺少的参数
                Data_judgment = 1  # 参数不全
                result['total_electricity_fee_to_yingbu'] = (
                    f"参数不全，无法进行补缴费用的计算，缺少的参数有: {', '.join(Missing_data)}"
                )

                # 最终结果
                final_result['total_electricity_fee_to_yingbu'] = {
                    "Data_judgment": Data_judgment,
                    "final_result": None,
                    "result": result['total_electricity_fee_to_yingbu'],
                    "Missing_data": Missing_data  # 缺少的参数
                }




        # 私增变压器补交钱的情况
        if xinxi['type'] == 'private_addivate_byq':
            # 获取参数
            apparent_power = float(xinxi.get('apparent_power', 0) or 0)
            private_addivate_date = xinxi.get('date', None)
            base_price = float(xinxi.get('base_price', 0))
            private_enddate_byq = xinxi.get('private_enddate_byq', None)
            
            # 初始化缺少的参数列表
            Missing_data = []
            
            # 检查哪些参数为 0 或 None，并记录到 Missing_data
            if apparent_power == 0:
                Missing_data.append('视在功率 (apparent_power)')
            if private_addivate_date is None:
                Missing_data.append('私增日期 (private_addivate_date)')
            if base_price == 0:
                Missing_data.append('基本电价 (base_price)')
            if private_enddate_byq is None:
                Missing_data.append('私增变压器结束日期 (private_enddate_byq)')

            # 判断是否有缺少的参数
            if not Missing_data:  # 如果 Missing_data 为空，说明所有参数都不为 0 或 None
                Data_judgment = 0  # 参数齐全

                # 将日期字符串转换为 datetime 对象
                private_enddate_byq = datetime.strptime(private_enddate_byq, '%Y%m%d')
                private_addition_date = datetime.strptime(private_addivate_date, '%Y%m%d')

                # 计算使用天数
                days_in_use = (private_enddate_byq - private_addition_date).days
                
                # 计算私增变压器补缴费用
                electricity_fee_private_addition = (apparent_power * (days_in_use / 30)) * base_price
                total_electricity_fee_to_add += electricity_fee_private_addition

                # 计算过程
                result["total_electricity_fee_to_add"] = (
                    f"私增变压器补交钱计算过程: 视在功率: {apparent_power} * 使用期间的天数: {days_in_use} * 电价: {base_price} = 补缴的费用: {total_electricity_fee_to_add}"
                )

                # 最终结果
                final_result["total_electricity_fee_to_add"] = {
                    "Data_judgment": Data_judgment,
                    "final_result": total_electricity_fee_to_add,
                    "result": result["total_electricity_fee_to_add"]
                }

            else:  # 有缺少的参数
                Data_judgment = 1  # 参数不全

                # 输出缺少参数的提示
                result["total_electricity_fee_to_add"] = (
                    f"参数不全，无法进行补缴费用的计算，缺少的参数有: {', '.join(Missing_data)}"
                )

                # 最终结果
                final_result["total_electricity_fee_to_add"] = {
                    "Data_judgment": Data_judgment,
                    "final_result": None,
                    "result": result["total_electricity_fee_to_add"],
                    "Missing_data": Missing_data  # 缺少的参数
                }


        # 读表错误
        if xinxi['type'] == 'reading_error':  
            # 获取参数
            actual_reading = xinxi.get('actual_reading', 0)
            previous_reading = xinxi.get('previous_reading', 0)
            base_price = xinxi.get('base_price', 0)
            error_reading = xinxi.get('error_reading', 0)
            
            # 初始化缺少的参数列表
            Missing_data = []

            # 检查哪些参数为 0，并记录到 Missing_data
            if actual_reading == 0:
                Missing_data.append('实际读数 (actual_reading)')
            if previous_reading == 0:
                Missing_data.append('上月读数 (previous_reading)')
            if base_price == 0:
                Missing_data.append('基本电价 (base_price)')
            if error_reading == 0:
                Missing_data.append('抄错读数 (error_reading)')

            # 判断是否有缺少的参数
            if not Missing_data:  # 如果 Missing_data 为空，说明所有参数都不为 0
                Data_judgment = 0  # 参数齐全

                # 计算应退电量和错误读数电费
                yingtui_elect = error_reading - actual_reading
                error_reading_fee = yingtui_elect * base_price + 60  # 60 为增电费题目未给的常量

                # 计算过程
                result['error_reading_fee'] = (
                    f"读表错误电费计算: (读表错误的值: {error_reading} - 实际的表值: {actual_reading}) * 电费单价: {base_price} + 60 (增电费) = 补缴的钱: {error_reading_fee}"
                )

                # 最终结果
                final_result['error_reading_fee'] = {
                    "Data_judgment": Data_judgment,
                    "final_result": error_reading_fee,
                    "result": result['error_reading_fee']
                }

            else:  # 有缺少的参数
                Data_judgment = 1  # 参数不全

                # 输出缺少参数的提示
                result['error_reading_fee'] = (
                    f"参数不全，无法进行补缴费用的计算，缺少的参数有: {', '.join(Missing_data)}"
                )

                # 最终结果
                final_result['error_reading_fee'] = {
                    "Data_judgment": Data_judgment,
                    "final_result": None,
                    "result": result['error_reading_fee'],
                    "Missing_data": Missing_data  # 缺少的参数
                }



        #力调电费 
        if xinxi['type'] == 'litiao_elect':
            # 获取参数
            glys = xinxi.get('glys', 0)
            error_glys = xinxi.get('error_glys', 0)
            glysxs = xinxi.get('glysxs', 0)
            active_power = xinxi.get('active_power', 0)
            reactive_power = xinxi.get('reactive_power', 0)
            power_adjustment_fee = xinxi.get('power_adjustment_fee', 0)

            # 初始化缺少的参数列表
            Missing_data = []

            # 检查哪些参数为 0，并记录到 Missing_data
            if glys == 0:
                Missing_data.append('功率因数 (glys)')
            if error_glys == 0:
                Missing_data.append('错误的功率因数 (error_glys)')
            if glysxs == 0:
                Missing_data.append('功率因数调整系数 (glysxs)')
            if active_power == 0:
                Missing_data.append('有功功率 (active_power)')
            if reactive_power == 0:
                Missing_data.append('无功功率 (reactive_power)')
            if power_adjustment_fee == 0:
                Missing_data.append('力调电费 (power_adjustment_fee)')

            # 判断是否有缺少的参数
            if not Missing_data:  # 如果 Missing_data 为空，说明所有参数都不为 0
                Data_judgment = 0  # 参数齐全

                # 力调电费计算
                elect_litiao = power_adjustment_fee - (active_power * (power_adjustment_fee / 1000)) * glysxs

                # 计算过程
                result['elect_litiao'] = (
                    f"力调电量计算: 力调电费的基础费用: {power_adjustment_fee} - (有功功率: {active_power} * (力调电费费用/1000): {power_adjustment_fee / 1000}) * 功率因数调整系数: {glysxs} = 退补费用: {elect_litiao}"
                )

                # 最终结果
                final_result['elect_litiao'] = {
                    "Data_judgment": Data_judgment,
                    "final_result": elect_litiao,
                    "result": result['elect_litiao']
                }

            else:  # 有缺少的参数
                Data_judgment = 1  # 参数不全

                # 输出缺少参数的提示
                result['elect_litiao'] = (
                    f"参数不全，无法进行力调费用的计算，缺少的参数有: {', '.join(Missing_data)}"
                )

                # 最终结果
                final_result['elect_litiao'] = {
                    "Data_judgment": Data_judgment,
                    "final_result": None,
                    "result": result['elect_litiao'],
                    "Missing_data": Missing_data  # 缺少的参数
                }






        # 电费单价错误类型
        if xinxi['type'] == 'error_elcfee':
            # 获取参数
            error_elc_fee = float(xinxi.get('error_elc_fee', 0) or 0)
            elc_use = float(xinxi.get('elc_use', 0) or 0)
            base_price = float(xinxi.get('base_price', 0) or 0)
            unit_price = float(xinxi.get('unit_price', 0) or 0)

            # 初始化缺少的参数列表
            Missing_data = []

            # 检查哪些参数为 0，并记录到 Missing_data
            if error_elc_fee == 0:
                Missing_data.append('错误的电费单价 (error_elc_fee)')
            if elc_use == 0:
                Missing_data.append('电量使用值 (elc_use)')
            if base_price == 0:
                Missing_data.append('基础电费 (base_price)')
            if unit_price == 0:
                Missing_data.append('电费单价 (unit_price)')

            # 判断是否有缺少的参数
            if not Missing_data:  # 如果 Missing_data 为空，说明所有参数都不为 0
                Data_judgment = 0  # 参数齐全

                # 计算电费单价错误的退补费用
                elcfee_ero_tb = -elc_use * (unit_price - error_elc_fee)

                # 计算过程
                result['elcfee_ero_tb'] = (
                    f"电费单价错误计算过程: 电量: {elc_use} * (基础电费: {unit_price} - 错误的电量费用: {error_elc_fee}) = 退补费用: {elcfee_ero_tb}"
                )

                # 最终结果
                final_result['elcfee_ero_tb'] = {
                    "Data_judgment": Data_judgment,
                    "final_result": elcfee_ero_tb,
                    "result": result['elcfee_ero_tb']
                }

            else:  # 有缺少的参数
                Data_judgment = 1  # 参数不全

                # 输出缺少参数的提示
                result['elcfee_ero_tb'] = (
                    f"参数不全，无法进行电费单价错误计算，缺少的参数有: {', '.join(Missing_data)}"
                )

                # 最终结果
                final_result['elcfee_ero_tb'] = {
                    "Data_judgment": Data_judgment,
                    "final_result": None,
                    "result": result['elcfee_ero_tb'],
                    "Missing_data": Missing_data  # 缺少的参数
                }





        # 表计错误快慢类型
        if xinxi['type'] == 'error_meter_man':
            # 获取参数
            meter_Speed_ero = float(xinxi.get('meter_Speed_ero', 0) or 0)
            elc_use = float(xinxi.get('elc_use', 0) or 0)

            # 初始化缺少的参数列表
            Missing_data = []

            # 检查哪些参数为 0，并记录到 Missing_data
            if meter_Speed_ero == 0:
                Missing_data.append('电表速度误差 (meter_Speed_ero)')
            if elc_use == 0:
                Missing_data.append('电量使用值 (elc_use)')

            # 判断是否有缺少的参数
            if not Missing_data:  # 如果 Missing_data 为空，说明所有参数都不为 0
                Data_judgment = 0  # 参数齐全

                # 计算退补电量
                elc_yingbu = (elc_use * meter_Speed_ero) / (1 + meter_Speed_ero)

                # 计算过程
                result['elc_yingbu'] = (
                    f"计算过程: (使用的电量: {elc_use} * 电表的速度误差: {meter_Speed_ero}) / (1 + 电表的速度误差: {meter_Speed_ero}) = 退补电量: {elc_yingbu}"
                )

                # 最终结果
                final_result['elc_yingbu'] = {
                    "Data_judgment": Data_judgment,
                    "final_result": elc_yingbu,
                    "result": result['elc_yingbu']
                }

            else:  # 有缺少的参数
                Data_judgment = 1  # 参数不全

                # 输出缺少参数的提示
                result['elc_yingbu'] = (
                    f"参数不全，无法进行电表速度误差的退补电量计算，缺少的参数有: {', '.join(Missing_data)}"
                )

                # 最终结果
                final_result['elc_yingbu'] = {
                    "Data_judgment": Data_judgment,
                    "final_result": None,
                    "result": result['elc_yingbu'],
                    "Missing_data": Missing_data  # 缺少的参数
                }




#           'type':"error_meter_man"的时候参数需要json列表中的，"elc_error_percentage","elc_use";代入到方法中计算

        # 表计算错误多少类型，多计量8%或少计量8%
        if xinxi['type'] == 'error_meter_duo':
            # 获取参数
            elc_error_percentage = float(xinxi.get('elc_error_percentage', 0) or 0)
            elc_use = float(xinxi.get('elc_use', 0) or 0)
            base_price = float(xinxi.get('base_price', 0) or 0)

            # 初始化缺少的参数列表
            Missing_data = []

            # 检查哪些参数为 0，并记录到 Missing_data
            if elc_error_percentage == 0:
                Missing_data.append('电量误差百分比 (elc_error_percentage)')
            if elc_use == 0:
                Missing_data.append('电量使用值 (elc_use)')
            if base_price == 0:
                Missing_data.append('基础电费 (base_price)')

            # 判断是否有缺少的参数
            if not Missing_data:  # 如果 Missing_data 为空，说明所有参数都不为 0
                Data_judgment = 0  # 参数齐全

                # 根据计量误差的正负计算退补电量
                if elc_error_percentage >= 0:
                    elc_yingbu = elc_use * (1 + elc_error_percentage) - elc_use
                else:
                    elc_yingbu = elc_use * (-elc_error_percentage)

                # 计算退补费用
                ero_meter_duo = elc_yingbu * base_price

                # 计算过程
                result['ero_meter_duo'] = (
                    f"计算过程: 使用的电量: {elc_use}, 计量误差: {elc_error_percentage} = 退补费用: {ero_meter_duo}"
                )

                # 最终结果
                final_result['ero_meter_duo'] = {
                    "Data_judgment": Data_judgment,
                    "final_result": ero_meter_duo,
                    "result": result['ero_meter_duo']
                }

            else:  # 有缺少的参数
                Data_judgment = 1  # 参数不全

                # 输出缺少参数的提示
                result['ero_meter_duo'] = (
                    f"参数不全，无法进行计量误差的退补费用计算，缺少的参数有: {', '.join(Missing_data)}"
                )

                # 最终结果
                final_result['ero_meter_duo'] = {
                    "Data_judgment": Data_judgment,
                    "final_result": None,
                    "result": result['ero_meter_duo'],
                    "Missing_data": Missing_data  # 缺少的参数
                }



        # 三相四线退补电费问题
        if xinxi['type'] == 'error_current_transformer34':
            # 获取参数
            current_ratio_A = float(xinxi.get('current_ratio_A', 0) or 0)
            current_ratio_B = float(xinxi.get('current_ratio_B', 0) or 0)
            current_ratio_C = float(xinxi.get('current_ratio_C', 0) or 0)
            elc_use = float(xinxi.get('elc_use', 0) or 0)

            # 初始化缺少的参数列表
            Missing_data = []

            # 检查哪些参数为 0，并记录到 Missing_data
            if current_ratio_A == 0:
                Missing_data.append('相 A 电流互感器比率 (current_ratio_A)')
            if current_ratio_B == 0:
                Missing_data.append('相 B 电流互感器比率 (current_ratio_B)')
            if current_ratio_C == 0:
                Missing_data.append('相 C 电流互感器比率 (current_ratio_C)')
            if elc_use == 0:
                Missing_data.append('电量使用值 (elc_use)')

            # 判断是否有缺少的参数
            if not Missing_data:  # 如果 Missing_data 为空，说明所有参数都不为 0
                Data_judgment = 0  # 参数齐全

                # 计算正确接线时的功率 P1 和错误接线时的功率 P2
                gl_P1 = 3 * (1 / current_ratio_A)
                gl_P2 = (1 / current_ratio_A) + (1 / current_ratio_B) - (1 / current_ratio_C)

                # 计算更正系数 K 和更正率 Gz_lv
                Gz_K = gl_P1 / gl_P2
                Gz_lv = Gz_K - 1

                # 计算退补电量
                error_current_transformer_yingbu_elc = Gz_lv * elc_use

                # 计算过程
                result['error_current_transformer_yingbu_elc'] = (
                    f"计算过程: 正确接线功率: {gl_P1} / 错误接线功率: {gl_P2} - 1 * 用电量: {elc_use} = 退补电量: {error_current_transformer_yingbu_elc}"
                )

                # 最终结果
                final_result['error_current_transformer_yingbu_elc'] = {
                    "Data_judgment": Data_judgment,
                    "final_result": error_current_transformer_yingbu_elc,
                    "result": result['error_current_transformer_yingbu_elc']
                }

            else:  # 有缺少的参数
                Data_judgment = 1  # 参数不全

                # 输出缺少参数的提示
                result['error_current_transformer_yingbu_elc'] = (
                    f"参数不全，无法进行电流互感器的退补费用计算，缺少的参数有: {', '.join(Missing_data)}"
                )

                # 最终结果
                final_result['error_current_transformer_yingbu_elc'] = {
                    "Data_judgment": Data_judgment,
                    "final_result": None,
                    "result": result['error_current_transformer_yingbu_elc'],
                    "Missing_data": Missing_data  # 缺少的参数
                }



        # 系统计算错误问题   "type":"sys_error_elcfee"的时候参数需要json列表中的,"error_sys_elcfee","elc_use","unit_price";代入到方法中计算
        if xinxi['type'] == 'sys_error_elcfee':
            # 获取参数
            error_sys_elcfee = float(xinxi.get('error_sys_elcfee', 0) or 0)
            elc_use = float(xinxi.get('elc_use', 0) or 0)
            base_price = float(xinxi.get('base_price', 0) or 0)

            # 初始化缺少的参数列表
            Missing_data = []

            # 检查哪些参数为 0，并记录到 Missing_data
            if error_sys_elcfee == 0:
                Missing_data.append('系统计算错误电费 (error_sys_elcfee)')
            if elc_use == 0:
                Missing_data.append('电量使用值 (elc_use)')
            if base_price == 0:
                Missing_data.append('电费单价 (base_price)')

            # 判断是否有缺少的参数
            if not Missing_data:  # 如果 Missing_data 为空，说明所有参数都不为 0
                Data_judgment = 0  # 参数齐全

                # 计算退补电费
                sys_chang_fee = elc_use * base_price - error_sys_elcfee

                # 计算过程
                result['sys_chang_fee'] = (
                    f"计算过程: 使用电量: {elc_use} * 电费单价: {base_price} - 系统计算的错误电费: {error_sys_elcfee} = 退补费用: {sys_chang_fee}"
                )

                # 最终结果
                final_result['sys_chang_fee'] = {
                    "Data_judgment": Data_judgment,
                    "final_result": sys_chang_fee,
                    "result": result['sys_chang_fee']
                }

            else:  # 有缺少的参数
                Data_judgment = 1  # 参数不全

                # 输出缺少参数的提示
                result['sys_chang_fee'] = (
                    f"参数不全，无法进行系统错误电费退补计算，缺少的参数有: {', '.join(Missing_data)}"
                )

                # 最终结果
                final_result['sys_chang_fee'] = {
                    "Data_judgment": Data_judgment,
                    "final_result": None,
                    "result": result['sys_chang_fee'],
                    "Missing_data": Missing_data  # 缺少的参数
                }




        # 三相三线缺相情况
        if xinxi['type'] == 'error_voltage_loss33':
            # 获取参数
            elc_use = float(xinxi.get('elc_use', 0) or 0)
            current_ratio_A = float(xinxi.get('current_ratio_A', 0) or 0)
            current_ratio_B = float(xinxi.get('current_ratio_B', 0) or 0)
            current_ratio_C = float(xinxi.get('current_ratio_C', 0) or 0)
            elc_SjuseK = float(xinxi.get('elc_SjuseK', 0) or 0)
            base_price = float(xinxi.get('base_price', 0) or 0)

            # 初始化缺少的参数列表
            Missing_data = []

            # 检查哪些参数为 0，并记录到 Missing_data
            if elc_use == 0:
                Missing_data.append('电量使用值 (elc_use)')
            if current_ratio_A == 0:
                Missing_data.append('相A电流变比 (current_ratio_A)')
            if current_ratio_B == 0:
                Missing_data.append('相B电流变比 (current_ratio_B)')
            if current_ratio_C == 0:
                Missing_data.append('相C电流变比 (current_ratio_C)')
            if elc_SjuseK == 0:
                Missing_data.append('电量调整系数 (elc_SjuseK)')
            if base_price == 0:
                Missing_data.append('电费单价 (base_price)')

            # 判断是否有缺少的参数
            if not Missing_data:  # 如果 Missing_data 为空，说明所有参数都不为 0
                Data_judgment = 0  # 参数齐全

                # 计算退补电费
                loss_33yb = elc_use * base_price - ((elc_use * elc_SjuseK) * base_price)

                # 计算过程
                result['loss_33yb'] = (
                    f"计算过程: 使用电量: {elc_use} * 电费单价: {base_price} - (使用电量: {elc_use} * 系数K: {elc_SjuseK}) * 电费单价: {base_price} = 退补费用: {loss_33yb}"
                )

                # 最终结果
                final_result['loss_33yb'] = {
                    "Data_judgment": Data_judgment,
                    "final_result": loss_33yb,
                    "result": result['loss_33yb']
                }

            else:  # 有缺少的参数
                Data_judgment = 1  # 参数不全

                # 输出缺少参数的提示
                result['loss_33yb'] = (
                    f"参数不全，无法进行电压损耗退补计算，缺少的参数有: {', '.join(Missing_data)}"
                )

                # 最终结果
                final_result['loss_33yb'] = {
                    "Data_judgment": Data_judgment,
                    "final_result": None,
                    "result": result['loss_33yb'],
                    "Missing_data": Missing_data  # 缺少的参数
                }






        # "type":"error_voltage_fx33"的时候需要json列表中的,"elc_use","base_price","elc_33JfuseK";代入到方法中计算。三相三线电流接反电费退补计算示例
        if xinxi['type'] == 'error_voltage_fx33':
            # 获取参数
            elc_use = float(xinxi.get('elc_use', 0) or 0)
            unit_price = float(xinxi.get('unit_price', 0) or 0)
            elc_33JfuseK = float(xinxi.get('elc_33JfuseK', 0) or 0)

            # 初始化缺少的参数列表
            Missing_data = []

            # 检查哪些参数为 0，并记录到 Missing_data
            if elc_use == 0:
                Missing_data.append('电量使用值 (elc_use)')
            if unit_price == 0:
                Missing_data.append('电费单价 (unit_price)')
            if elc_33JfuseK == 0:
                Missing_data.append('电压计费系数K (elc_33JfuseK)')

            # 判断是否有缺少的参数
            if not Missing_data:  # 如果 Missing_data 为空，说明所有参数都不为 0
                Data_judgment = 0  # 参数齐全

                # 计算计费单价退补
                jf_33yb = (elc_use * unit_price) - ((elc_use / (1 + elc_33JfuseK)) * unit_price)

                # 保证退补费用为正数
                jf_33yb = abs(jf_33yb)

                # 计算过程
                result['jf_33yb'] = (
                    f"计算过程: 电量: {elc_use} * 电费单价: {unit_price} - ((使用电量: {elc_use} / (1 + 系数K: {elc_33JfuseK})) * 单价: {unit_price}) = 计费单价退补: {jf_33yb}"
                )

                # 最终结果
                final_result['jf_33yb'] = {
                    "Data_judgment": Data_judgment,
                    "final_result": jf_33yb,
                    "result": result['jf_33yb']
                }

            else:  # 有缺少的参数
                Data_judgment = 1  # 参数不全

                # 输出缺少参数的提示
                result['jf_33yb'] = (
                    f"参数不全，无法进行电压计费退补计算，缺少的参数有: {', '.join(Missing_data)}"
                )

                # 最终结果
                final_result['jf_33yb'] = {
                    "Data_judgment": Data_judgment,
                    "final_result": None,
                    "result": result['jf_33yb'],
                    "Missing_data": Missing_data  # 缺少的参数
                }



    # Calculation_process = {
    #     "electricity_fee": f"计算过程：视在功率: {apparent_power} * 电价: {base_price} = 正常变压器所缴纳电费: {electricity_fee}",
    #     "total_electricity_fee_to_yingbu": f"变压器减容电费计算过程: 视在功率: {apparent_power} * 电价: {base_price} * (具体使用时间 / 每个月天数) = 补缴费用: {total_electricity_fee_to_yingbu}",
    #     "total_electricity_fee_to_add": f"私增变压器补交钱计算过程: 视在功率: {apparent_power} * 使用期间的天数 * 电价: {base_price} = 补缴的费用: {total_electricity_fee_to_add}",
    #     "error_reading_fee": f"读表错误电费计算: (读表错误的值: {error_reading} - 实际的表值: {actual_reading}) * 电费单价: {base_price} + 60 (题目给定数，暂未详情设置) = 补缴的钱: {error_reading_fee}",
    #     "elect_litiao": f"力调电量计算: 力调电费的基础费用: {power_adjustment_fee} - (有功功率: {active_power} * (力调电费费用/1000) {power_adjustment_fee / 1000}) * 功率因数调整系数: {glysxs} = 退补费用: {elect_litiao}",
    #     "elcfee_ero_tb": f"电费单价错误计算过程: 电量: {elc_use} * (基础电费 - 错误的电量费用): {unit_price - error_elc_fee} = 退补费用: {elcfee_ero_tb}",
    #     "elc_yingbu": f"计算过程: (使用的电量: {elc_use} * 电表的速度误差: {meter_Speed_ero}) / (1 + 电表的速度误差: {meter_Speed_ero}) = 退补费用: {elc_yingbu}",
    #     "error_current_transformer_yingbu_elc": f"计算过程: 正确接线功率: {gl_P1} / 错误接线功率: {gl_P2} - 1 * 用电量: {elc_use} = 退补费用: {error_current_transformer_yingbu_elc}",
    #     "sys_chang_fee": f"计算过程: 使用电量: {elc_use} * 电费单价: {base_price} - 系统计算的错误电费: {error_sys_elcfee} = 退补费用: {sys_chang_fee}",
    #     "ero_meter_duo": f"计算过程: elc_use: {elc_use}, 计量误差: {elc_error_percentage} = 退补费用: {ero_meter_duo}",
    #     "loss_33yb": f"计算过程: 使用的电量: {elc_use} * 电费单价: {base_price} - (使用电量: {elc_use} * 系数K: {elc_SjuseK}) * 电费电价: {base_price} = 退补费用: {loss_33yb}",
    #     "jf_33yb": f"计算过程: 电量: {elc_use} * 电费电价: {unit_price} - ((使用电量: {elc_use} / (1 + 系数K: {elc_33JfuseK})) * 单价: {unit_price}) = 计费单价退补: {jf_33yb}"
    # }




    return final_result

class Chattest(BaseModel):
    content: str
    role: str = "user"


    
def convert_messages_to_dict(messages):
    message_dicts = []
    for message in messages:
        if isinstance(message, Chattest):
            message_dict = {
                "role": message.role,
                "content": message.content
            }
            message_dicts.append(message_dict)
    return message_dicts



@app.post("/agent")
async def read_item(request: List[Chattest]):

    llm = get_chat_model({
        # Use the model service provided by DashScope:
        'model': 'qwen-max-0919',
        'model_server': 'dashscope',
        'api_key': 'sk-92b2a6e512dd462899eb3baee40bd2fa',

        # Use the OpenAI-compatible model service provided by DashScope:
        # 'model': 'qwen1.5-14b-chat',
        # 'model_server': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
        # 'api_key': os.getenv('DASHSCOPE_API_KEY'),

        # Use the model service provided by Together.AI:
        # 'model': 'Qwen/Qwen1.5-14B-Chat',
        # 'model_server': 'https://api.together.xyz',  # api_base
        # 'api_key': os.getenv('TOGETHER_API_KEY'),

        # Use your own model service compatible with OpenAI API:
        # 'model': 'Qwen/Qwen1.5-72B-Chat',
        # 'model_server': 'http://localhost:8000/v1',  # api_base
        # 'api_key': 'EMPTY',
    })

    # Step 1: send the conversation and available functions to the model
    messages = convert_messages_to_dict(request)
    print('messages内容：',messages, 'messages类型',type(messages))
    # messages = [{'role': 'user', 'content': "params"}]
    # print('messages内容：',messages, 'messages类型',type(messages))
    functions = [
        {
            'name': 'calc_base',
            'description': """
            该函数用于基本电费、电费的退补电费、补缴电费的电量电费计算。包含用户减容变压器时候退补的钱、以及用户私增变压器时候要补的钱的计算方法。每个问题、每台变压器等情况要由单独的JSON对象表示。
            
            """,
            'parameters': {
                'type': 'object',
                        'properties': {
                    'fee_type_and_xinxi': {
                        'type': 'object',
                        'description': """  根据用户描述填入对应参数,该函数会根据json字典中不同的'type'有不同的算法,json文件为多个字典组合成的数组,即使只有一条记录也要使用数组方式保存到json包含一下属性：
                        "type"表示电费退补的类型"type":"normal_byq"是计算正常运行变压器类型，"type":"volume_reduction_byq"是减容变压器类型，"type":"private_addivate_byq"是私增变压器类型,"type":"reading_error"是读取电表错误类型,"type":"error_elcfee"是用于标识电价应用错误的情况，即客户应该执行的电价与实际执行的电价不符。这种情况下需要根据正确的电价计算出应退补的电费,
                        "type":"error_meter_man"是电表计量速度的错误类型(电能表走快或者走慢),"type":"error_current_transformer34"是三相四线计量装置应退补的电量，以纠正因互感器设置不当而导致的计量误差。,"type":"error_meter_duo"是电能表有误差,多计了或者少计了的量的百分比是多少的情况例如计量装置少计了20%的电量,
                        "type":"sys_error_elcfee"用于表示系统在计算电费时出现的错误,这通常指的是系统错误导致计算出的电费不准确，可能与实际抄表数据、电价等因素有关,"type":"error_meter","type":"error_voltage_loss33"表示三相三线缺相的电费退补情况,"type":"error_voltage_fx33"指的是三相三线电流接反电费退补计算的情况。
                        
                        "apparent_power"表示视在功率,若无提供则默认为0,
                        "date"在"type":"normal_byq"为null,在"type":"volume_reduction_byq"为减容当天的日期，在"type":"private_addivate_byq"为用户私增变压器的当天日期,当用户只说月份没说具体时间默认为每个月的一号,格式为YYYYMMDD,例如20230314
                        "actual_reading"表示实际抄表读数。
                        "previous_reading"表示上月抄表读数。
                        "base_price"表示变压器的基本电费为固定值，当用户有说明时候再代入。
                        "max_demand"表示最大需量如果用户未提及则默认为0。
                        "private_enddate_byq"表示私增变压器结束使用的当天日期格式为'YYYYMMDD',例如20230606，用户如果没有提及私增变压器结束使用的当天日期但是有说明抄表日期那么该值的默认值为{end_day},如果用户没有提及私增变压器结束使用的当天日期且没有说明抄表日期那么默认为null。
                        "active_power"表示有功功率。
                        "reactive_power"表示无功功率。
                        "power_adjustment_fee"表示力调电费。
                        "unit_price"表示单价电费或者电度电价每度电的电费或应收用户正确的电费单价。
                        "unit_jiben"表示基本电价(基本电费的电价)。
                        "error_reading"表示电表误抄、抄错的电量度数，例如将实际抄码6668错录入为6678，则6678是抄错的值就是"error_reading"的值。
                        "glys"表示功率因数标准默认为0.85。
                        "error_glys"表示用户提供错误的功率因数。
                        "glysxs"表示功率因数调整系数，默认为0.025。
                        "error_elc_fee"表示用户所缴纳的错误类型电价，例如：用户使用的是普通居民用电的价格0.6/(kW·h)，但是电力公司发行的是大工业用电的价格0.88/(kW·h)，那么该'error_elc_fee'就表示大工业用电的电价0.88/(kW·h)。
                        "elc_use"表示发行的总用电量是多少，指问题中第二次抄表的电量-第一次抄表的电量或还未装表的时候到第一次抄表所使用的电量是多少或者多个月的电量总和量。
                        "elc_error_percentage"表示表计的实际误差百分比，例如表少计20%则为-0.2，表多计10%则为0.1。
                        "current_ratio_A"A相电流互感器的变比，例如 150/5就是30那就是"current_ratio_A":30。
                        "current_ratio_B"B相电流互感器的变比，例如 100/5就是20那就是"current_ratio_B":20。
                        "current_ratio_C"C相电流互感器的变比，例如 200/5就是40那就是"current_ratio_C":40,（注意C相极性反接）。
                        "elc_error_meas"表示表多计了或者少计了的量的百分比是多少，比如多计了20%那么就为0.2少计了60％那么就为0.6。
                        "error_sys_elcfee"表示系统计算错误的电费值。
                        "elc_SjuseK"表示实际用电量是正常情况的倍率，比如：经测算实际用电量约为正常情况的 80%，那么"elc_SjuseK"为0.8。
                        "meter_Speed_ero"表示出现问题的电能表行走速度对比正常，比如其表慢20％那么值为-0.2，其表快40％那么值为0.4。
                        "elc_33JfuseK"三相三线电流接反后电能计量比实际用电量少的量，比如确定电流接反后电能计量比实际用电量少了20%则"elc_33JfuseK"= -0.2,确定电流接反后电能计量比实际用电量多了30%则"elc_33JfuseK"= 0.3。






                        我会根据不同的'type'情况说明json中所需要的参数，当'type'的情况是以下情况时候：
                        'type':"normal_byq"的时候参数需要json列表中的'apparent_power','unit_price','base_price'；代入到方法中计算。
                        'type':"volume_reduction_byq"的时候参数需要json列表中的'apparent_power','date','base_price','max_demand'；代入到方法中计算。
                        'type':"private_addivate_byq"的时候参数需要json列表中的'apparent_power','date','base_price','max_demand',"private_enddate_byq"；代入到方法中计算。
                        'type':"reading_error"的时候参数需要json列表中的'actual_reading','previous_reading','base_price','error_reading';代入到方法中计算。
                        'type':"litiao_elect"的时候参数需要json列表中的,"glys","error_glys","glysxs","active_power","reactive_power","unit_price","power_adjustment_fee";代入到方法中计算。
                        'type':"error_elcfee"的时候参数需要json列表中的,"error_elc_fee","elc_use","base_price","unit_price";代入到方法中计算。
                        "type":"error_current_transformer34"的时候参数需要json列表中的,"elc_error_percentage","current_ratio_A","current_ratio_B","current_ratio_C","elc_use";代入到方法中计算。
                        'type':"error_meter_man"的时候参数需要json列表中的，"meter_Speed_ero","elc_use";代入到方法中计算。
                        "type":"error_meter_duo"的时候参数需要json列表中的,"elc_error_percentage"，"elc_use","base_price";代入到方法中计算。
                        "type":"sys_error_elcfee"的时候参数需要json列表中的,"error_sys_elcfee","elc_use","base_price",;代入到方法中计算。
                        "type":"error_voltage_loss33"的时候需要json列表中的,"elc_use","current_ratio_A","current_ratio_B","current_ratio_C","elc_SjuseK","base_price";代入到方法中计算。
                        "type":"error_voltage_fx33"的时候需要json列表中的,"elc_use","unit_price","elc_33JfuseK";代入到方法中计算。


                        


                       根据用户问题提供参数写入参数到json中： 
                        用json数组表示例如:[
                                            {
                                                "type": "normal_byq",
                                                "apparent_power": 500,
                                                "base_price": 0.588,
                                                "unit_jiben": 20

                                            },
                                            {
                                                "type": "volume_reduction_byq",
                                                "apparent_power": 500,
                                                "date": "2023-03-26"
                                                "base_price": 0.588,
                                                "max_demand": 0.0,
                                                "unit_jiben": null
                                                

                                            },
                                            {
                                                "type": "private_addivate_byq",
                                                "private_enddate_byq": "20230824",
                                                "date": "2023-03-26",
                                                "apparent_power":660,
                                                "base_price":20

                                            },
                                            {
                                                "type": "reading_error",
                                                "actual_reading": 680,
                                                "previous_reading": 580,
                                                "base_price": 0.588,
                                                "error_reading": 690

                                            },
                                            {
                                                "type": "litiao_elect",
                                                "active_power": 500,
                                                "reactive_power": 600,
                                                "power_adjustment_fee": 900,
                                                "glys" : 0.95,
                                                "error_glys" : 0.88,                        
                                                "glysxs" : 0.023

                                            },
                                             {
                                                "type": "error_elcfee",
                                                "base_price": 0.66,
                                                "elc_use" : 900,
                                                "error_elc_fee": 100,
                                                "unit_price": 0.66

                                            },
                                             {
                                                "type": "error_meter_man",
                                                "elc_use" : 900,
                                                "meter_Speed_ero":null

                                            },
                                            {
                                                "type":"error_meter_duo",
                                                "elc_error_percentage":0.2,
                                                "elc_use" : 900,
                                                "base_price": 0.66
                                            },
                                            {
                                                "type": "error_current_transformer34",
                                                "elc_use" : 600,
                                                "current_ratio_A":30,
                                                "current_ratio_B":20,
                                                "current_ratio_C":40

                                            },
                                            {
                                                "type":"sys_error_elcfee",
                                                "base_price": 0.66,
                                                "error_sys_elcfee": 100,
                                                "elc_use" : 900

                                            },
                                            {
                                                "type":"error_voltage_loss33",
                                                "elc_use" : 600,
                                                "current_ratio_A":30,
                                                "current_ratio_B":20,
                                                "current_ratio_C":40,
                                                "elc_SjuseK":0.8,
                                                "base_price": 0.66

                                            },
                                            {
                                                "type":"error_voltage_fx33",
                                                "elc_use" : 600,
                                                "unit_price": 0.66,
                                                "elc_33JfuseK":0.8


                                            }

                                        ]


                        
                        """
                            },
            'range': { 
                        'type': 'string',
                        'description': '''该变量指的是用户问题中的抄表日期。用户如果没有提供任何抄表信息详情则默认上次抄表时间20230501本次抄表时间为20230601,用户若给了几月几号没给年份请提醒用户给出今年年份是多少年''',
                        "parameters": {
                                "type": "object",
                                "properties": {
                                    "start_day": {
                                        "type": "string",
                                        "description": "该参数指用户问题中开始的日期。时间用字符串表示格式为'YYYYMMDD'。例如3月5号为20230305，用户无提供则默认为20230501"
                                    },
                                    
                                    "end_day": {
                                        "type": "string",
                                        "description": "该参数指通常是用户最后一次抄表的日期时间用字符串表示格式为'YYYYMMDD'。例如4月5号为20230405，用户无提供则默认为20230601"
                                    },
                                     "monthly_cutoff_day": {
                                        "type": "integer",
                                        "description": "该参数指每个月的抄表日期。例如用户的抄表例日是每月25号则此值为25。若无提供，则默认为当月的月末。"
                                    }
                                                            
                        
                                },
                        
                    },
                    
                },         
                },
                'required': [],
            }
        },

    ]
    print('# Assistant Response 1:')
    responses = []
    for responses in llm.chat(
            messages=messages,
            functions=functions,
            stream=True,
    ):
        responses

    messages.extend(responses)  # extend conversation with assistant's reply

    # Step 2: check if the model wanted to call a function
    last_response = messages[-1]
    if last_response.get('function_call', None):


        available_functions = {
            'calc_base': calc_base,
        }  # only one function in this example, but you can have multiple
        function_name = last_response['function_call']['name']
        function_to_call = available_functions[function_name]
        function_args = json.loads(last_response['function_call']['arguments'])
        function_response = function_to_call(**function_args)
        print('# Function Response:')
        print(function_response)

        # Step 4: send the info for each function call and function response to the model
        messages.append({
            'role': 'function',
            'name': function_name,
            'content': function_response,
        })  # extend conversation with function response

        print('# Assistant Response 2:')
    return function_response