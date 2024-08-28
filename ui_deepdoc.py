import gradio as gr
import pdfplumber
import os
import numpy as np
import concurrent.futures
from tqdm import tqdm
from vision import TableStructureRecognizer, Recognizer
from vision.ocr import OCR
from vision.seeit import draw_box
from PIL import Image
import pandas as pd
import re
import threading
from langchain_openai import ChatOpenAI

_instance = None


def get_instance():
    global _instance
    if _instance is None:
        ocr = OCR()
        _instance = ocr
    return _instance


class LLM:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = ChatOpenAI(
                    model='qwen57Bfp16:latest',
                    api_key='qwen2',
                    openai_api_base="http://112.48.199.202:11434/v1/"
                )
        return cls._instance


llm = LLM()


def get_table_data(img, tb_cpns, ocr, html=False):
    boxes = ocr(np.array(img))
    boxes = Recognizer.sort_Y_firstly(
        [{"x0": b[0][0], "x1": b[1][0],
          "top": b[0][1], "text": t[0],
          "bottom": b[-1][1],
          "layout_type": "table",
          "page_number": 0} for b, t in boxes if b[0][0] <= b[1][0] and b[0][1] <= b[-1][1]],
        np.mean([b[-1][1] - b[0][1] for b, _ in boxes]) / 3
    )

    def gather(kwd, fzy=10, ption=0.6):
        nonlocal boxes
        eles = Recognizer.sort_Y_firstly(
            [r for r in tb_cpns if re.match(kwd, r["label"])], fzy)
        eles = Recognizer.layouts_cleanup(boxes, eles, 5, ption)
        return Recognizer.sort_Y_firstly(eles, 0)

    headers = gather(r".*header$")
    rows = gather(r".* (row|header)")
    spans = gather(r".*spanning")
    clmns = sorted([r for r in tb_cpns if re.match(
        r"table column$", r["label"])], key=lambda x: x["x0"])
    clmns = Recognizer.layouts_cleanup(boxes, clmns, 5, 0.5)

    for b in boxes:
        ii = Recognizer.find_overlapped_with_threashold(b, rows, thr=0.3)
        if ii is not None:
            b["R"] = ii
            b["R_top"] = rows[ii]["top"]
            b["R_bott"] = rows[ii]["bottom"]

        ii = Recognizer.find_overlapped_with_threashold(b, headers, thr=0.3)
        if ii is not None:
            b["H_top"] = headers[ii]["top"]
            b["H_bott"] = headers[ii]["bottom"]
            b["H_left"] = headers[ii]["x0"]
            b["H_right"] = headers[ii]["x1"]
            b["H"] = ii

        ii = Recognizer.find_horizontally_tightest_fit(b, clmns)
        if ii is not None:
            b["C"] = ii
            b["C_left"] = clmns[ii]["x0"]
            b["C_right"] = clmns[ii]["x1"]

        ii = Recognizer.find_overlapped_with_threashold(b, spans, thr=0.3)
        if ii is not None:
            b["H_top"] = spans[ii]["top"]
            b["H_bott"] = spans[ii]["bottom"]
            b["H_left"] = spans[ii]["x0"]
            b["H_right"] = spans[ii]["x1"]
            b["SP"] = ii

    table_data = TableStructureRecognizer.construct_table(boxes, html=html)
    return table_data


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
    file_path = ans_txt[current_index]
    # print('file_path:', file_path)
    if file_path.endswith('.csv'):
        # print(pd.read_csv(file_path))
        return '', pd.read_csv(file_path)
    else:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return content, pd.DataFrame()


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


def normal_tsr_ocr(ocr, cut_pics, threshold, output_dir):
    # 展示图片
    ocr_pic_show_layout = []
    # image对象
    ocr_pic_pil_image = []
    # pd对象
    # ocr_pic_show_ans = []
    # 保存表格数据的文件路径列表
    table_data_paths = []

    labels = TableStructureRecognizer.labels
    detr = TableStructureRecognizer()

    for pic in cut_pics:
        # 之后layout的地址
        should_output = os.path.join(output_dir, os.path.basename(pic))
        # image对象
        img = Image.open(pic)

        ocr_pic_show_layout.append(should_output)
        ocr_pic_pil_image.append(img)

    layouts = detr(ocr_pic_pil_image, float(threshold))

    for i, lyt in enumerate(layouts):
        table_data = get_table_data(ocr_pic_pil_image[i], lyt, ocr)
        print('table_data:', table_data)
        df = pd.DataFrame(table_data, columns=['data'])
        df_split = df['data'].str.split(';', expand=True)
        csv_path = ocr_pic_show_layout[i] + ".csv"
        df_split.to_csv(csv_path, index=True)

        # ocr_pic_show_ans.append(df_split)
        table_data_paths.append(csv_path)

        # print("save result to: " + csv_path)
        lyt = [{
            "type": t["label"],
            "bbox": [t["x0"], t["top"], t["x1"], t["bottom"]],
            "score": t["score"]
        } for t in lyt]
        generate_img = draw_box(ocr_pic_pil_image[i], lyt, labels, float(threshold))
        generate_img.save(ocr_pic_show_layout[i], quality=95)

    return ocr_pic_show_layout, table_data_paths


def ocr_it(input_file, threshold, mode, cut_pics):
    start_default = 0
    show_table = 'tsr'
    ocr_path = 'ocr_outputs'
    tsr_output_dir = 'layouts_outputs'

    work_dir = os.path.dirname(input_file)
    file_name = os.path.basename(input_file)
    output_dir = os.path.join(work_dir, ocr_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    tsr_output_dir = os.path.join(work_dir, tsr_output_dir)
    if not os.path.exists(tsr_output_dir):
        os.makedirs(tsr_output_dir)
    print(input_file, threshold, mode)
    print(cut_pics)
    ocr = get_instance()

    if mode == '否':
        print("输出路径:", output_dir)
        ocr_pic_show_layout, ocr_pic_show_ans = normal_ocr(ocr, cut_pics, threshold, output_dir)
        return ocr_pic_show_layout, ocr_pic_show_ans, ocr_pic_show_layout[start_default], start_default
    else:
        print("输出路径:", tsr_output_dir)
        ocr_pic_show_layout, table_data_paths = normal_tsr_ocr(ocr, cut_pics, threshold, tsr_output_dir)
        return ocr_pic_show_layout, table_data_paths, ocr_pic_show_layout[start_default], start_default


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
            submit_button = gr.Button(value='开始识别', variant='primary', scale=4)
        # 操作
        with gr.Row():
            old_one = gr.Button(value='查看上一图片', variant='secondary', scale=5)
            next_one = gr.Button(value='查看下一图片', variant='secondary', scale=5)
        # 隐藏参数界面
        with gr.Row():
            cut_pic = gr.Dropdown(label='切分图片列表', choices=[], visible=False, allow_custom_value=True)
            ans_pic = gr.Dropdown(label='结果图片列表', choices=[], visible=False, allow_custom_value=True)
            ans_txt = gr.Dropdown(label='结果文档列表', choices=[], visible=False, allow_custom_value=True)
            current_index = gr.Textbox(label='结果展示index', visible=False)
        # 结果页面
        with gr.Row():
            pic_ocr = gr.Image(label='识别预览', scale=5)
            # 文本框
            ans = gr.Textbox(info='识别结果', scale=5, lines=20)
            # 显示表格数据
            ans_table = gr.DataFrame(label='表格结果', scale=5, visible=False)
        # 聊天部分
        with gr.Row():
            chatbot = gr.Chatbot()
        with gr.Row():
            with gr.Column(scale=8):
                msg = gr.Textbox(placeholder="输入想要询问的信息")
                gr.Examples(["合同的签订日期是什么时候？", "产品的数量和单价分别是多少？", "这份合同的流水号是什么？",
                             "这份合同的供方和需方分别是哪两家公司？", "供方和需方的传真号码分别是什么？",
                             "帮我将内容总结成字典形式", "供方和需方的联系电话分别是什么？", "SOB编号是多少?",
                             "采购订单的合同编号是什么？"],
                            msg)
            with gr.Column(scale=2):
                button_click = gr.Button('发送')
                clear = gr.Button("清除信息")

        def update_components(mode):
            threshold = 0.5 if mode == '是' else 0.9
            ans_visible = mode == '否'
            ans_table_visible = mode == '是'
            return threshold, gr.update(visible=ans_visible), gr.update(visible=ans_table_visible)

        def chat_response(user_message, history, ans_txt, current_index):
            # 首先添加用户消息到历史记录
            history = history + [[user_message, None]]

            # 然后生成机器人的回复
            current_index = int(current_index)
            file_path = ans_txt[current_index]
            with open(file_path, 'r', encoding='utf-8') as f:
                contents = f.read()

            prompt = "以下是图片OCR识别的结果:\n```\n"
            end = "\n```\n就上述信息回答以下问题,尽可能简短,仅给出答案即可:\n"
            msgs = prompt + contents + end + user_message
            print("\n" + msgs + "\n")
            bot_message = llm.invoke(msgs).content

            # 逐字符添加机器人的回复
            history[-1][1] = ""
            for character in bot_message:
                history[-1][1] += character
                import time
                time.sleep(0.001)
                yield history

        # movement
        str_mode.change(fn=update_components, inputs=str_mode, outputs=[threshold_slider, ans, ans_table])
        file_ori.change(fn=process_file, inputs=file_ori, outputs=[pic_show, cut_pic])
        submit_button.click(fn=ocr_it, inputs=[file_ori, threshold_slider, str_mode, cut_pic],
                            outputs=[ans_pic, ans_txt, pic_ocr, current_index])
        old_one.click(fn=select_file_old, inputs=[ans_pic, current_index], outputs=[pic_ocr, current_index])
        next_one.click(fn=select_file_new, inputs=[ans_pic, current_index], outputs=[pic_ocr, current_index])
        pic_ocr.change(fn=get_ans, inputs=[ans_txt, current_index], outputs=[ans, ans_table])

        button_click.click(fn=chat_response,
                           inputs=[msg, chatbot, ans_txt, current_index],
                           outputs=chatbot)
        msg.submit(fn=chat_response,
                   inputs=[msg, chatbot, ans_txt, current_index],
                   outputs=chatbot)
        clear.click(lambda: None, None, chatbot, queue=False)
    return demo


if __name__ == '__main__':
    """
    nohup python ui.py>0.log &
    """
    app = create_app()
    app.launch(server_name="0.0.0.0", server_port=5656, share=False)
