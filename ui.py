import gradio as gr
import pdfplumber
import os
import numpy as np

from vision import TableStructureRecognizer
from vision.ocr import OCR
from vision.seeit import draw_box
from PIL import Image


def process_pdf(file_obj, zoomin=3):
    outputs = []
    this_pdf = pdfplumber.open(file_obj)
    images = [p.to_image(resolution=72 * zoomin).annotated for i, p in
              enumerate(this_pdf.pages)]
    for i, page in enumerate(images):
        filename = os.path.split(file_obj)[0] + "/" + os.path.split(file_obj)[-1] + f"_show_{i}.jpg"
        page.save(filename, quality=95)
        outputs.append(filename)
    return outputs


def process_file(file):
    file_extension = file.split('.')[-1]
    if file_extension == 'pdf':
        cut_pics = process_pdf(file)
        return cut_pics, cut_pics
    else:
        return [file], [file]


def select_file_old(file_dict, current_index):
    # print(file_dict)
    current_index = int(current_index)
    if current_index > 0:
        return file_dict[current_index - 1], current_index - 1
    else:
        return file_dict[0], 0


def select_file_new(file_dict, current_index):
    # print(file_dict)
    current_index = int(current_index)
    if current_index < len(file_dict) - 1:
        return file_dict[current_index + 1], current_index + 1
    else:
        return file_dict[len(file_dict) - 1], len(file_dict) - 1


def get_ans(ans_txt, current_index):
    current_index = int(current_index)
    with open(ans_txt[current_index], 'r', encoding='utf-8') as f:
        content = f.read()
        return content


def ocr_task(ocr, img_path, threshold, output_dir):
    img_name = os.path.basename(img_path)
    img = Image.open(img_path)
    bxs = ocr(np.array(img))
    bxs = [(line[0], line[1][0]) for line in bxs]
    bxs = [{
        "text": t,
        "bbox": [b[0][0], b[0][1], b[1][0], b[-1][1]],
        "type": "ocr",
        "score": 1} for b, t in bxs if b[0][0] <= b[1][0] and b[0][1] <= b[-1][1]]
    img = draw_box(img, bxs, ["ocr"], threshold)
    ocr_name = os.path.join(output_dir, img_name)
    img.save(ocr_name, quality=95)
    with open(ocr_name + ".txt", "w+", encoding='utf-8') as f:
        f.write("\n".join([o["text"] for o in bxs]))
    # print(f"Processed image: {img_name}")
    return ocr_name


import concurrent.futures
from tqdm import tqdm


def normal_ocr(ocr, cut_pics, threshold, output_dir):
    ocr_pic_show_layout = []
    ocr_pic_show_ans = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # 提交任务到线程池
        futures = [executor.submit(ocr_task, ocr, img, threshold, output_dir) for img in cut_pics]

        # 使用tqdm创建进度条
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(cut_pics)):
            ocr_name = future.result()
            ocr_pic_show_layout.append(ocr_name)
            ocr_pic_show_ans.append(ocr_name + ".txt")

    # print("OCR finished")
    return ocr_pic_show_layout, ocr_pic_show_ans


def ocr(input_file, threshold, mode, cut_pics):
    start_default = 0
    show_table = 'tsr'
    show_layout = 'layout'
    ocr_path = 'ocr_outputs'

    work_dir = os.path.dirname(input_file)
    file_name = os.path.basename(input_file)
    output_dir = os.path.join(work_dir, ocr_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    # print(input_file, threshold, mode, cut_pics)
    # print(work_dir, output_dir)

    if mode == '否':
        ocr = OCR()
        ocr_pic_show_layout, ocr_pic_show_ans = normal_ocr(ocr, cut_pics, threshold, output_dir)
        return ocr_pic_show_layout, ocr_pic_show_ans, ocr_pic_show_layout[start_default], start_default
    else:
        print("表格模式")
        labels = TableStructureRecognizer.labels
        detr = TableStructureRecognizer()
        ocr = OCR()


def create_app():
    with gr.Blocks(title="Orc") as demo:
        # 输入页面
        with gr.Row():
            file_ori = gr.File(file_count='single', file_types=['image', '.pdf'],
                               label='上传文件', scale=5)
            pic_show = gr.Gallery(label='文件预览', scale=5, columns=4, container=True, preview=True)
        # 调控界面
        with gr.Row():
            threshold_slider = gr.Slider(label='置信度', minimum=0.2, interactive=True, maximum=0.9, value=0.9,
                                         step=0.1, scale=4, info="设置置信度")
            str_mode = gr.Dropdown(label='表格模式', choices=['是', '否'], value='否', scale=2, interactive=True,
                                   info='图片开启表格识别,精度下降')
            submit_button = gr.Button(value='Generate', variant='primary', scale=4)
        # 操作
        with gr.Row():
            old_one = gr.Button(value='last one', variant='secondary', scale=5)
            next_one = gr.Button(value='next one', variant='secondary', scale=5)
        # 隐藏参数界面
        with gr.Row():
            cut_pic = gr.Dropdown(label='切分图片列表', choices=[], visible=False, allow_custom_value=True)
            ans_pic = gr.Dropdown(label='结果图片列表', choices=[], visible=False, allow_custom_value=True)
            ans_txt = gr.Dropdown(label='结果文档列表', choices=[], visible=False, allow_custom_value=True)
            current_index = gr.Textbox(label='结果展示index', visible=False)
        # 结果页面
        with gr.Row():
            pic_ocr = gr.Image(label='识别预览', scale=5)
            ans = gr.Textbox(label='识别结果', scale=5, lines=20)
        # movement
        str_mode.change(fn=lambda x: 0.5 if x == '是' else 0.9, inputs=str_mode, outputs=threshold_slider)
        file_ori.change(fn=process_file, inputs=file_ori, outputs=[pic_show, cut_pic])
        submit_button.click(fn=ocr, inputs=[file_ori, threshold_slider, str_mode, cut_pic],
                            outputs=[ans_pic, ans_txt, pic_ocr, current_index])
        old_one.click(fn=select_file_old, inputs=[ans_pic, current_index], outputs=[pic_ocr, current_index])
        next_one.click(fn=select_file_new, inputs=[ans_pic, current_index], outputs=[pic_ocr, current_index])
        pic_ocr.change(fn=get_ans, inputs=[ans_txt, current_index], outputs=ans)
    return demo


if __name__ == '__main__':
    """
    nohup python ui.py>0.log &
    """
    app = create_app()
    app.launch(server_name="0.0.0.0", server_port=5656, share=False)
