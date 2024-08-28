import os
import time
import requests
import logging
import json
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
ip = "127.0.0.1"


# 匹配并替换图片
def replace_images(md_content, img_dict):
    def replacer(match):
        img_path = match.group(2)
        img_desc = match.group(1)
        if img_path in img_dict:
            replacement = img_dict[img_path]
            if img_desc:
                replacement = f"*{img_desc}:*\n{replacement}\n"
            return replacement
        return match.group(0)  # 如果图片不在字典中，保持原样

    pattern = re.compile(r'!\[(.*?)\]\((.*?)\)')
    return pattern.sub(replacer, md_content)


def pdf2md(file_ori_path, file_out_path, *, ocr_mode='auto'):
    logger.info("开始pdf转md")
    url = f"http://{ip}:9521/convert-pdf/"
    data = {
        "input_pdf_path": file_ori_path,
        "output_dir": file_out_path,
        "mode": ocr_mode
    }
    start_time = time.time()
    response = requests.post(url, params=data)
    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.info(f"cost: {elapsed_time} s")

    new_md_name = os.path.basename(file_ori_path).split('.')[0] + "_tsr.md"

    if response.status_code == 200:
        logger.info("开始md表格识别-获取图片")
        logger.info(f"Success: {response.json()}")
        output_md_path = response.json()['output_md_path']
        new_md_path = os.path.join(response.json()['output_dir'], new_md_name)
        image_path = response.json()['output_dir'] + "/" + 'images'
        middle_json_path = response.json()['output_dir'] + "/" + 'middle.json'
        logger.info(f"\noutput_md_path:{output_md_path}\nimage_path:{image_path}\nmiddle_json_path:{middle_json_path}")

        # 读取JSON文件,获取表格图片位置
        with open(middle_json_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        # 读取Markdown文件内容
        with open(output_md_path, 'r', encoding='utf-8') as file:
            content = file.read()
        # 获取表格列表
        table_image_list = []
        for page_info in data['pdf_info']:
            for page_block in page_info['preproc_blocks']:
                if page_block['type'] == 'table':
                    for table_image in page_block['blocks']:
                        if table_image['type'] == 'table_body':
                            name = table_image['lines'][0]['spans'][0]['image_path']
                            table_image_list.append(name)
        logger.debug(f"表格图片: {table_image_list}")

        from vision import TableStructureRecognizer
        from PIL import Image
        from ui_deepdoc import get_table_data, get_instance
        ocr = get_instance()
        detr = TableStructureRecognizer()
        result = {}
        logger.info("开始md表格识别-表格识别")
        start_time = time.time()
        for i, pic in enumerate(table_image_list):
            img = Image.open(response.json()['output_dir'] + "/images/" + pic)
            thresholds, layouts = [0.9, 0.8, 0.7, 0.6, 0.5], []
            for threshold in thresholds:
                layouts = detr([img], threshold)
                if len(layouts) > 0:
                    break
                logger.debug(threshold)
            for lyt in layouts:
                try:
                    table_data = get_table_data(img, lyt, ocr, True)
                    result["images/" + pic] = table_data
                except Exception as e:
                    print('err:', e)
        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.info(f"cost: {elapsed_time} s")
        logger.info("开始md表格识别-表格替换")
        new_content = replace_images(content, result)
        with open(new_md_path, 'w', encoding='utf-8') as file:
            file.write(new_content)
        logger.info(f"处理后的Markdown文件已保存至 {new_md_path}")
        return new_md_path
    else:
        logger.error(f"Error-status_code:{response.status_code}.response:{response.json()}")
        return None


if __name__ == '__main__':
    """
    source activate myDeepdoc
    cd /mnt/data/llch/deepdoc2/myDeepdoc
    python pdf2md.py
    """
    pdf_file1 = '/mnt/data/llch/ForMinerU/input/NPD2308检验报告及检验记录.pdf'
    pdf_file2 = '/mnt/data/llch/ForMinerU/input/NPD2308检验文件.pdf'
    pdf_file3 = '/mnt/data/llch/ForMinerU/input/NPD2308工艺文件.pdf'
    pdf_file4 = '/mnt/data/llch/ForMinerU/input/1900035003-吉林科新光机电技术开发有限公司-许宣瑜-201908-08670348.pdf'
    pdf_file = pdf_file2
    file_out_path = '/mnt/data/llch/ForMinerU/output'
    pdf_ocr_mode = 'auto'
    md_file = pdf2md(pdf_file, file_out_path, ocr_mode=pdf_ocr_mode)
    # print(md_file)
