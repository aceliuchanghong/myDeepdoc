import argparse
import os
import shutil

from model import FileConventionFactory, LLM
from ui_deepdoc import process_file, ocr_it

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


def main(opt):
    llm = LLM()
    file_convention = file_convention_mapping[opt.type]
    new_file = FileConventionFactory.create_file_convention(file_convention)
    if opt.spe:
        new_file.type = '1'

    cut_pics, _ = process_file(opt.f)
    _, ocr_pic_show_ans, _, _ = ocr_it(opt.f, 0.9, '否', cut_pics)
    ocr_content = read_files(ocr_pic_show_ans)
    # print(ocr_content)

    msgs = new_file.prompt_start + ocr_content + new_file.prompt_end + str(new_file.set_rule()) + "\n"
    result = llm.invoke(msgs).content
    new_file.translate_json(result)
    new_name = new_file.name
    new_path = os.path.join(opt.out, new_name + '.pdf')
    print(new_path)
    shutil.copy(opt.f, new_path)


if __name__ == '__main__':
    """
    conda activate myDeepdoc
    python rename_pdf.py --type 1
    python rename_pdf.py --f C:\\Users\liuch\Documents\合合科技\测试文件样本4\采购合同2.pdf --type 1
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--f', default=r'C:\Users\liuch\Documents\合合科技\测试文件样本4\采购合同.pdf',
                        help='pdf文档路径')
    parser.add_argument('--type', default='1', help='文档类型')
    parser.add_argument('--out', default=r'C:\Users\liuch\Desktop', help='输出路径')
    parser.add_argument('--spe', default='', help='特别指定')
    opt = parser.parse_args()
    main(opt)
