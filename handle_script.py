# -*- coding: utf-8 -*-
import sys
import time
import csv
import os
import re
from datetime import datetime, timedelta

sys.path.append("/home/dianmi_365/.local/lib/python3.8/site-packages")
import cn2an
from pdfminer.high_level import extract_text

# =============================公共常量=============================
# 目录路径
directory = "./csv/"
# 合同csv文件名后缀
contract_csv_filename_suffix = "_contract.csv"
# 离职单csv文件名后缀
resign_csv_filename_suffix = "_resign.csv"
# 定义合同表头
contract_headers = [
    "文件名",
    "合同类型",
    "姓名",
    "证件号",
    "手机号",
    "合同开始日期",
    "合同结束日期",
    "合同签署时长(年)",
    "试用期签署时长（天）",
    "试用期开始日期",
    "试用期结束日期",
]
# 定义离职单表头
resign_headers = ["文件名", "合同类型", "姓名", "证件号", "离职日期"]
# =============================公共常量=============================


# =============================公共方法=============================
# 清除已有文件
def cleanExistFile(file_list):
    for f_name in file_list:
        if os.path.exists(f_name):
            os.remove(f_name)


# 提取文本(去除了换行符 \n 和 空格 方便处理)
def handle_extract_text(file):
    #  row_text = extract_text(file)
    #  text_without_newline = re.sub(r'\n','', row_text)
    #  text_without_blank = re.sub(r' ','', text_without_newline)
    #  return text_without_blank
    # 简化的处理方法
    row_text = extract_text(file)
    # 去除所有的换行符 \n 和 空格
    text_without_blank_and_newline = re.sub(r"[\n\s]", "", row_text)
    return text_without_blank_and_newline


# 获取合同csv文件名称
def get_contract_csv_name(project_id):
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory + project_id + contract_csv_filename_suffix


# 获取离职单csv文件名称
def get_resign_csv_name(project_id):
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory + project_id + resign_csv_filename_suffix


# 合同写入CSV
def write_to_contract_csv(contract_csv_filename, row_data):
    with open(contract_csv_filename, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(row_data)


# 离职单写入CSV
def write_to_resign_csv(resign_csv_filename, row_data):
    with open(resign_csv_filename, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(row_data)


# 清除已存在的合同csv、离职单csv文件，新建合同csv、离职单csv文件
def pre_handle(contract_csv_filename, resign_csv_filename, project_id):
    # 清除已有文件
    cleanExistFile([contract_csv_filename, resign_csv_filename])
    # 写入合同表头
    write_to_contract_csv(contract_csv_filename, contract_headers)
    # 写入离职单表头
    write_to_resign_csv(resign_csv_filename, resign_headers)


# =============================公共方法=============================


# =============================处理器=============================
# TODO 每个处理器的遍历子文件夹的功能需要做下！！！
# =============================A8XX9 处理器=============================
class A8XX9_Handler:
    def process(self, project_id):
        contract_csv_filename = get_contract_csv_name(project_id)
        resign_csv_filename = get_resign_csv_name(project_id)
        # 预处理
        pre_handle(contract_csv_filename, resign_csv_filename, project_id)

        # 遍历处理当前文件夹下面所有子目录下的文件
        for root, dirs, files in os.walk("./" + project_id):
            for file in files:
                # 文件的全路径
                file_path = os.path.join(root, file)
                if file.endswith(".pdf"):
                    # 劳动合同解析
                    if "劳动合同" in file:
                        A8XX9_handle_contract(file_path, contract_csv_filename)
                        print(file_path + " <===============================> 劳动合同解析完毕")
                    # 离职单解析
                    elif "离职单" in file:
                        A8XX9_handle_resign(file_path, resign_csv_filename)
                        print(file_path + " <===============================> 离职单解析完毕")
                    else:
                        print(file_path + " --> 不需要解析的文件类型 ")


# 劳动合同处理函数
def A8XX9_handle_contract(file, contract_csv_filename):
    # 解析PDF文本
    pdf_text = handle_extract_text(file)
    # 匹配字符串
    row_data = A8XX9_match_contract_strings(file, pdf_text)
    # 写入csv 文件中
    write_to_contract_csv(contract_csv_filename, row_data)


# 匹配劳动合同字段
def A8XX9_match_contract_strings(file, pdf_text):
    # "文件名", "合同类型", "姓名", "证件号", "手机号", "合同开始日期", "合同结束日期",
    # "合同签署时长", "试用期签署时长", "试用期开始日期", "试用期结束日期"
    name = pdf_text[pdf_text.find("（职工）姓名：") + 7 : pdf_text.find("（职工）姓名：") + 10]
    # 第二代身份证18位：8位出生日期码，四位数年份+2位数月份+2位数日期。 3位顺序码，男性为奇数，女性为偶数。 最后再加一位校验码。
    id_card = pdf_text[pdf_text.find("身份证号码：") + 6 : pdf_text.find("身份证号码：") + 24]
    phone = pdf_text[pdf_text.find("联系电话：") + 5 : pdf_text.find("联系电话：") + 16]
    contract_start_date = pdf_text[
        pdf_text.find("有固定期限：从") + 7 : pdf_text.find("有固定期限：从") + 17
    ]
    contract_end_date = pdf_text[pdf_text.find("起到") + 2 : pdf_text.find("起到") + 12]
    # 需要计算
    start = datetime.datetime.strptime(contract_start_date, "%Y-%m-%d")
    end = datetime.datetime.strptime(contract_end_date, "%Y-%m-%d")
    sign_period = (end - start).days // 365
    # 试用期 （天为单位）
    # 可能会有 180，也可能会有 60 天的，所以这里做一个匹配
    row_trail_period = pdf_text[
        pdf_text.find("双方同意以本合同期限的前") + 12 : pdf_text.find("双方同意以本合同期限的前") + 18
    ]
    pattern = r"\d+"
    try:
        trail_period = int(re.search(pattern, row_trail_period).group())
    except (AttributeError, ValueError):
        trail_period = ""
    # 试用期开始 = 合同开始日期
    trail_period_start = contract_start_date
    try:
        # 需要计算
        format_trail_period_start = datetime.datetime.strptime(
            trail_period_start, "%Y-%m-%d"
        )
        # 累加180天
        format_trail_period_start += datetime.timedelta(days=int(trail_period))
        # 转换输出格式
        trail_period_end = format_trail_period_start.strftime("%Y-%m-%d")
    except (AttributeError, ValueError):
        trail_period_end = ""

    return [
        file,
        "劳动合同",
        name,
        id_card,
        phone,
        contract_start_date,
        contract_end_date,
        sign_period,
        trail_period,
        trail_period_start,
        trail_period_end,
    ]


# 离职单处理函数
def A8XX9_handle_resign(file, resign_csv_filename):
    # 解析PDF文本
    pdf_text = handle_extract_text(file)
    # 匹配字符串
    row_data = A8XX9_match_resign_strings(file, pdf_text)
    # 写入csv 文件中
    write_to_resign_csv(resign_csv_filename, row_data)


# 匹配离职单
def A8XX9_match_resign_strings(file, pdf_text):
    # 匹配 "文件名", "合同类型", "姓名", "证件号", "离职日期"
    name = pdf_text[pdf_text.find("姓名") + 2 : pdf_text.find("姓名") + 5]
    id_card = (
        pdf_text[pdf_text.find("身份证号码") + 5 : pdf_text.find("身份证号码") + 17]
        + ""
        + pdf_text[pdf_text.find("（员工") + 3 : pdf_text.find("（员工") + 9]
    )
    resign_date = pdf_text[pdf_text.find("本人填写）") + 5 : pdf_text.find("本人填写）") + 15]
    return [file, "离职单", name, id_card, resign_date]


# =============================A8XX9 处理器=============================


# =============================A8VEX 处理器=============================
# A8VEX 处理器
class A8VEX_Handler:
    def process(self, project_id):
        contract_csv_filename = get_contract_csv_name(project_id)
        resign_csv_filename = get_resign_csv_name(project_id)
        # 预处理
        pre_handle(contract_csv_filename, resign_csv_filename, project_id)

        # 遍历处理当前文件夹下面所有子目录下的文件
        for root, dirs, files in os.walk("./" + project_id):
            for file in files:
                # 文件的全路径
                file_path = os.path.join(root, file)
                if file.endswith(".pdf"):
                    # 聘用合同解析
                    if "聘用合同" in file:
                        A8VEX_handle_contract(file_path, contract_csv_filename)
                        print(
                            file_path + " <===============================> 聘用合同 解析完毕"
                        )
                    # 用工协议书
                    elif "用工协议书" in file:
                        A8VEX_handle_protocol(file_path, contract_csv_filename)
                        print(
                            file_path + " <===============================> 用工协议书 解析完毕"
                        )
                    # 离职单解析
                    elif "的离职单" in file:
                        A8VEX_handle_resign(file_path, resign_csv_filename)
                        print(file_path + " <===============================> 离职单 解析完毕")
                    else:
                        print(file_path + " --> 不需要解析的文件类型 ")


# 聘用合同处理函数
def A8VEX_handle_contract(file, contract_csv_filename):
    # 解析PDF文本
    pdf_text = handle_extract_text(file)
    # 匹配字符串
    row_data = A8VEX_match_contract_strings(file, pdf_text)
    # 写入 csv 文件中
    write_to_contract_csv(contract_csv_filename, row_data)


# 解析聘用合同处理函数
def A8VEX_match_contract_strings(file, pdf_text):
    # "文件名", "合同类型", "姓名", "证件号", "手机号", "合同开始日期", "合同结束日期",
    # "合同签署时长", "试用期签署时长", "试用期开始日期", "试用期结束日期"

    name_str = "职工）姓名："
    name_index = pdf_text.find(name_str)
    name = pdf_text[name_index + 6 : name_index + 9]

    # 第二代身份证18位：8位出生日期码，四位数年份+2位数月份+2位数日期。 3位顺序码，男性为奇数，女性为偶数。 最后再加一位校验码。
    id_card_str = "身份证号码："
    id_card_index = pdf_text.find(id_card_str)
    id_card = pdf_text[id_card_index + 6 : id_card_index + 24]

    # 电话号码
    phone_str = "联系电话："
    phone_index = pdf_text.find(phone_str)
    phone = pdf_text[phone_index + 5 : phone_index + 16]

    # 合同开始、结束日期
    start_date_str = "本合同期限自"
    start_date_index = pdf_text.find(start_date_str)
    contract_start_date = pdf_text[start_date_index + 6 : start_date_index + 16]
    # 聘用合同没有 合同结束日期 和 签署时长
    contract_end_date = "无"
    sign_period = "无"

    # 试用期 （天为单位）
    # 用工协议书 没有试用期
    trail_period = "无"
    trail_period_start = "无"
    trail_period_end = "无"

    # print([file, "劳动合同", name, id_card, phone, contract_start_date, contract_end_date, sign_period, trail_period, trail_period_start, trail_period_end])
    return [
        file,
        "劳动合同",
        name,
        id_card,
        phone,
        contract_start_date,
        contract_end_date,
        sign_period,
        trail_period,
        trail_period_start,
        trail_period_end,
    ]


# 用工协议书处理函数
def A8VEX_handle_protocol(file, contract_csv_filename):
    # 解析PDF文本
    pdf_text = handle_extract_text(file)
    # 匹配字符串
    row_data = A8VEX_match_protocol_strings(file, pdf_text)
    # 写入csv 文件中
    write_to_contract_csv(contract_csv_filename, row_data)


# 匹配用工协议书字段处理函数
def A8VEX_match_protocol_strings(file, pdf_text):
    # "文件名", "合同类型", "姓名", "证件号", "手机号", "合同开始日期", "合同结束日期",
    # "合同签署时长", "试用期签署时长", "试用期开始日期", "试用期结束日期"

    name_str = "聘用人)："
    name_index = pdf_text.find(name_str)
    name = pdf_text[name_index + 5 : name_index + 8]

    # 第二代身份证18位：8位出生日期码，四位数年份+2位数月份+2位数日期。 3位顺序码，男性为奇数，女性为偶数。 最后再加一位校验码。
    id_card_str = "身份证号码："
    id_card_index = pdf_text.find(id_card_str)
    id_card = pdf_text[id_card_index + 6 : id_card_index + 24]

    # 电话号码
    phone_str = "乙方作为退休人员"
    phone_index = pdf_text.find(phone_str)
    phone = pdf_text[phone_index - 11 : phone_index]

    # 合同开始、结束日期
    start_date_str = "聘用期限：自"
    start_date_index = pdf_text.find(start_date_str)
    contract_start_date = pdf_text[start_date_index + 6 : start_date_index + 16]
    # 特殊情况，如果存在没有 合同开始、结束日期的特殊处理
    if not any(map(str.isdigit, contract_start_date)):
        contract_start_date = "无"

    end_date_str = "起至"
    end_date_index = pdf_text.find(end_date_str)
    contract_end_date = pdf_text[end_date_index + 2 : end_date_index + 12]
    if not any(map(str.isdigit, contract_end_date)):
        contract_end_date = "无"

    # 需要计算
    sign_period = "无"
    if contract_start_date and contract_start_date != "无" and contract_end_date:
        start = datetime.datetime.strptime(contract_start_date, "%Y-%m-%d")
        end = datetime.datetime.strptime(contract_end_date, "%Y-%m-%d")
        sign_period = (end - start).days // 365

    # 试用期 （天为单位）
    # 用工协议书 没有试用期
    trail_period = "无"
    trail_period_start = "无"
    trail_period_end = "无"

    return [
        file,
        "用工协议书",
        name,
        id_card,
        phone,
        contract_start_date,
        contract_end_date,
        sign_period,
        trail_period,
        trail_period_start,
        trail_period_end,
    ]


# 离职单处理函数
def A8VEX_handle_resign(file, resign_csv_filename):
    # 解析PDF文本
    pdf_text = handle_extract_text(file)
    # 匹配字符串
    row_data = A8VEX_match_resign_strings(file, pdf_text)
    # 写入csv 文件中
    write_to_resign_csv(resign_csv_filename, row_data)


# 匹配离职单
def A8VEX_match_resign_strings(file, pdf_text):
    # 匹配 "文件名", "合同类型", "姓名", "证件号", "离职日期"
    name_str = "姓名"
    name_index = pdf_text.find(name_str)
    # 截止到联系电话前，都是姓名
    phone_str = "联系电话"
    phone_index = pdf_text.find(phone_str)
    name = pdf_text[name_index + 2 : phone_index]

    # 第二代身份证18位：8位出生日期码，四位数年份+2位数月份+2位数日期。 3位顺序码，男性为奇数，女性为偶数。 最后再加一位校验码。
    id_card_str = "身份证号码"
    id_card_index = pdf_text.find(id_card_str)
    id_card_sub = pdf_text[id_card_index + 5 : id_card_index + 17]
    retain_str = "员工本"
    retain_index = pdf_text.find(retain_str)
    retain = pdf_text[retain_index + 3 : retain_index + 9]
    id_card = id_card_sub + retain

    resign_str = "人填写）"
    resign_index = pdf_text.find(resign_str)
    resign_date = pdf_text[resign_index + 4 : resign_index + 14]

    return [file, "离职单", name, id_card, resign_date]


# =============================A8VEX 处理器=============================


# =============================A8SXZ 处理器=============================
class A8SXZ_Handler:
    def process(self, project_id):
        contract_csv_filename = get_contract_csv_name(project_id)
        resign_csv_filename = get_resign_csv_name(project_id)
        # 预处理
        pre_handle(contract_csv_filename, resign_csv_filename, project_id)

        # 遍历处理当前文件夹下面所有子目录下的文件
        for root, dirs, files in os.walk("./" + project_id):
            for file in files:
                # 文件的全路径
                file_path = os.path.join(root, file)
                if file.endswith(".pdf"):
                    # 合同解析
                    if "全日制劳动合同" in file:
                        A8SXZ_handle_contract(file_path, contract_csv_filename)
                        print(
                            file_path + " <===============================> 聘用合同 解析完毕"
                        )
                    # 离职单解析
                    elif "的离职单" in file:
                        A8SXZ_handle_resign(file_path, resign_csv_filename)
                        print(file_path + " <===============================> 离职单 解析完毕")
                    else:
                        print(file_path + " --> 不需要解析的文件类型 ")


# 合同处理函数
def A8SXZ_handle_contract(file, contract_csv_filename):
    # 解析PDF文本
    pdf_text = handle_extract_text(file)
    # 匹配字符串
    row_data = A8SXZ_match_contract_strings(file, pdf_text)
    # 写入 csv 文件中
    write_to_contract_csv(contract_csv_filename, row_data)


# 解析合同处理函数
def A8SXZ_match_contract_strings(file, pdf_text):
    # "文件名", "合同类型", "姓名", "证件号", "手机号", "合同开始日期", "合同结束日期",
    # "合同签署时长", "试用期签署时长", "试用期开始日期", "试用期结束日期"

    name_str = "职工）姓名："
    name_index = pdf_text.find(name_str)
    name = pdf_text[name_index + 6 : name_index + 9]

    # 第二代身份证18位：8位出生日期码，四位数年份+2位数月份+2位数日期。 3位顺序码，男性为奇数，女性为偶数。 最后再加一位校验码。
    id_card_str = "身份证号码："
    id_card_index = pdf_text.find(id_card_str)
    id_card = pdf_text[id_card_index + 6 : id_card_index + 24]

    # 电话号码
    phone_str = "联系电话："
    phone_index = pdf_text.find(phone_str)
    phone = pdf_text[phone_index + 5 : phone_index + 16]

    # 合同开始日期
    start_date_str = "年：从"
    start_date_index = pdf_text.find(start_date_str)
    contract_start_date = pdf_text[start_date_index + 3 : start_date_index + 13]
    # 结束日期：这里的截取需要考虑到 试用期的也是一样格式，所以不能只用 “起至“
    # 3 + 10 + 2 = 15，最后一个字符索引为 14
    end_date_str = start_date_str + contract_start_date + "起至"
    end_date_index = pdf_text.find(end_date_str)
    contract_end_date = pdf_text[end_date_index + 15 : end_date_index + 25]

    # 合同签署时长
    sign_str = "、固定期限"
    sign_index = pdf_text.find(sign_str)
    # 这里取到的是繁体中文数字
    sign_period_cn = pdf_text[sign_index + 5 : sign_index + 6]
    # 转换成 数字
    sign_period = cn2an.cn2an(sign_period_cn)

    # 试用期 （天为单位）
    trail_period_str = "试用期"
    trail_period_index = pdf_text.find(trail_period_str)
    # 这里是月
    trail_period_month = pdf_text[trail_period_index + 3 : trail_period_index + 4]

    # 转换成 天
    try:
        trail_period = int(trail_period_month) * 30
    except (AttributeError, ValueError):
        trail_period = "无"

    trail_period_start = "无"
    trail_period_end = "无"
    if trail_period != "无":
        # 试用期开始
        tp_start_str = "个月，从"
        tp_start_index = pdf_text.find(tp_start_str)
        trail_period_start = pdf_text[tp_start_index + 4 : tp_start_index + 14]
        # 试用期结束
        # 4 + 10 + 2 = 16，最后一个字符索引为 15
        trail_period_end_str = tp_start_str + trail_period_start + "起至"
        trail_period_end_index = pdf_text.find(trail_period_end_str)
        trail_period_end = pdf_text[
            trail_period_end_index + 16 : trail_period_end_index + 26
        ]

    return [
        file,
        "劳动合同",
        name,
        id_card,
        phone,
        contract_start_date,
        contract_end_date,
        sign_period,
        trail_period,
        trail_period_start,
        trail_period_end,
    ]


# 离职单处理函数
def A8SXZ_handle_resign(file, resign_csv_filename):
    # 解析PDF文本
    pdf_text = handle_extract_text(file)
    # 匹配字符串
    row_data = A8SXZ_match_resign_strings(file, pdf_text)
    # 写入csv 文件中
    write_to_resign_csv(resign_csv_filename, row_data)


# 匹配离职单
def A8SXZ_match_resign_strings(file, pdf_text):
    # 匹配 "文件名", "合同类型", "姓名", "证件号", "离职日期"

    name_str = "姓名"
    name_index = pdf_text.find(name_str)
    # 截止到联系电话前，都是姓名
    phone_str = "联系电话"
    phone_index = pdf_text.find(phone_str)
    name = pdf_text[name_index + 2 : phone_index]

    # 第二代身份证18位：8位出生日期码，四位数年份+2位数月份+2位数日期。 3位顺序码，男性为奇数，女性为偶数。 最后再加一位校验码。
    id_card_str = "身份证号码"
    id_card_index = pdf_text.find(id_card_str)
    id_card_sub = pdf_text[id_card_index + 5 : id_card_index + 17]
    retain_str = "（员工"
    retain_index = pdf_text.find(retain_str)
    retain = pdf_text[retain_index + 3 : retain_index + 9]
    id_card = id_card_sub + retain

    resign_str = "人填写）"
    resign_index = pdf_text.find(resign_str)
    resign_date = pdf_text[resign_index + 4 : resign_index + 14]

    return [file, "离职单", name, id_card, resign_date]


# =============================A8SXZ 处理器=============================


# =============================A832G 处理器=============================
class A832G_Handler:
    def process(self, project_id):
        contract_csv_filename = get_contract_csv_name(project_id)
        resign_csv_filename = get_resign_csv_name(project_id)
        # 预处理
        pre_handle(contract_csv_filename, resign_csv_filename, project_id)

        # 遍历处理当前文件夹下面所有子目录下的文件
        for root, dirs, files in os.walk("./" + project_id):
            for file in files:
                if file.endswith(".pdf"):
                    # 文件的全路径
                    file_path = os.path.join(root, file)
                    if "退休返聘协议" in file:
                        A832G_handle_protocol(file_path, contract_csv_filename)
                        print(
                            file_path + " <===============================> 退休返聘协议 解析完毕"
                        )

                    elif "聘用合同" in file:
                        A832G_handle_hire_contract(file_path, contract_csv_filename)
                        print(
                            file_path + " <===============================> 聘用合同 解析完毕"
                        )

                    elif "劳动合同" in file:
                        A832G_handle_contract(file_path, contract_csv_filename)
                        print(
                            file_path + " <===============================> 劳动合同 解析完毕"
                        )

                    elif "的离职单" in file:
                        A832G_handle_resign(file_path, resign_csv_filename)
                        print(file_path + " <===============================> 离职单 解析完毕")

                    elif "实习协议" in file:
                        A832G_handle_practice(file_path, contract_csv_filename)
                        print(
                            file_path + " <===============================> 实习协议 解析完毕"
                        )

                    else:
                        print(file_path + " --> 不需要解析的文件类型 ")


# 退休人员用工协议书
def A832G_handle_protocol(file, contract_csv_filename):
    # 解析PDF文本
    pdf_text = handle_extract_text(file)
    # 匹配字符串
    row_data = A832G_match_protocol_strings(file, pdf_text)
    # 写入 csv 文件中
    write_to_contract_csv(contract_csv_filename, row_data)


# 退休人员用工协议书 匹配函数
def A832G_match_protocol_strings(file, pdf_text):
    # "文件名", "合同类型", "姓名", "证件号", "手机号", "合同开始日期", "合同结束日期",
    # "合同签署时长", "试用期签署时长", "试用期开始日期", "试用期结束日期"

    # 第二代身份证18位：8位出生日期码，四位数年份+2位数月份+2位数日期。 3位顺序码，男性为奇数，女性为偶数。 最后再加一位校验码。
    id_card_str = "身份证号："
    id_card_index = pdf_text.find(id_card_str)
    id_card = pdf_text[id_card_index + 5 : id_card_index + 23]

    # 姓名
    name_str = "被聘用人)："
    name_index = pdf_text.find(name_str)
    name = pdf_text[name_index + 6 : id_card_index]

    # 电话号码
    phone_str = "乙方作为退休人员"
    phone_index = pdf_text.find(phone_str)
    phone = pdf_text[phone_index - 11 : phone_index]

    # 合同开始日期
    start_date_str = "聘用期限："
    start_date_index = pdf_text.find(start_date_str)
    contract_start_date_temp = pdf_text[start_date_index + 5 : start_date_index + 15]
    # 提取
    contract_start_date = extract_special_date(contract_start_date_temp)
    if contract_start_date is None:
        contract_start_date = "无"
    # 结束日期
    end_date_str = "起至"
    end_date_index = pdf_text.find(end_date_str)
    contract_end_date_temp = pdf_text[end_date_index + 2 : end_date_index + 12]
    # 提取
    contract_end_date = extract_special_date(contract_end_date_temp)
    if contract_end_date is None:
        contract_end_date = "无"

    # 合同签署时长
    sign_period = "无"

    # 试用期 （天为单位）
    trail_period = "无"

    # 试用期开始
    trail_period_start = "无"
    # 试用期结束
    trail_period_end = "无"

    return [
        file,
        "退休返聘协议",
        name,
        id_card,
        phone,
        contract_start_date,
        contract_end_date,
        sign_period,
        trail_period,
        trail_period_start,
        trail_period_end,
    ]


# 聘用合同
def A832G_handle_hire_contract(file, contract_csv_filename):
    # 解析PDF文本
    pdf_text = handle_extract_text(file)
    # 匹配字符串
    row_data = A832G_match_hire_contract_strings(file, pdf_text)
    # 写入 csv 文件中
    write_to_contract_csv(contract_csv_filename, row_data)


# 聘用合同 匹配函数
def A832G_match_hire_contract_strings(file, pdf_text):
    # "文件名", "合同类型", "姓名", "证件号", "手机号", "合同开始日期", "合同结束日期",
    # "合同签署时长", "试用期签署时长", "试用期开始日期", "试用期结束日期"

    # 第二代身份证18位：8位出生日期码，四位数年份+2位数月份+2位数日期。 3位顺序码，男性为奇数，女性为偶数。 最后再加一位校验码。
    id_card_str = "份证号码："
    id_card_index = pdf_text.find(id_card_str)
    id_card = pdf_text[id_card_index + 5 : id_card_index + 23]

    # 姓名
    name_str = "职工）姓名："
    name_index = pdf_text.find(name_str)
    sex_index = pdf_text.find("性别")
    name = pdf_text[name_index + 6 : sex_index]

    # 电话号码
    phone_str = "联系电话："
    phone_index = pdf_text.find(phone_str)
    phone = pdf_text[phone_index + 5 : phone_index + 16]

    # 合同开始日期
    start_date_str = "本合同期限自"
    start_date_index = pdf_text.find(start_date_str)
    contract_start_date = pdf_text[start_date_index + 6 : start_date_index + 16]
    # 结束日期
    contract_end_date = "无"
    # 合同签署时长
    sign_period = "无"

    # 试用期 （天为单位）
    trail_period = "无"
    # 试用期开始
    trail_period_start = "无"
    # 试用期结束
    trail_period_end = "无"

    # print([file, "劳动合同", name, id_card, phone, contract_start_date, contract_end_date, sign_period, trail_period, trail_period_start, trail_period_end])
    return [
        file,
        "聘用合同",
        name,
        id_card,
        phone,
        contract_start_date,
        contract_end_date,
        sign_period,
        trail_period,
        trail_period_start,
        trail_period_end,
    ]


# 劳动合同
def A832G_handle_contract(file, contract_csv_filename):
    # 解析PDF文本
    pdf_text = handle_extract_text(file)
    # 匹配字符串
    row_data = A832G_match_contract_strings(file, pdf_text)
    # 写入 csv 文件中
    write_to_contract_csv(contract_csv_filename, row_data)


# 劳动合同 匹配函数
def A832G_match_contract_strings(file, pdf_text):
    # "文件名", "合同类型", "姓名", "证件号", "手机号", "合同开始日期", "合同结束日期",
    # "合同签署时长", "试用期签署时长", "试用期开始日期", "试用期结束日期"

    # 第二代身份证18位：8位出生日期码，四位数年份+2位数月份+2位数日期。 3位顺序码，男性为奇数，女性为偶数。 最后再加一位校验码。
    id_card_str = "份证号码："
    id_card_index = pdf_text.find(id_card_str)
    id_card = pdf_text[id_card_index + 5 : id_card_index + 23]
    # 最后一位 字母
    if not id_card[:-1].isdigit():
        id_card = "无"

    # 姓名
    name_str = "职工）姓名："
    name_index = pdf_text.find(name_str)
    sex_index = pdf_text.find("性别")
    name = pdf_text[name_index + 6 : sex_index]

    # 电话号码
    phone_str = "联系电话："
    phone_index = pdf_text.find(phone_str)
    phone = pdf_text[phone_index + 5 : phone_index + 16]

    # 合同开始日期
    start_date_str = "年：从"
    start_date_index = pdf_text.find(start_date_str)
    contract_start_date = pdf_text[start_date_index + 3 : start_date_index + 13]
    # 结束日期：这里的截取需要考虑到 试用期的也是一样格式，所以不能只用 “起至“
    # 3 + 10 + 2 = 15，最后一个字符索引为 14
    end_date_str = start_date_str + contract_start_date + "起至"
    end_date_index = pdf_text.find(end_date_str)
    contract_end_date = pdf_text[end_date_index + 15 : end_date_index + 25]

    # 合同签署时长
    sign_str = "、固定期限"
    sign_index = pdf_text.find(sign_str)
    # 这里取到的是繁体中文数字
    sign_period_cn = pdf_text[sign_index + 5 : sign_index + 6]
    # 转换成 数字
    try:
        sign_period = int(cn2an.cn2an(sign_period_cn, "smart"))
    except (AttributeError, ValueError):
        sign_period = ""

    # 试用期 （天为单位）
    trail_period_str = "试用期"
    trail_period_index = pdf_text.find(trail_period_str)
    try:
        # 这里是月
        trail_period_month_cn = pdf_text[
            trail_period_index + 3 : trail_period_index + 4
        ]
        trail_period_month = cn2an.cn2an(trail_period_month_cn, "smart")
        # 转换成 天
        trail_period = int(trail_period_month) * 30
    except (AttributeError, ValueError):
        trail_period = ""

    # 试用期开始
    tp_start_str = "个月，从"
    tp_start_index = pdf_text.find(tp_start_str)
    trail_period_start = pdf_text[tp_start_index + 4 : tp_start_index + 14]
    # 试用期结束
    # 4 + 10 + 2 = 16，最后一个字符索引为 15
    trail_period_end_str = tp_start_str + trail_period_start + "起至"
    trail_period_end_index = pdf_text.find(trail_period_end_str)
    trail_period_end = pdf_text[
        trail_period_end_index + 16 : trail_period_end_index + 26
    ]

    return [
        file,
        "劳动合同",
        name,
        id_card,
        phone,
        contract_start_date,
        contract_end_date,
        sign_period,
        trail_period,
        trail_period_start,
        trail_period_end,
    ]


# 离职单
def A832G_handle_resign(file, resign_csv_filename):
    # 解析PDF文本
    pdf_text = handle_extract_text(file)
    # 匹配字符串
    row_data = A832G_match_resign_strings(file, pdf_text)
    # 写入 csv 文件中
    write_to_contract_csv(resign_csv_filename, row_data)


# 离职单 匹配函数
def A832G_match_resign_strings(file, pdf_text):
    # 匹配 "文件名", "合同类型", "姓名", "证件号", "离职日期"

    name_str = "姓名"
    name_index = pdf_text.find(name_str)
    # 截止到联系电话前，都是姓名
    phone_str = "联系电"
    phone_index = pdf_text.find(phone_str)
    name = pdf_text[name_index + 2 : phone_index]

    # 第二代身份证18位：8位出生日期码，四位数年份+2位数月份+2位数日期。 3位顺序码，男性为奇数，女性为偶数。 最后再加一位校验码。
    id_card_str = "离职原因"
    id_card_index = pdf_text.find(id_card_str)
    id_card_sub = pdf_text[id_card_index + 4 : id_card_index + 16]
    retain_str = "员工本"
    retain_index = pdf_text.find(retain_str)
    retain = pdf_text[retain_index + 3 : retain_index + 9]
    id_card = id_card_sub + retain

    # 离职日期
    resign_str = "个人原因"
    resign_index = pdf_text.find(resign_str)
    resign_date = pdf_text[resign_index + 4 : resign_index + 14]

    return [file, "离职单", name, id_card, resign_date]


# 实习协议
def A832G_handle_practice(file, contract_csv_filename):
    # 解析PDF文本
    pdf_text = handle_extract_text(file)
    # 匹配字符串
    row_data = A832G_match_practice_strings(file, pdf_text)
    # 写入 csv 文件中
    write_to_contract_csv(contract_csv_filename, row_data)


# 实习协议 匹配函数
def A832G_match_practice_strings(file, pdf_text):
    # "文件名", "合同类型", "姓名", "证件号", "手机号", "合同开始日期", "合同结束日期",
    # "合同签署时长", "试用期签署时长", "试用期开始日期", "试用期结束日期"

    # 第二代身份证18位：8位出生日期码，四位数年份+2位数月份+2位数日期。 3位顺序码，男性为奇数，女性为偶数。 最后再加一位校验码。
    id_card_str = "份证号码："
    id_card_index = pdf_text.find(id_card_str)
    id_card = pdf_text[id_card_index + 5 : id_card_index + 23]

    # 姓名
    name_str = "简称乙方）:"
    name_str_eng = "简称乙方):"
    name_index = pdf_text.find(name_str)
    if name_index == -1:
        name_index = pdf_text.find(name_str_eng)
    tmp_index = pdf_text.find("身份证")
    name = pdf_text[name_index + 6 : tmp_index]

    # 电话号码
    phone_str = "式："
    phone_index = pdf_text.find(phone_str)
    phone = pdf_text[phone_index + 2 : phone_index + 13]

    # 合同开始日期
    start_date_str = "实习期限自"
    start_date_index = pdf_text.find(start_date_str)
    contract_start_date = pdf_text[start_date_index + 5 : start_date_index + 15]
    # 结束日期
    end_date_str = "起至"
    end_date_index = pdf_text.find(end_date_str)
    contract_end_date = pdf_text[end_date_index + 2 : end_date_index + 12]

    # 合同签署时长
    # 需要计算
    start = datetime.datetime.strptime(contract_start_date, "%Y-%m-%d")
    end = datetime.datetime.strptime(contract_end_date, "%Y-%m-%d")
    sign_period = (end - start).days // 365

    # 试用期 （天为单位）
    trail_period = "无"

    # 试用期开始
    trail_period_start = "无"
    # 试用期结束
    trail_period_end = "无"

    return [
        file,
        "实习协议",
        name,
        id_card,
        phone,
        contract_start_date,
        contract_end_date,
        sign_period,
        trail_period,
        trail_period_start,
        trail_period_end,
    ]


# =============================A832G 处理器=============================


# =============================A8M5E 处理器=============================
class A8M5E_Handler:
    def process(self, project_id):
        contract_csv_filename = get_contract_csv_name(project_id)
        resign_csv_filename = get_resign_csv_name(project_id)
        # 预处理
        pre_handle(contract_csv_filename, resign_csv_filename, project_id)

        # 遍历处理当前文件夹下面所有子目录下的文件
        for root, dirs, files in os.walk("./" + project_id):
            for file in files:
                if file.endswith(".pdf"):
                    # 文件的全路径
                    file_path = os.path.join(root, file)
                    if "固定期限劳动合同" in file:
                        A8M5E_handle_fix_time_contract(file_path, contract_csv_filename)
                        print(
                            file_path
                            + " <===============================> 固定期限劳动合同 解析完毕"
                        )

                    elif "劳务合同" in file:
                        A8M5E_handle_contract(file_path, contract_csv_filename)
                        print(
                            file_path + " <===============================> 劳务合同 解析完毕"
                        )

                    elif "退休返聘" in file:
                        A8M5E_handle_hire_contract(file_path, contract_csv_filename)
                        print(
                            file_path + " <===============================> 退休返聘 解析完毕"
                        )
                        print()

                    elif "实习协议" in file:
                        A8M5E_handle_practice(file_path, contract_csv_filename)
                        print(
                            file_path + " <===============================> 实习协议 解析完毕"
                        )

                    elif "的离职申请" in file:
                        A8M5E_handle_resign(file_path, resign_csv_filename)
                        print(file_path + " <===============================> 离职 解析完毕")

                    else:
                        print(file_path + " --> 不需要解析的文件类型 ")


# 离职
def A8M5E_handle_resign(file, resign_csv_filename):
    # 解析PDF文本
    pdf_text = handle_extract_text(file)
    # 匹配字符串
    row_data = A8M5E_handle_resign_match_str(file, pdf_text)
    # 写入 csv 文件中
    write_to_contract_csv(resign_csv_filename, row_data)


# 离职 匹配函数
def A8M5E_handle_resign_match_str(file, pdf_text):
    # 匹配 "文件名", "合同类型", "姓名", "证件号", "离职日期"

    name_str = "名岗位"
    name_index = pdf_text.find(name_str)
    # 截止到联系电话前，都是姓名
    phone_str = "联系电"
    phone_index = pdf_text.find(phone_str)
    if name_index == -1:
        a_name_str = "姓名"
        name_index = pdf_text.find(a_name_str)
        name = pdf_text[name_index + 2 : phone_index]
    else:
        name = pdf_text[name_index + 3 : phone_index]

    # 第二代身份证18位：8位出生日期码，四位数年份+2位数月份+2位数日期。 3位顺序码，男性为奇数，女性为偶数。 最后再加一位校验码。
    id_card_str = "身份证号码"
    id_card_index = pdf_text.find(id_card_str)
    id_card_sub = pdf_text[id_card_index + 5 : id_card_index + 23]
    # 最后一位校验码是字母
    if id_card_sub[:-1].isdigit():
        id_card = id_card_sub
    else:
        id_card_sub = pdf_text[id_card_index + 5 : id_card_index + 20]
        retain_str = "员工本人填"
        retain_index = pdf_text.find(retain_str)
        retain = pdf_text[retain_index + 5 : retain_index + 8]
        id_card = id_card_sub + retain

    # 离职日期
    resign_date = "异常"
    try:
        resign_str = "个人原因"
        resign_index = pdf_text.find(resign_str)
        resign_date = pdf_text[resign_index + 4 : resign_index + 14]
        if not resign_date[0].isdigit():
            resign_str = "离职原因√"
            resign_index = pdf_text.find(resign_str)
            # 10 不是固定值
            tem_str = "填写）"
            tem_index = pdf_text.find(tem_str)
            resign_date = pdf_text[tem_index + 3 : resign_index]
            print("离职日期：", str(resign_date))
            if "/" in resign_date:
                year, month, day = map(int, resign_date.split("/"))
                resign_date = f"{year}-{month:02d}-{day:02d}"
    except (Exception, SyntaxError) as e:
        print("异常：" + str(e))
        resign_date = "异常"

    return [file, "离职单", name, id_card, resign_date]


# 实习协议
def A8M5E_handle_practice(file, contract_csv_filename):
    # 解析PDF文本
    pdf_text = handle_extract_text(file)
    # 匹配字符串
    row_data = A8M5E_handle_practice_match_str(file, pdf_text)
    # 写入 csv 文件中
    write_to_contract_csv(contract_csv_filename, row_data)


# 实习协议 匹配函数
def A8M5E_handle_practice_match_str(file, pdf_text):
    # "文件名", "合同类型", "姓名", "证件号", "手机号", "合同开始日期", "合同结束日期",
    # "合同签署时长", "试用期签署时长", "试用期开始日期", "试用期结束日期"

    # 第二代身份证18位：8位出生日期码，四位数年份+2位数月份+2位数日期。 3位顺序码，男性为奇数，女性为偶数。 最后再加一位校验码。
    id_card_str = "份证号码："
    id_card_index = pdf_text.find(id_card_str)
    id_card = pdf_text[id_card_index + 5 : id_card_index + 23]

    # 姓名
    name_str = "简称乙方）:"
    name_str_eng = "简称乙方):"
    name_index = pdf_text.find(name_str)
    if name_index == -1:
        name_index = pdf_text.find(name_str_eng)
    tmp_index = pdf_text.find("身份证")
    name = pdf_text[name_index + 6 : tmp_index]

    # 电话号码
    phone_str = "）联系方式："
    phone_index = pdf_text.find(phone_str)
    phone = pdf_text[phone_index + 6 : phone_index + 17]

    # 合同开始日期
    start_date_str = "实习期限自"
    start_date_index = pdf_text.find(start_date_str)
    contract_start_date = pdf_text[start_date_index + 5 : start_date_index + 15]
    # 结束日期
    end_date_str = "起至"
    end_date_index = pdf_text.find(end_date_str)
    contract_end_date = pdf_text[end_date_index + 2 : end_date_index + 12]

    # 合同签署时长
    # 需要计算
    try:
        start = datetime.datetime.strptime(contract_start_date, "%Y-%m-%d")
        end = datetime.datetime.strptime(contract_end_date, "%Y-%m-%d")
        sign_period = (end - start).days // 365
        if sign_period < 1:
            sign_period = float(sign_period)
    except Exception:
        sign_period = "无"

    # 试用期 （天为单位）
    trail_period = "无"

    # 试用期开始
    trail_period_start = "无"
    # 试用期结束
    trail_period_end = "无"

    return [
        file,
        "实习协议",
        name,
        id_card,
        phone,
        contract_start_date,
        contract_end_date,
        sign_period,
        trail_period,
        trail_period_start,
        trail_period_end,
    ]


# 退休返聘
def A8M5E_handle_hire_contract(file, contract_csv_filename):
    # 解析PDF文本
    pdf_text = handle_extract_text(file)
    # 匹配字符串
    row_data = A8M5E_handle_hire_contract_match_str(file, pdf_text)
    # 写入 csv 文件中
    write_to_contract_csv(contract_csv_filename, row_data)


# 退休返聘 匹配函数
def A8M5E_handle_hire_contract_match_str(file, pdf_text):
    # "文件名", "合同类型", "姓名", "证件号", "手机号", "合同开始日期", "合同结束日期",
    # "合同签署时长", "试用期签署时长", "试用期开始日期", "试用期结束日期"

    name_str = "聘用人)："
    name_index = pdf_text.find(name_str)
    name = pdf_text[name_index + 5 : name_index + 8]

    # 第二代身份证18位：8位出生日期码，四位数年份+2位数月份+2位数日期。 3位顺序码，男性为奇数，女性为偶数。 最后再加一位校验码。
    id_card_str = "身份证号码："
    id_card_index = pdf_text.find(id_card_str)
    id_card = pdf_text[id_card_index + 6 : id_card_index + 24]

    # 电话号码
    phone_str = "乙方作为退休人员"
    phone_index = pdf_text.find(phone_str)
    phone = pdf_text[phone_index - 11 : phone_index]

    # 合同开始、结束日期
    start_date_str = "聘用期限：自"
    start_date_index = pdf_text.find(start_date_str)
    contract_start_date = pdf_text[start_date_index + 6 : start_date_index + 16]
    # 特殊情况，如果存在没有 合同开始、结束日期的特殊处理
    if not any(map(str.isdigit, contract_start_date)):
        contract_start_date = "无"

    end_date_str = "起至"
    end_date_index = pdf_text.find(end_date_str)
    contract_end_date = pdf_text[end_date_index + 2 : end_date_index + 12]
    if not any(map(str.isdigit, contract_end_date)):
        contract_end_date = "无"

    # 需要计算
    sign_period = "无"
    try:
        if contract_start_date and contract_start_date != "无" and contract_end_date:
            start = datetime.datetime.strptime(contract_start_date, "%Y-%m-%d")
            end = datetime.datetime.strptime(contract_end_date, "%Y-%m-%d")
            sign_period = (end - start).days // 365
    except ValueError:
        sign_period = "无"

    # 试用期 （天为单位）
    trail_period = "无"
    trail_period_start = "无"
    trail_period_end = "无"

    return [
        file,
        "退休返聘",
        name,
        id_card,
        phone,
        contract_start_date,
        contract_end_date,
        sign_period,
        trail_period,
        trail_period_start,
        trail_period_end,
    ]


# 劳务合同
def A8M5E_handle_contract(file, contract_csv_filename):
    # 解析PDF文本
    pdf_text = handle_extract_text(file)
    # 匹配字符串
    row_data = A8M5E_handle_contract_match_str(file, pdf_text)
    # 写入 csv 文件中
    write_to_contract_csv(contract_csv_filename, row_data)


# 劳务合同 匹配函数
def A8M5E_handle_contract_match_str(file, pdf_text):
    # "文件名", "合同类型", "姓名", "证件号", "手机号", "合同开始日期", "合同结束日期",
    # "合同签署时长", "试用期签署时长", "试用期开始日期", "试用期结束日期"

    # 第二代身份证18位：8位出生日期码，四位数年份+2位数月份+2位数日期。 3位顺序码，男性为奇数，女性为偶数。 最后再加一位校验码。
    id_card_str = "份证号码："
    id_card_index = pdf_text.find(id_card_str)
    id_card = pdf_text[id_card_index + 5 : id_card_index + 23]

    # 姓名
    name_str = "乙方:"
    name_str_eng = "乙方："
    name_index = pdf_text.find(name_str)
    if name_index == -1:
        name_index = pdf_text.find(name_str_eng)
    tmp_index = pdf_text.find("身份证")
    name = pdf_text[name_index + 3 : tmp_index]

    # 电话号码
    phone_str = "邮箱"
    phone_index = pdf_text.find(phone_str)
    phone = pdf_text[phone_index - 11 : phone_index]

    # 合同开始日期
    start_date_str = "同期限为："
    start_date_index = pdf_text.find(start_date_str)
    contract_start_date = pdf_text[start_date_index + 5 : start_date_index + 15]
    # TODO 如果包含 / ，说明日期分隔符是/，需要再次解析
    if "/" in contract_start_date:
        contract_start_date = extract_special_date(contract_start_date)
    contract_start_date = contract_start_date.replace("/", "-")
    # 结束日期
    end_date_str = "起至"
    end_date_index = pdf_text.find(end_date_str)
    contract_end_date = pdf_text[end_date_index + 2 : end_date_index + 12]
    if "/" in contract_end_date:
        contract_end_date = extract_special_date(contract_end_date)
    contract_end_date = contract_end_date.replace("/", "-")

    # 合同签署时长
    # 需要计算
    try:
        start = datetime.datetime.strptime(contract_start_date, "%Y-%m-%d")
        end = datetime.datetime.strptime(contract_end_date, "%Y-%m-%d")
        sign_period = (end - start).days // 365
    except Exception:
        sign_period = "无"

    # 试用期 （天为单位）
    trail_period = "无"

    # 试用期开始
    trail_period_start = "无"
    # 试用期结束
    trail_period_end = "无"

    return [
        file,
        "劳务合同",
        name,
        id_card,
        phone,
        contract_start_date,
        contract_end_date,
        sign_period,
        trail_period,
        trail_period_start,
        trail_period_end,
    ]


# 固定期限劳动合同
def A8M5E_handle_fix_time_contract(file, contract_csv_filename):
    # 解析PDF文本
    pdf_text = handle_extract_text(file)
    # 匹配字符串
    row_data = A8M5E_handle_fix_time_contract_match_str(file, pdf_text)
    # 写入 csv 文件中
    write_to_contract_csv(contract_csv_filename, row_data)


# 固定期限劳动合同 匹配函数
def A8M5E_handle_fix_time_contract_match_str(file, pdf_text):
    # "文件名", "合同类型", "姓名", "证件号", "手机号", "合同开始日期", "合同结束日期",
    # "合同签署时长", "试用期签署时长", "试用期开始日期", "试用期结束日期"

    # 第二代身份证18位：8位出生日期码，四位数年份+2位数月份+2位数日期。 3位顺序码，男性为奇数，女性为偶数。 最后再加一位校验码。
    id_card_str = "份证号码："
    id_card_index = pdf_text.find(id_card_str)
    id_card = pdf_text[id_card_index + 5 : id_card_index + 23]

    # 姓名
    name_str = "职工）姓名："
    name_index = pdf_text.find(name_str)
    sex_index = pdf_text.find("性别")
    name = pdf_text[name_index + 6 : sex_index]

    # 电话号码
    phone_str = "联系电话："
    phone_index = pdf_text.find(phone_str)
    phone = pdf_text[phone_index + 5 : phone_index + 16]

    # 合同开始日期
    start_date_str = "：从"
    start_date_index = pdf_text.find(start_date_str)
    contract_start_date = pdf_text[start_date_index + 2 : start_date_index + 12]
    # TODO 如果包含 / ，说明日期分隔符是/，需要再次解析
    print("处理前 -》 开始日期" + str(contract_start_date))
    if "/" in contract_start_date:
        contract_start_date = extract_special_date(contract_start_date)

    # 结束日期：这里的截取需要考虑到 试用期的也是一样格式，所以不能只用 “起至“
    # contract_start_date  的长度是变化的
    end_date_str = start_date_str + contract_start_date + "起至"
    end_date_index = pdf_text.find(end_date_str)
    contract_end_date = pdf_text[
        end_date_index + len(contract_start_date) + 4 : end_date_index + 24
    ]
    print("处理前 结束日期 -》" + str(contract_end_date))
    if "/" in contract_end_date:
        contract_end_date = extract_special_date(contract_end_date)

    # 对月和日进行处理，确保它们是两位数
    if "/" in contract_start_date:
        year, month, day = map(int, contract_start_date.split("/"))
        contract_start_date = f"{year}-{month:02d}-{day:02d}"
    print("处理后 -》 开始日期" + str(contract_start_date))
    # 对月和日进行处理，确保它们是两位数
    if contract_end_date is not None and "/" in contract_end_date:
        year, month, day = map(int, contract_end_date.split("/"))
        contract_end_date = f"{year}-{month:02d}-{day:02d}"
    print("处理后 结束日期 -》" + str(contract_end_date))

    # 合同签署时长
    sign_str = "、固定期限"
    sign_index = pdf_text.find(sign_str)
    temp_str = "从" + contract_start_date
    temp_index = pdf_text.find(temp_str)
    # 这里取到的是繁体中文数字
    sign_period_cn = pdf_text[sign_index + 5 : temp_index]
    # 转换成 数字
    try:
        sign_period = int(cn2an.cn2an(sign_period_cn, "smart"))
    except (AttributeError, ValueError):
        sign_period = "无"

    # 试用期 （天为单位）
    trail_period_str = "试用期"
    trail_period_index = pdf_text.find(trail_period_str)
    try:
        # 这里是月
        trail_period_month_cn = pdf_text[
            trail_period_index + 3 : trail_period_index + 4
        ]
        if trail_period_month_cn == "/":
            trail_period = "无"
        else:
            trail_period_month = cn2an.cn2an(trail_period_month_cn, "smart")
            # 转换成 天
            trail_period = int(trail_period_month) * 30
    except (AttributeError, ValueError):
        trail_period = "无"

    trail_period_start = "无"
    trail_period_end = "无"
    if trail_period != "无":
        # 试用期开始
        tp_start_str = "个月，从"
        tp_start_index = pdf_text.find(tp_start_str)
        trail_period_start = pdf_text[tp_start_index + 4 : tp_start_index + 14]
        # 如果包含 /， 那么说明日期分隔符是 /
        print("处理前 -》 试用期开始：" + str(trail_period_start))
        if "/" in trail_period_start:
            trail_period_start = extract_special_date(trail_period_start)

        # 试用期结束
        # 4 + 10 + 2 = 16，最后一个字符索引为 15
        trail_period_end_str = "，从" + trail_period_start + "起至"
        trail_period_end_index = pdf_text.find(trail_period_end_str)
        trail_period_end = pdf_text[
            trail_period_end_index
            + len(trail_period_start)
            + 4 : trail_period_end_index
            + 24
        ]
        print("处理前 -》 试用期结束：" + str(trail_period_end))
        if "其中" in trail_period_end:
            trail_period_end = trail_period_end[:-4]
        # 如果包含 /， 那么说明日期分隔符是 /
        if "/" in trail_period_end:
            trail_period_end = extract_special_date(trail_period_end)

        # 对月和日进行处理，确保它们是两位数
        if "/" in trail_period_start:
            year, month, day = map(int, trail_period_start.split("/"))
            trail_period_start = f"{year}-{month:02d}-{day:02d}"
        print("处理后 -》 试用期开始：" + str(trail_period_start))
        # 年月日
        if trail_period_end is not None and "/" in trail_period_end:
            year, month, day = map(int, trail_period_end.split("/"))
            trail_period_end = f"{year}-{month:02d}-{day:02d}"
        print("处理后 -》 试用期结束：" + str(trail_period_end))

    return [
        file,
        "固定期限劳动合同",
        name,
        id_card,
        phone,
        contract_start_date,
        contract_end_date,
        sign_period,
        trail_period,
        trail_period_start,
        trail_period_end,
    ]


# 提取特殊的日期分隔符
def extract_special_date(input_string):
    # 使用正则表达式匹配日期格式
    match = re.search(r"(\d{4}/\d{1,2}/\d{1,2})", input_string)
    # 检查是否有匹配，如果有则返回匹配的日期字符串，否则返回None
    if match:
        date_str = match.group(1)
        # # 对月和日进行处理，确保它们是两位数
        # year, month, day = map(int, date_str.split('/'))
        # formatted_date = f"{year}-{month:02d}-{day:02d}"
        return date_str
    else:
        return "无"


# =============================A8M5E 处理器=============================


# =============================A8GQK_Handler 处理器=============================
class A8GQK_Handler:
    def process(self, project_id):
        contract_csv_filename = get_contract_csv_name(project_id)
        resign_csv_filename = get_resign_csv_name(project_id)
        # 预处理
        pre_handle(contract_csv_filename, resign_csv_filename, project_id)

        total_dirs = sum([len(dirs) for _, dirs, _ in os.walk("./" + project_id)])
        print("总文件夹数量：", int(total_dirs))

        # 遍历处理当前文件夹下面所有子目录下的文件
        for root, dirs, files in os.walk("./" + project_id):
            total_dirs -= 1
            print("剩余文件夹数量：", int(total_dirs))

            for file in files:
                if file.endswith(".pdf"):
                    # 文件的全路径
                    file_path = os.path.join(root, file)
                    if "劳动合同" in file and not "补充协议" in file:
                        is_dianmi = "点米转签" in file
                        A8GQK_handle_contract(
                            file_path, contract_csv_filename, is_dianmi
                        )
                        print(
                            file_path
                            + " <===============================> "
                            + "劳动合同（点米转签）"
                            if is_dianmi
                            else "劳动合同" + " 解析完毕"
                        )

                    elif "续签协议" in file:
                        A8GQK_handle_continue(file_path, contract_csv_filename)
                        print(
                            file_path + " <===============================> 续签协议 解析完毕"
                        )

                    elif "-离职申请" in file:
                        A8GQK_handle_resign(file_path, resign_csv_filename)
                        print(file_path + " <===============================> 离职 解析完毕")

                    else:
                        print(file_path + " --> 不需要解析的文件类型 ")


def A8GQK_handle_resign(file_path, resign_csv_filename):
    # 解析PDF文本
    pdf_text = handle_extract_text(file_path)
    try:
        # 匹配字符串
        row_data = A8GQK_handle_resign_str(file_path, pdf_text)
    except:
        row_data = [file_path, "离职单", "", "", "异常"]
    # 写入 csv 文件中
    write_to_contract_csv(resign_csv_filename, row_data)


# 离职 匹配函数
def A8GQK_handle_resign_str(file, pdf_text):
    # 匹配 "文件名", "合同类型", "姓名", "证件号", "离职日期"

    name_str = "姓名"
    name_index = pdf_text.find(name_str)
    # 截止到联系电话前，都是姓名
    phone_str = "联系电"
    phone_index = pdf_text.find(phone_str)
    name = pdf_text[name_index + len(name_str) : phone_index]

    # 第二代身份证18位：8位出生日期码，四位数年份+2位数月份+2位数日期。 3位顺序码，男性为奇数，女性为偶数。 最后再加一位校验码。
    id_card_str = "身份证号码"
    id_card_index = pdf_text.find(id_card_str)
    id_card_sub = pdf_text[id_card_index + 5 : id_card_index + 23]
    # 有可能最后一位是 X
    if id_card_sub[:-1].isdigit():
        id_card = id_card_sub
    else:
        id_card = "异常"

    # 离职日期
    try:
        r_str = "员工本人填写）"
        r_index = pdf_text.find(r_str)
        resign_date = pdf_text[r_index + len(r_str): r_index + len(r_str) + 10]
    except Exception:
        resign_date = "异常"

    return [file, "离职单", name, id_card, resign_date]


def A8GQK_handle_continue(file_path, contract_csv_filename):
    # 解析PDF文本
    pdf_text = handle_extract_text(file_path)
    # 匹配字符串
    try:
        row_data = A8GQK_handle_continue_str(file_path, pdf_text)
    except Exception as e:
        print("e ", str(e))
        row_data = [file_path, "续签协议", "", "", "", "", "", "", "", "", "异常"]
        pass
    # 写入 csv 文件中
    write_to_contract_csv(contract_csv_filename, row_data)


def A8GQK_handle_continue_str(file, pdf_text):
    # "文件名", "合同类型", "姓名", "证件号", "手机号", "合同开始日期", "合同结束日期",
    # "合同签署时长", "试用期签署时长", "试用期开始日期", "试用期结束日期"

    # 第二代身份证18位：8位出生日期码，四位数年份+2位数月份+2位数日期。 3位顺序码，男性为奇数，女性为偶数。 最后再加一位校验码。
    id_card_str = "（以下简称乙方"
    id_card_index = pdf_text.find(id_card_str)
    id_card = pdf_text[id_card_index - 18 : id_card_index]

    name_str = "协议书乙方："
    name_index = pdf_text.find(name_str)
    id_card_sss = pdf_text.find(id_card)
    name = pdf_text[name_index + 6 : id_card_sss - 1 ]

    # 电话号码
    phone = "无"

    # 合同开始日期
    start_date_str = "签协议有效期从"
    start_date_index = pdf_text.find(start_date_str)
    contract_start_date = pdf_text[start_date_index + 7 : start_date_index + 17]
    # 结束日期：这里的截取需要考虑到 试用期的也是一样格式，所以不能只用 “起至“
    # 3 + 10 + 2 = 15，最后一个字符索引为 14
    end_date_str = start_date_str + contract_start_date + "起至"
    end_date_index = pdf_text.find(end_date_str)
    contract_end_date = pdf_text[
        end_date_index + 9 + len(contract_start_date) : end_date_index + 9 + len(contract_start_date) + 10
    ]

    # 合同签署时长
    # 需要计算
    try:
        start = datetime.datetime.strptime(contract_start_date, "%Y-%m-%d")
        end = datetime.datetime.strptime(contract_end_date, "%Y-%m-%d")
        sign_period = (end - start).days // 365
    except Exception:
        sign_period = "无"

    # 试用期 （天为单位）
    trail_period = "无"
    trail_period_start = "无"
    trail_period_end = "无"

    return [
        file,
        "续签协议",
        name,
        id_card,
        phone,
        contract_start_date,
        contract_end_date,
        sign_period,
        trail_period,
        trail_period_start,
        trail_period_end,
    ]


# 劳动合同（点米转签）
def A8GQK_handle_contract(file_path, contract_csv_filename, is_dianmi):
    # 解析PDF文本
    pdf_text = handle_extract_text(file_path)

    pdf_text = pdf_text[:1000]

    # 匹配字符串
    try:
        row_data = A8GQK_handle_contract_dianmi_match_str(
            file_path, pdf_text, is_dianmi
        )
    except:
        row_data = [
            file_path,
            "劳动合同（点米转签）" if is_dianmi else "劳动合同",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "异常",
        ]
        pass
    # 写入 csv 文件中
    write_to_contract_csv(contract_csv_filename, row_data)


# 劳动合同（点米转签）匹配函数
def A8GQK_handle_contract_dianmi_match_str(file, pdf_text, is_dianmi):
    # "文件名", "合同类型", "姓名", "证件号", "手机号", "合同开始日期", "合同结束日期",
    # "合同签署时长", "试用期签署时长", "试用期开始日期", "试用期结束日期"

    name_str = "职工）姓名："
    name_index = pdf_text.find(name_str)
    sex_str = "性别"
    sex_index = pdf_text.find(sex_str)
    name = pdf_text[name_index + 6 : sex_index]

    # 第二代身份证18位：8位出生日期码，四位数年份+2位数月份+2位数日期。 3位顺序码，男性为奇数，女性为偶数。 最后再加一位校验码。
    id_card_str = "身份证号码："
    id_card_index = pdf_text.find(id_card_str)
    id_card = pdf_text[id_card_index + 6 : id_card_index + 24]

    # 电话号码
    phone_str = "联系电话："
    phone_index = pdf_text.find(phone_str)
    phone = pdf_text[phone_index + 5 : phone_index + 16]

    # 合同开始日期
    start_date_str = "有固定期限：从"
    start_date_index = pdf_text.find(start_date_str)
    contract_start_date = pdf_text[start_date_index + 7 : start_date_index + 17]
    # 结束日期：这里的截取需要考虑到 试用期的也是一样格式，所以不能只用 “起至“
    # 3 + 10 + 2 = 15，最后一个字符索引为 14
    end_date_str = start_date_str + contract_start_date + "起至"
    end_date_index = pdf_text.find(end_date_str)
    contract_end_date = pdf_text[
        end_date_index + len(contract_start_date) + 9  : end_date_index + len(end_date_str) + 10
    ]

    # 合同签署时长
    # 需要计算
    try:
        start = datetime.datetime.strptime(contract_start_date, "%Y-%m-%d")
        end = datetime.datetime.strptime(contract_end_date, "%Y-%m-%d")
        sign_period = (end - start).days // 365
    except Exception:
        sign_period = "无"

    # 试用期 （天为单位）
    trail_period_str = "止，试用期"
    trail_period_index = pdf_text.find(trail_period_str)
    # 这里是月
    trail_period_month = pdf_text[trail_period_index + len(trail_period_str) : trail_period_index + len(trail_period_str) + 1]
    # 转换成 天
    try:
        trail_period = int(trail_period_month) * 30
    except (AttributeError, ValueError):
        trail_period = "无"

    trail_period_start = "无"
    trail_period_end = "无"
    if trail_period != "无":
        # 试用期开始 = 合同开始日期
        trail_period_start = contract_start_date
        try:
            # 试用期结束
            # 需要计算
            format_trail_period_start = datetime.strptime(
                trail_period_start, "%Y-%m-%d"
            )
            # 累加180天
            format_trail_period_start += timedelta(days=int(trail_period))
            # 转换输出格式
            trail_period_end = format_trail_period_start.strftime("%Y-%m-%d")
        except (AttributeError, ValueError) as e:
            print(str(e))
            trail_period_end = "无"

    return [
        file,
        "劳动合同（点米转签）" if is_dianmi else "劳动合同",
        name,
        id_card,
        phone,
        contract_start_date,
        contract_end_date,
        sign_period,
        trail_period,
        trail_period_start,
        trail_period_end,
    ]


# =============================A8GQK_Handler 处理器=============================

# =============================AZDKB_Handler 处理器=============================


class AZDKB_Handler:
    def process(self, project_id):
        contract_csv_filename = get_contract_csv_name(project_id)
        resign_csv_filename = get_resign_csv_name(project_id)
        # 预处理
        pre_handle(contract_csv_filename, resign_csv_filename, project_id)

        total_dirs = sum([len(dirs) for _, dirs, _ in os.walk("./" + project_id)])
        print("总文件夹数量：", int(total_dirs))

        # 遍历处理当前文件夹下面所有子目录下的文件
        for root, dirs, files in os.walk("./" + project_id):
            total_dirs -= 1
            print("剩余文件夹数量：", int(total_dirs))

            for file in files:
                if file.endswith(".pdf"):
                    # 文件的全路径
                    file_path = os.path.join(root, file)
                    if "专职体验顾问" in file:
                        print("解析文件名：" + file_path)
                        AA_handle_fix_time_contract(
                            file_path, contract_csv_filename, "无试用期" in file
                        )
                        print(
                            file_path + " <===============================> 专职体验顾问 解析完毕"
                        )

                    elif "的劳动合同.pdf" in file:
                        print("解析文件名：" + file_path)
                        AA_handle_contract(file_path, contract_csv_filename)
                        print(
                            file_path + " <===============================> 劳务合同 解析完毕"
                        )

                    else:
                        print(file_path + " --> 不需要解析的文件类型 ")


def AA_handle_contract(file, contract_csv_filename):
    # 解析PDF文本
    pdf_text = handle_extract_text(file)
    # 匹配字符串
    try:
        row_data = AB_handle_fix_time_contract_match_str(file, pdf_text)
    except:
        row_data = [file, "劳动合同", "", "", "", "", "", "", "", "", "异常"]
        pass
    # 写入 csv 文件中
    write_to_contract_csv(contract_csv_filename, row_data)


def AB_handle_fix_time_contract_match_str(file, pdf_text):
    # "文件名", "合同类型", "姓名", "证件号", "手机号", "合同开始日期", "合同结束日期",
    # "合同签署时长", "试用期签署时长", "试用期开始日期", "试用期结束日期"

    # 取前1000位就行
    pdf_text = pdf_text[:1000]

    # 第二代身份证18位：8位出生日期码，四位数年份+2位数月份+2位数日期。 3位顺序码，男性为奇数，女性为偶数。 最后再加一位校验码。
    id_card_str = "份证号码："
    id_card_index = pdf_text.find(id_card_str)
    id_card = pdf_text[id_card_index + 5 : id_card_index + 23]

    # 姓名
    name_str = "工）：姓名："
    name_index = pdf_text.find(name_str)
    tmp_index = pdf_text.find("性别")
    name = pdf_text[name_index + 6 : tmp_index]

    # 电话号码
    phone_str = "联系电话："
    phone_index = pdf_text.find(phone_str)
    phone = pdf_text[phone_index + 5 : phone_index + 16]

    # 合同开始日期
    start_date_str = "年，从"
    start_date_index = pdf_text.find(start_date_str)
    contract_start_date = pdf_text[start_date_index + 3 : start_date_index + 13]
    print("合同开始日期 -》" + str(contract_start_date))
    # 解析
    if "起" in contract_start_date:
        contract_start_date = contract_start_date[: contract_start_date.find("起")]
    # 使用正则表达式匹配中文日期格式
    if "年" in contract_start_date:
        # 将日期格式化为 "YYYY-MM-DD"，月份和日期补0
        contract_start_date = handle_date(contract_start_date)

    # 结束日期
    tem_str = "止。"
    tem_index = pdf_text.find(tem_str)
    # 3 + len() + 1 =
    ttt_str = start_date_str + contract_start_date + "起"
    ttt_index = pdf_text.find(ttt_str)
    contract_end_date = pdf_text[
        ttt_index + 3 + len(contract_start_date) + 1 : tem_index
    ]
    print("合同结束日期 -》" + str(contract_end_date))
    # 使用正则表达式匹配中文日期格式
    if "年" in contract_end_date:
        # 将日期格式化为 "YYYY-MM-DD"，月份和日期补0
        contract_end_date = handle_date(contract_end_date)

    # 对合同开始、结束日期进行格式话
    try:
        if len(contract_start_date) < 10:
            contract_start_date = formatter_date(contract_start_date)
    except:
        pass
    try:
        if len(contract_end_date) < 10:
            contract_end_date = formatter_date(contract_end_date)
    except:
        pass

    # 合同签署时长
    time_period = "，本劳动合同期限为"
    time_peroid_index = pdf_text.find(time_period)
    sign_period = pdf_text[time_peroid_index + 9 : time_peroid_index + 10]
    print("合同签署时长 -》" + str(sign_period))

    # 试用期的计算
    trail = "限的前"
    trail_end = "个月为试用期"
    l = pdf_text.find(trail)
    r = pdf_text.find(trail_end)
    trail_period_month = pdf_text[l + 3 : r]
    try:
        # 转换成 数字
        trail_period_month = cn2an.cn2an(trail_period_month, "smart")
        # 转换成天
        trail_period = int(trail_period_month) * 30
    except:
        trail_period = "无"

    # 试用期开始
    trail_period_start = "无"
    trail_period_end = "无"
    if trail_period != "无":
        trail_period_start = contract_start_date
        s_date = datetime.strptime(trail_period_start, "%Y-%m-%d")
        result_date = s_date + timedelta(trail_period)
        trail_period_end = result_date.strftime("%Y-%m-%d")
    print("试用期开始日期 -》" + str(trail_period_start))
    print("试用期结束日期 -》" + str(trail_period_end))

    return [
        file,
        "劳动合同",
        name,
        id_card,
        phone,
        contract_start_date,
        contract_end_date,
        sign_period,
        trail_period,
        trail_period_start,
        trail_period_end,
    ]


def formatter_date(date_str):
    # 将日期字符串解析为日期对象
    date_object = datetime.strptime(date_str, "%Y-%m-%d")

    # 将日期格式化为 "YYYY-MM-DD"，月份和日期补0
    return date_object.strftime("%Y-%m-%d")


def handle_date(date_year):
    match = re.search(r"(\d{4}年\d{1,2}月\d{1,2}日)", date_year)
    if match:
        # 提取匹配的日期字符串
        date_str = match.group(1)

        # 使用中文日期格式解析日期字符串
        date_object = datetime.strptime(date_str, "%Y年%m月%d日")

        # 将日期格式化为 "YYYY-MM-DD"，月份和日期补0
        date_year = date_object.strftime("%Y-%m-%d")
        return date_year
    else:
        return None


def AA_handle_fix_time_contract(file, contract_csv_filename, is_pratice):
    # 解析PDF文本
    pdf_text = handle_extract_text(file)
    # 匹配字符串
    try:
        row_data = AA_handle_fix_time_contract_match_str(file, pdf_text, is_pratice)
    except:
        row_data = [file, "专职体验顾问", "", "", "", "", "", "", "", "", "异常"]
        pass
    # 写入 csv 文件中
    write_to_contract_csv(contract_csv_filename, row_data)


def AA_handle_fix_time_contract_match_str(file, pdf_text, is_pratice):
    # "文件名", "合同类型", "姓名", "证件号", "手机号", "合同开始日期", "合同结束日期",
    # "合同签署时长", "试用期签署时长", "试用期开始日期", "试用期结束日期"

    # 取前1000位就行
    pdf_text = pdf_text[:1000]

    # 第二代身份证18位：8位出生日期码，四位数年份+2位数月份+2位数日期。 3位顺序码，男性为奇数，女性为偶数。 最后再加一位校验码。
    id_card_str = "份证号码："
    id_card_index = pdf_text.find(id_card_str)
    id_card = pdf_text[id_card_index + 5 : id_card_index + 23]

    # 姓名
    name_str = "方（员工）："
    name_index = pdf_text.find(name_str)
    tmp_index = pdf_text.find("居民身份")
    name = pdf_text[name_index + 6 : tmp_index]

    # 电话号码
    phone_str = "乙方（员工"
    phone_index = pdf_text.find(phone_str)
    phone = pdf_text[phone_index - 11 : phone_index]

    # 合同开始日期
    start_date_str = "定期限：自"
    start_date_index = pdf_text.find(start_date_str)
    contract_start_date = pdf_text[start_date_index + 5 : start_date_index + 15]
    # 结束日期
    end_date_str = "起至"
    end_date_index = pdf_text.find(end_date_str)
    tem_str = "止。"
    tem_index = pdf_text.find(tem_str)
    contract_end_date = pdf_text[end_date_index + 2 : tem_index]

    # 合同签署时长
    # 需要计算
    try:
        start_s = datetime.strptime(contract_start_date, "%Y-%m-%d")
        end_e = datetime.strptime(contract_end_date, "%Y-%m-%d")
        sign_period = (end_e - start_s).days // 365
        if sign_period < 1:
            sign_period = float(sign_period)
    except Exception:
        sign_period = "无"

    if is_pratice:
        # 试用期 （天为单位）
        trail_period = "无"
        # 试用期开始
        trail_period_start = "无"
        # 试用期结束
        trail_period_end = "无"
    else:
        # 开始日期
        start_date_str = "试用期自"
        start_date_index = pdf_text.find(start_date_str)
        trail_period_start = pdf_text[start_date_index + 4 : start_date_index + 14]
        # 结束日期
        end_date_str = start_date_str + trail_period_start + "起至"
        end_date_index = pdf_text.find(end_date_str)
        tem_str = "止，"
        tem_index = pdf_text.find(tem_str)
        trail_period_end = pdf_text[
            end_date_index
            + len(trail_period_start)
            + 6 : end_date_index
            + len(trail_period_start)
            + 16
        ]

        # 试用期 （天为单位）
        # 需要计算
        try:
            start_s = datetime.strptime(trail_period_start, "%Y-%m-%d")
            end_e = datetime.strptime(trail_period_end, "%Y-%m-%d")
            trail_period = (end_e - start_s).days
            if trail_period < 1:
                trail_period = float(trail_period)
        except Exception:
            trail_period = "无"

    return [
        file,
        "专职体验顾问",
        name,
        id_card,
        phone,
        contract_start_date,
        contract_end_date,
        sign_period,
        trail_period,
        trail_period_start,
        trail_period_end,
    ]


# =============================AZDKB_Handler 处理器=============================

# =============================A8DNC_Handler 处理器=============================
class A8DNC_Handler:
    def process(self, project_id):
        contract_csv_filename = get_contract_csv_name(project_id)
        resign_csv_filename = get_resign_csv_name(project_id)
        # 预处理
        pre_handle(contract_csv_filename, resign_csv_filename, project_id)

        total_dirs = sum([len(dirs) for _, dirs, _ in os.walk("./" + project_id)])
        print("总文件夹数量：", int(total_dirs))

        # 遍历处理当前文件夹下面所有子目录下的文件
        for root, dirs, files in os.walk("./" + project_id):
            total_dirs -= 1
            print("剩余文件夹数量：", int(total_dirs))

            for file in files:
                if file.endswith(".pdf"):
                    # 文件的全路径
                    file_path = os.path.join(root, file)
                    if "员工聘用协议" in file:
                        print("解析文件名：" + file_path)
                        XXX_handle_fix_time_contract(
                            file_path, contract_csv_filename
                        )
                        print(
                            file_path + " <===============================> 员工聘用协议 解析完毕"
                        )
                    elif "退休返聘协议书" in file:
                        print("解析文件名：" + file_path)
                        XXB_handle_fix_time_contract(file_path, contract_csv_filename)
                        print(file_path + " <===============================> 退休返聘协议书 解析完毕")

                    elif "离职单" in file:
                        print("解析文件名：" + file_path)
                        aaaaa_handle_resign(file_path, resign_csv_filename)
                        print(file_path + " <===============================> 离职单 解析完毕")

                    elif "离职申请单" in file:
                        print("解析文件名：" + file_path)
                        bbbbb_handle_resign(file_path, resign_csv_filename)
                        print(file_path + " <===============================> 离职单 解析完毕")


                    else:
                        print(file_path + " --> 不需要解析的文件类型 ")

def bbbbb_handle_resign(file_path, resign_csv_filename):
    # 解析PDF文本
    pdf_text = handle_extract_text(file_path)
    try:
        # 匹配字符串
        row_data = bbbbb_handle_resign_str(file_path, pdf_text)
    except:
        row_data = [file_path, "离职申请单", "", "", "异常"]
    # 写入 csv 文件中
    write_to_contract_csv(resign_csv_filename, row_data)

# 离职 匹配函数
def bbbbb_handle_resign_str(file, pdf_text):
    # 匹配 "文件名", "合同类型", "姓名", "证件号", "离职日期"

    name_str = "姓名"
    name_index = pdf_text.find(name_str)
    # 截止到联系电话前，都是姓名
    phone_str = "入职日期"
    phone_index = pdf_text.find(phone_str)
    name = pdf_text[name_index + len(name_str) : phone_index]

    # 第二代身份证18位：8位出生日期码，四位数年份+2位数月份+2位数日期。 3位顺序码，男性为奇数，女性为偶数。 最后再加一位校验码。
    id_card_str = "申请离职日期"
    id_card_index = pdf_text.find(id_card_str)
    i_sub_1 = pdf_text[id_card_index - 17 : id_card_index]
    i_1 = "身份证号码"
    i_i = pdf_text.find(i_1)
    i_sub_2 = pdf_text[i_i + len(i_1) : i_i + len(i_1) + 1]
    id_card = i_sub_1 + i_sub_2

    # 离职日期
    x_1 = "写）"
    x_iii = pdf_text.find(x_1)
    x_sub_1 = pdf_text[x_iii + 2 : x_iii + 3]
    r_str = "员工本人填"
    r_iii = pdf_text.find(r_str)
    resign_date = pdf_text[r_iii + len(r_str) : r_iii + len(r_str) + 9]

    return [file, "离职申请单", name, id_card, resign_date]

def aaaaa_handle_resign(file_path, resign_csv_filename):
    # 解析PDF文本
    pdf_text = handle_extract_text(file_path)
    try:
        # 匹配字符串
        row_data = aaaaa_handle_resign_str(file_path, pdf_text)
    except:
        row_data = [file_path, "离职单", "", "", "异常"]
    # 写入 csv 文件中
    write_to_contract_csv(resign_csv_filename, row_data)

# 离职 匹配函数
def aaaaa_handle_resign_str(file, pdf_text):
    # 匹配 "文件名", "合同类型", "姓名", "证件号", "离职日期"

    name_str = "本人"
    name_index = pdf_text.find(name_str)
    # 截止到联系电话前，都是姓名
    phone_str = "（身份证号码"
    phone_index = pdf_text.find(phone_str)
    name = pdf_text[name_index + len(name_str) : phone_index]

    # 第二代身份证18位：8位出生日期码，四位数年份+2位数月份+2位数日期。 3位顺序码，男性为奇数，女性为偶数。 最后再加一位校验码。
    id_card_str = "份证号码："
    id_card_index = pdf_text.find(id_card_str)
    id_card = pdf_text[id_card_index + 5 : id_card_index + 23]

    # 离职日期
    r_str = "日期："
    r_index = pdf_text.find(r_str)
    resign_date = pdf_text[r_index + len(r_str): r_index + len(r_str) + 10]

    return [file, "离职单", name, id_card, resign_date]


def XXB_handle_fix_time_contract(file_path, contract_csv_filename):
    # 解析PDF文本
    pdf_text = handle_extract_text(file_path)
    # 匹配字符串
    try:
        row_data = XXB_handle_fix_time_contract_match_str(file_path, pdf_text)
    except:
        row_data = [file_path, "退休返聘协议书", "", "", "", "", "", "", "", "", "异常"]
        pass
    # 写入 csv 文件中
    write_to_contract_csv(contract_csv_filename, row_data) 

def XXB_handle_fix_time_contract_match_str(file, pdf_text):
       # "文件名", "合同类型", "姓名", "证件号", "手机号", "合同开始日期", "合同结束日期",
    # "合同签署时长", "试用期签署时长", "试用期开始日期", "试用期结束日期"

    # 取前1000位就行
    pdf_text = pdf_text[:1000]

    # 第二代身份证18位：8位出生日期码，四位数年份+2位数月份+2位数日期。 3位顺序码，男性为奇数，女性为偶数。 最后再加一位校验码。
    id_card_str = "份证号码："
    id_card_index = pdf_text.find(id_card_str)
    id_card = pdf_text[id_card_index + 5 : id_card_index + 23]

    # 姓名
    name_str = "聘用人)："
    name_index = pdf_text.find(name_str)
    tmp_index = pdf_text.find("，身份证号码")
    name = pdf_text[name_index + 5 : tmp_index]

    # 电话号码
    phone_str = "乙方作为退休人员"
    phone_index = pdf_text.find(phone_str)
    phone = pdf_text[phone_index - 11 : phone_index]

    # 合同开始日期
    start_date_str = "聘用期限：自"
    start_date_index = pdf_text.find(start_date_str)
    s_len = len(start_date_str)
    contract_start_date = pdf_text[start_date_index + s_len : start_date_index + s_len + 10]
    print("合同开始日期 -》" + str(contract_start_date))

    # 结束日期
    tem_str = "止。二"
    tem_index = pdf_text.find(tem_str)
    contract_end_date = pdf_text[
        tem_index - 10 : tem_index
    ]
    print("合同结束日期 -》" + str(contract_end_date))

    # 对合同开始、结束日期进行格式话
    try:
        if len(contract_start_date) < 10:
            contract_start_date = formatter_date(contract_start_date)
    except:
        pass
    try:
        if len(contract_end_date) < 10:
            contract_end_date = formatter_date(contract_end_date)
    except:
        pass

    # 合同签署时长
    # 需要计算
    try:
        start_s = datetime.strptime(contract_start_date, "%Y-%m-%d")
        end_e = datetime.strptime(contract_end_date, "%Y-%m-%d")
        sign_period = (end_e - start_s).days // 365
        if sign_period < 1:
            sign_period = float(sign_period)
    except Exception:
        sign_period = "无"

    print("合同签署时长 -》" + str(sign_period))

    # 无试用期
    trail_period = "无"
    # 试用期开始
    trail_period_start = "无"
    trail_period_end = "无"

    return [
        file,
        "员工聘用协议",
        name,
        id_card,
        phone,
        contract_start_date,
        contract_end_date,
        sign_period,
        trail_period,
        trail_period_start,
        trail_period_end,
    ] 


def XXX_handle_fix_time_contract(file, contract_csv_filename):
    # 解析PDF文本
    pdf_text = handle_extract_text(file)
    # 匹配字符串
    try:
        row_data = XX_handle_fix_time_contract_match_str(file, pdf_text)
    except:
        row_data = [file, "劳动合同", "", "", "", "", "", "", "", "", "异常"]
        pass
    # 写入 csv 文件中
    write_to_contract_csv(contract_csv_filename, row_data)
    
def XX_handle_fix_time_contract_match_str(file, pdf_text):
    # "文件名", "合同类型", "姓名", "证件号", "手机号", "合同开始日期", "合同结束日期",
    # "合同签署时长", "试用期签署时长", "试用期开始日期", "试用期结束日期"

    # 取前1000位就行
    pdf_text = pdf_text[:1000]

    # 第二代身份证18位：8位出生日期码，四位数年份+2位数月份+2位数日期。 3位顺序码，男性为奇数，女性为偶数。 最后再加一位校验码。
    id_card_str = "份证号码："
    id_card_index = pdf_text.find(id_card_str)
    id_card = pdf_text[id_card_index + 5 : id_card_index + 23]

    # 姓名
    name_str = "工）姓名："
    name_index = pdf_text.find(name_str)
    tmp_index = pdf_text.find("性别")
    name = pdf_text[name_index + 5 : tmp_index]

    # 电话号码
    phone_str = "联系电话："
    phone_index = pdf_text.find(phone_str)
    phone = pdf_text[phone_index + 5 : phone_index + 16]

    # 合同开始日期
    start_date_str = "本合同期限自"
    start_date_index = pdf_text.find(start_date_str)
    s_len = len(start_date_str)
    contract_start_date = pdf_text[start_date_index + s_len : start_date_index + s_len + 10]
    print("合同开始日期 -》" + str(contract_start_date))
    # 解析
    # if "起" in contract_start_date:
    #     contract_start_date = contract_start_date[: contract_start_date.find("起")]
    # # 使用正则表达式匹配中文日期格式
    # if "年" in contract_start_date:
    #     # 将日期格式化为 "YYYY-MM-DD"，月份和日期补0
    #     contract_start_date = handle_date(contract_start_date)

    # 结束日期
    tem_str = "，期限"
    tem_index = pdf_text.find(tem_str)
    contract_end_date = pdf_text[
        tem_index - 10 : tem_index
    ]
    print("合同结束日期 -》" + str(contract_end_date))
    # # 使用正则表达式匹配中文日期格式
    # if "年" in contract_end_date:
    #     # 将日期格式化为 "YYYY-MM-DD"，月份和日期补0
    #     contract_end_date = handle_date(contract_end_date)

    # 对合同开始、结束日期进行格式话
    try:
        if len(contract_start_date) < 10:
            contract_start_date = formatter_date(contract_start_date)
    except:
        pass
    try:
        if len(contract_end_date) < 10:
            contract_end_date = formatter_date(contract_end_date)
    except:
        pass

    # 合同签署时长
    e_period = "，期限"
    e_peroid_index = pdf_text.find(e_period)
    d_str = "个月。"
    d_index = pdf_text.find(d_str)
    sign_period_month = pdf_text[e_peroid_index + 3 : d_index]
    # 月转换成 年
    try:
        sign_period = int(sign_period_month) / 12
    except:
        sign_period = sign_period_month
    print("合同签署时长 -》" + str(sign_period))

    # 无试用期
    trail_period = "无"
    # 试用期开始
    trail_period_start = "无"
    trail_period_end = "无"

    return [
        file,
        "员工聘用协议",
        name,
        id_card,
        phone,
        contract_start_date,
        contract_end_date,
        sign_period,
        trail_period,
        trail_period_start,
        trail_period_end,
    ]


# =============================A8DNC_Handler 处理器=============================

# =============================处理器=============================


# =============================主方法=============================
# TODO 维护对应的处理器map (每实现一个新的处理器，就要在这里维护)
project_handler_map = {
    "A8XX9": A8XX9_Handler,
    "A8VEX": A8VEX_Handler,
    "A8SXZ": A8SXZ_Handler,
    "A832G": A832G_Handler,
    "A8M5E": A8M5E_Handler,
    "AZDKB": AZDKB_Handler,
    "A8GQK": A8GQK_Handler,
    "A8DNC": A8DNC_Handler
}

# TODO 优化
# TODO 处理的文件数打印出来
# TODO 维护一个巨大的规则表，这个方法抽象掉很多方法
if __name__ == "__main__":
    print("开始解析程序\n")
    while True:
        # TODO 优化：用户可以输入多个项目id，进行遍历处理
        # 通过用户输入
        # project_ID = input("请输入需要处理的企业标识码，或输入 q 退出解析程序......\n")
        project_ID = "A8DNC"
        if project_ID == "q":
            print("退出解析程序，Bye Bye.......")
            break
        # 如果输入不存在的企业标识码，打印提示信息，退出程序
        project_ID = project_ID.upper()
        if project_ID not in project_handler_map:
            print("当前企业标识码【" + project_ID + "】暂未实现相应处理器......")
            print("请重新输入企业标识码，或输入 q 退出解析程序......\n")
            continue

        start_time = time.time()
        print("项目【" + project_ID + "】开始解析！开始时间：" + str(start_time))
        handler_class = project_handler_map[project_ID]
        handler = handler_class()
        handler.process(project_ID)
        end_time = time.time()
        print("项目【" + project_ID + "】解析完成！结束时间：" + str(end_time) + "\n")
        time_difference = end_time - start_time
        print(f"运行时间: {time_difference:.2f} 秒")
        # 解析完成，退出项目
        # exist = input("是否需要继续解析其他项目，输入任意键继续，输入 q 退出解析程序......\n")
        # if exist != 'q':
        #     continue

        print("退出解析程序，Bye Bye.......")
        break
# =============================主方法=============================
