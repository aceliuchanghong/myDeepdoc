import gradio as gr
import pdfplumber
import os


def process_pdf(file_obj, zoomin=3):
    outputs = []
    this_pdf = pdfplumber.open(file_obj)
    images = [p.to_image(resolution=72 * zoomin).annotated for i, p in
              enumerate(this_pdf.pages)]
    for i, page in enumerate(images):
        filename = os.path.split(file_obj)[0] + "/" + os.path.split(file_obj)[-1] + f"_show_{i}.jpg"
        page.save(filename, quality=99)
        outputs.append(filename)
    return outputs


def process_file(file):
    file_extension = file.split('.')[-1]
    if file_extension == 'pdf':
        return process_pdf(file)
    else:
        return [file]


def select_file_old(file_dict, current_index):
    print(file_dict)
    current_index = int(current_index)
    if current_index > 0:
        return file_dict[current_index - 1], current_index - 1
    else:
        return file_dict[0], 0


def select_file_new(file_dict, current_index):
    print(file_dict)
    current_index = int(current_index)
    if current_index < len(file_dict) - 1:
        return file_dict[current_index + 1], current_index + 1
    else:
        return file_dict[len(file_dict) - 1], len(file_dict) - 1


def get_ans(ans_txt, current_index):
    current_index = int(current_index)
    with open(ans_txt[current_index], 'r') as f:
        content = f.read()
        return content


def ocr(input_file, threshold, mode):
    ocr_pic_show_layout = []
    ocr_pic_show_ans = []
    if mode == '否':
        test_file_pic = r'C:\Users\liuch\AppData\Local\Temp\gradio\04b3b5b7fb87723f8e3082f97905b669184cb33f\sdt.pdf_0.jpg'
        test_file_ans = r'C:\Users\liuch\AppData\Local\Temp\gradio\04b3b5b7fb87723f8e3082f97905b669184cb33f\sdt.pdf_0.jpg.txt'
        ocr_pic_show_layout.append(test_file_pic)
        ocr_pic_show_ans.append(test_file_ans)
        return ocr_pic_show_layout, ocr_pic_show_ans, ocr_pic_show_layout[0], 0
    else:
        return ocr_pic_show_layout, ocr_pic_show_ans, ocr_pic_show_layout[0], 0


def create_app():
    with gr.Blocks(title="Orc") as demo:
        with gr.Row():
            file_ori = gr.File(file_count='single', file_types=['image', '.pdf'],
                               label='上传文件', scale=5)
            pic_show = gr.Gallery(label='文件预览', scale=5, columns=4, container=True, preview=True)
        with gr.Row():
            threshold_slider = gr.Slider(label='置信度', minimum=0.2, interactive=True, maximum=0.9, value=0.5,
                                         step=0.1, scale=4, info="设置置信度")
            str_mode = gr.Dropdown(label='表格模式', choices=['是', '否'], value='否', scale=2, interactive=True,
                                   info='图片开启表格识别')
            submit_button = gr.Button(value='Generate', variant='primary', scale=4)
        # 隐藏参数界面
        with gr.Row():
            ans_pic = gr.Dropdown(label='结果图片列表', choices=[], visible=False, allow_custom_value=True)
            ans_txt = gr.Dropdown(label='结果文档列表', choices=[], visible=False, allow_custom_value=True)
            current_index = gr.Textbox(label='结果展示index', visible=False)
        with gr.Row():
            pic_ocr = gr.Image(label='识别预览', scale=6, height=900, width=500)
            ans = gr.Textbox(label='识别结果', scale=4, interactive=True, lines=25)
        with gr.Row():
            old_one = gr.Button(value='last one', variant='secondary', scale=5)
            next_one = gr.Button(value='next one', variant='secondary', scale=5)
        # movement
        file_ori.change(fn=process_file, inputs=file_ori, outputs=pic_show)
        submit_button.click(fn=ocr, inputs=[file_ori, threshold_slider, str_mode],
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
