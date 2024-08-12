import os
import gradio as gr
from ui_deepdoc import process_pdf


def pdf_to_image(file):
    image_outputs_path = process_pdf(file)
    return image_outputs_path[0] if image_outputs_path else None


def pdf2md(file_ori_path, file_out_path, ocr_mode='auto', table_pic=False):
    pass


def md2word(file_input_path, file_output_path, *, translate=False, language='zh'):
    pass


def create_app():
    with gr.Blocks(title="🎉pdf2word🎉") as demo:
        demo.css = f"""
                <style>
                    link[rel="icon"] {{
                        content: url("./files/triumphal_arch_building_icon_263770.ico");
                    }}
                </style>
                """
        gr.Markdown("""
                ### PDF 转 Word 
                - 上传pdf文档
                - 选择默认选项或者自定义选项
                - 点击开始转化
                - 下载转化好的文档
                """)
        with gr.Row():
            with gr.Column(scale=5):
                file_ori = gr.File(file_count='single', file_types=['.pdf'], label='点击上传PDF文件', height=600)
                file_ori.GRADIO_CACHE = upload_default_path
            with gr.Column(scale=5):
                pdf_preview = gr.Image(label='PDF预览', height=600)
        with gr.Row():
            with gr.Column(scale=6):
                with gr.Accordion("基本参数设置", open=False):
                    pdf_ocr_mode = gr.Dropdown(label='文档识别模式', choices=['auto', 'ocr', 'txt'], value='auto',
                                               interactive=True, info='效果不好建议尝试ocr')
                    threshold_slider = gr.Slider(label="置信度", minimum=0.1, maximum=0.9, value=0.5, interactive=True,
                                                 step=0.1, info="设置置信度")
                    save_pic_or_table_data = gr.Dropdown(label='pdf转化为word时,其中表格是否保存为图片到word',
                                                         choices=['是', '否'], value='是', interactive=True,
                                                         info='否-则保存为表格')
                    translate_it = gr.Dropdown(label='是否翻译文档', choices=['否', '是'], value='否', interactive=True,
                                               info='翻译文档成指定语言')
                    language = gr.Dropdown(label='选择要翻译成什么语言的文档', choices=['English', '中文'],
                                           value='中文', interactive=True, info='翻译文档语言选择', visible=False)
            with gr.Column(scale=4):
                generate_button = gr.Button("开始转化", variant='primary',
                                            icon='./files/archery_bow_arch_sport_icon_228555.ico')
        with gr.Row():
            with gr.Column(scale=4):
                file_new = gr.File(file_count='single', label='转化完成的结果文件', visible=False)
            with gr.Column(scale=1):
                download = gr.Button("下载", variant='secondary', visible=False)
            file_new_preview = gr.Markdown(label='转化预览', value='### 初始默认', visible=False)

        def update_language(mode):
            language_visible = True if mode == '是' else False
            return gr.update(visible=language_visible)

        def download_new_file(file_path):
            return file_path

        # 第一部分
        file_ori.change(lambda x: pdf_to_image(x), inputs=[file_ori], outputs=[pdf_preview])
        # 第二部分
        translate_it.change(fn=update_language, inputs=[translate_it], outputs=[language])
        # 第三部分
        download.click(download_new_file, inputs=[file_new], outputs=[file_new])
    return demo


if __name__ == '__main__':
    """
    python pdf2word_ui.py
    nohup python pdf2word_ui.py>0.log &
    """
    upload_default_path = './z_pdf2word_default_dir'
    if not os.path.exists(upload_default_path):
        os.makedirs(upload_default_path)
    app = create_app()
    app.launch(server_name="0.0.0.0", server_port=812, share=False)
