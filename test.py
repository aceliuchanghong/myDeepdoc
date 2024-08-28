import logging
import json
import re


# 匹配并替换图片
def replace_images(md_content, img_dict):
    def replacer(match):
        img_path = match.group(2)
        img_desc = match.group(1)
        if img_path in img_dict:
            replacement = img_dict[img_path]
            if img_desc:
                replacement = f"{replacement}\n\n*{img_desc}*"
            return replacement
        return match.group(0)  # 如果图片不在字典中，保持原样

    pattern = re.compile(r'!\[(.*?)\]\((.*?)\)')
    return pattern.sub(replacer, md_content)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

middle_path = r'C:\Users\liuch\Documents\00\hanrui_50W\middle.json'
md_path = r'C:\Users\liuch\Documents\00\hanrui_50W\NPD2308检验报告及检验记录.md'
new_md_path = r'C:\Users\liuch\Documents\00\hanrui_50W\NPD2308检验报告及检验记录_new.md'
base_path = r'C:\Users\liuch\Documents\00\hanrui_50W'
# 读取JSON文件
with open(middle_path, 'r', encoding='utf-8') as file:
    data = json.load(file)
# 读取Markdown文件内容
with open(md_path, 'r', encoding='utf-8') as file:
    content = file.read()
table_image_list = []
# 输出读取到的数据
for page_info in data['pdf_info']:
    for page_block in page_info['preproc_blocks']:
        if page_block['type'] == 'table':
            for table_image in page_block['blocks']:
                if table_image['type'] == 'table_body':
                    name = table_image['lines'][0]['spans'][0]['image_path']
                    table_image_list.append(name)

from vision import TableStructureRecognizer
from PIL import Image
from ui_deepdoc import get_table_data, get_instance

ocr = get_instance()
detr = TableStructureRecognizer()
ocr_pic_pil_image = []
ocr_pic_pil_image_name = []
result = {}
print(f"表格图片: {table_image_list}")

for i, pic in enumerate(table_image_list):
    img = Image.open(base_path + "/images/" + pic)
    thresholds, layouts = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1], []
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
    # print(result)


new_content = replace_images(content, result)
with open(new_md_path, 'w', encoding='utf-8') as file:
    file.write(new_content)
print(f"处理后的Markdown文件已保存至 {new_md_path}")
