import gradio as gr

from ui_deepdoc import process_pdf


def pdf_to_image(file):
    image_outputs_path = process_pdf(file)
    return image_outputs_path[0] if image_outputs_path else None


def create_app():
    # , favicon_path="path_to_your_icon.ico"
    with gr.Blocks(title="🎉pdf2word🎉") as demo:
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
            with gr.Column(scale=5):
                pdf_preview = gr.Image(label='PDF预览', height=600)

        file_ori.change(lambda x: pdf_to_image(x), inputs=[file_ori], outputs=[pdf_preview])
    return demo


if __name__ == '__main__':
    """
    python pdf2word_ui.py
    nohup python pdf2word_ui.py>0.log &
    """
    app = create_app()
    app.launch(server_name="0.0.0.0", server_port=812, share=False)
