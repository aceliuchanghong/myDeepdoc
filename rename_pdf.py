import argparse
import os
import shutil
import logging
from model import FileConventionFactory, LLM
from ui_deepdoc import process_file, ocr_it

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

file_convention_mapping = {
    "1": "PurchaseOrderContract",
    "2": "Agreement",
    "3": "ReviewForm",
    "4": "InvoiceAndAcceptance",
    "5": "Statement",
    "6": "VerificationDocument",
    "7": "AuthorizationLetter",
    "8": "TenderDocument"
}


def read_files(ocr_pic_show_ans):
    result = ""
    for file in ocr_pic_show_ans:
        with open(file, 'r', encoding='utf-8') as f:
            result += f.read()
    return result


def handle_file(file_path, opt):
    out_path = opt.out
    error_path = os.path.join(opt.out, 'error')
    if not os.path.exists(out_path):
        os.makedirs(out_path)
    if not os.path.exists(error_path):
        os.makedirs(error_path)

    llm = LLM()
    file_convention = file_convention_mapping[opt.type]
    new_file = FileConventionFactory.create_file_convention(file_convention)
    if opt.spe:
        new_file.type = '1'

    cut_pics, _ = process_file(file_path)
    _, ocr_pic_show_ans, _, _ = ocr_it(file_path, 0.9, '否', cut_pics)
    ocr_content = read_files(ocr_pic_show_ans)
    logger.debug(ocr_content)

    msgs = new_file.prompt_start + ocr_content + new_file.prompt_end + str(new_file.set_rule()) + "\n"

    retries = opt.retry
    for _ in range(retries):
        try:
            result = llm.invoke(msgs).content
            logger.debug(result)
            new_file.translate_json(result)
            new_name = new_file.name
            new_path = os.path.join(opt.out, new_name + '.pdf')
            shutil.copy(file_path, new_path)
            print(new_path)
            break  # 如果成功，退出循环
        except Exception as e:
            print(f"Error encountered: {e}. Retrying...")
            if _ == retries - 1:
                shutil.copy(file_path, error_path)


def main(opt):
    if opt.dir:
        for root, _, files in os.walk(opt.dir):
            for file in files:
                if file.lower().endswith('.pdf'):
                    file_path = os.path.join(root, file)
                    try:
                        handle_file(file_path, opt)
                    except Exception as e:
                        logger.error(f'error:{file_path}')
    else:
        try:
            handle_file(opt.f, opt)
        except Exception as e:
            logger.error(f'error:{opt.f}')


if __name__ == '__main__':
    """
    conda activate myDeepdoc
    python rename_pdf.py --type 1
    python rename_pdf.py --f C:\\Users\liuch\Documents\合合科技\测试文件样本4\采购合同2.pdf --out C:\\Users\liuch\Documents\\00
    python rename_pdf.py --f C:\\Users\liuch\Documents\合合科技\测试文件样本3\发票单\发票签收单2.pdf --type 4 --out C:\\Users\liuch\Documents\\00
    python rename_pdf.py --f C:\\Users\liuch\Documents\合合科技\测试文件样本3\发票单\发票签收单2.pdf --type 4 --spe 2 --out C:\\Users\liuch\Documents\\00
    python rename_pdf.py --dir C:\\Users\liuch\Documents\合合科技\测试文件样本4 --out C:\\Users\liuch\Documents\\00
    python rename_pdf.py --dir /mnt/data/llch/deepdoc2/myDeepdoc/input/测试文件样本4 --out /mnt/data/llch/deepdoc2/myDeepdoc/output/4
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--f', default='/mnt/data/llch/deepdoc2/myDeepdoc/input/测试文件样本4/采购合同.pdf',
                        help='pdf文档绝对路径')
    parser.add_argument('--type', default='1', help='文档类型')
    parser.add_argument('--out', default='/mnt/data/llch/deepdoc2/myDeepdoc/output/4', help='输出路径')
    parser.add_argument('--spe', default='', help='特别指定模式')
    parser.add_argument('--dir', default='', help='pdf文件夹绝对路径')
    parser.add_argument('--retry', default=3, type=int, help='重跑次数')
    opt = parser.parse_args()
    main(opt)
