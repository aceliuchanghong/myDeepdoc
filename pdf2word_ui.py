import gradio as gr
from ui_deepdoc import process_pdf
import threading
from langchain_openai import ChatOpenAI
import requests
import logging
import pypandoc
import os

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def md2word(file_input_path):
    name = os.path.basename(file_input_path).split('.')[0] + ".docx"
    file_out = os.path.join(file_out_path, name)

    # Convert markdown to docx using pypandoc
    output = pypandoc.convert_file(file_input_path, 'docx', outputfile=file_out)

    return file_out


class Translate_LLM:
    _instance = None
    _lock = threading.Lock()
    """
    curl http://112.48.199.7:11434/api/generate -d '{
      "model": "mistral-nemo",
      "prompt": "你好,给我讲个笑话",
      "stream": false
    }'
    """

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = ChatOpenAI(
                    model='mistral-nemo',
                    api_key='mistral-nemo',
                    openai_api_base="http://112.48.199.7:11434/v1/"
                )
        return cls._instance


def pdf_to_image(file):
    image_outputs_path = process_pdf(file)
    return image_outputs_path[0], [] if image_outputs_path else [], []


def pdf2md(file_ori_path, file_out_path, *, ocr_mode='auto', table_pic=True,
           threshold=0.5):
    if file_ori_path.endswith('.md'):
        return file_ori_path
    url = "http://112.48.199.7:9521/convert-pdf/"
    data = {
        "input_pdf_path": file_ori_path,
        "output_dir": file_out_path,
        "mode": ocr_mode
    }
    response = requests.post(url, params=data)
    if response.status_code == 200:
        print(f"Success: {response.json()}")
        output_md_path = response.json()['output_md_path']
        print(output_md_path)
        if table_pic:
            return output_md_path

    else:
        logger.error(f"Error-status_code:{response.status_code}.response:{response.json()}")
        return None


def translate_md(file_ori, translate_it, language):
    if translate_it:
        print("需要翻译")
        pass
    else:
        return file_ori


def run_program(file_ori, pdf_ocr_mode, save_pic_or_table, threshold_slider, translate_it, language, pdf2md_hide):
    save_pic_or_table = True if save_pic_or_table == "是" else False
    translate_it = True if translate_it == "是" else False
    # 如果有转化好的md文件,就不转化了
    if pdf2md_hide:
        file_ori = pdf2md_hide
    print(f"starting:{file_ori}")

    md_file = pdf2md(file_ori, file_out_path, ocr_mode=pdf_ocr_mode, table_pic=save_pic_or_table,
                     threshold=threshold_slider)
    if not md_file:
        logger.error("文件识别失败")
        return None, None, None, None
    print(f"md_file:{md_file}")

    translate_md_file = translate_md(md_file, translate_it, language)
    if not translate_md_file:
        logger.error("文件翻译失败")
        return None, None, None, None
    print(f"translate_md_file:{translate_md_file}")

    word_file = md2word(translate_md_file)
    if not word_file:
        logger.error("文件转化word失败")
        return None, None, None, None
    print(f"word_file:{word_file}")

    with open(md_file, 'r', encoding='utf-8') as f:
        translate_md_file = f.read()

    return word_file, gr.update(value=translate_md_file, visible=True), md_file, translate_md_file, gr.update(
        visible=True)


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
                - 模型启动23s+pdf每页识别0.9s+表格识别每个0.6s+翻译每页0.2s
                """)
        with gr.Row():
            with gr.Column(scale=5):
                file_ori = gr.File(file_count='single', file_types=['.pdf'], label='点击上传PDF文件', height=600)
                file_ori.GRADIO_CACHE = upload_default_path
            with gr.Column(scale=5):
                pdf_preview = gr.Image(label='PDF预览', height=600)
        with gr.Row():
            with gr.Column(scale=5):
                with gr.Accordion("基本参数设置", open=False):
                    pdf_ocr_mode = gr.Dropdown(label='文档识别模式', choices=['auto', 'ocr', 'txt'], value='auto',
                                               interactive=True,
                                               info='默认auto,若文件公式多或者auto效果不好建议尝试ocr')
                    save_pic_or_table = gr.Dropdown(label='表格保存为图片(速度快)', choices=['是', '否'],
                                                    value='是',
                                                    interactive=True,
                                                    info='pdf转化为word时,文件中表格是否保存为图片,默认是,否-则保存为表格(精度下降)')
                    threshold_slider = gr.Slider(label="置信度", minimum=0.1, maximum=0.9, value=0.5, step=0.1,
                                                 interactive=True, visible=False,
                                                 info="默认0.5,识别置信度,值越大结果越准确,但是可能忽略很多不准确的结果")
                    translate_it = gr.Dropdown(label='翻译文档', choices=['否', '是'], value='否', interactive=True,
                                               info='翻译文档成指定语言')
                    language = gr.Dropdown(label='选择翻译语言', choices=['English', '中文'],
                                           value='中文', interactive=True, info='选择要翻译为的语言',
                                           visible=False)
            with gr.Column(scale=5):
                generate_button = gr.Button("开始转化", variant='primary',
                                            icon='./files/archery_bow_arch_sport_icon_228555.ico')
        with gr.Row():
            file_new = gr.File(file_count='single', label='转化完成的结果文件', visible=False)

            download = gr.Button("下载", variant='secondary', visible=False)
            file_new_preview = gr.Markdown(label='转化预览', value='### 初始默认', visible=False)
        with gr.Row():
            pdf2word_translate_hide = gr.Dropdown(label='pdf转化的默认word翻译之后的文件,此处仅存储', visible=False,
                                                  allow_custom_value=True)
            pdf2md_hide = gr.Dropdown(label='pdf转化的默认md文件,此处仅存储', visible=False, allow_custom_value=True)

        def set_language(mode):
            language_visible = True if mode == '是' else False
            return gr.update(visible=language_visible)

        def set_table(mode):
            language_visible = True if mode == '否' else False
            return gr.update(visible=language_visible)

        # 第一部分
        file_ori.change(lambda x: pdf_to_image(x), inputs=[file_ori], outputs=[pdf_preview, pdf2md_hide])
        # 第二部分
        save_pic_or_table.change(fn=set_table, inputs=[save_pic_or_table], outputs=[threshold_slider])
        translate_it.change(fn=set_language, inputs=[translate_it], outputs=[language])
        # 第三部分
        download.click(lambda x: x, inputs=[file_new], outputs=[file_new])
        # core
        generate_button.click(fn=run_program,
                              inputs=[
                                  file_ori, pdf_ocr_mode, save_pic_or_table, threshold_slider, translate_it, language,
                                  # 保存的临时文件参数
                                  pdf2md_hide
                              ],
                              outputs=[file_new, file_new_preview, pdf2word_translate_hide, pdf2md_hide, download])
    return demo


if __name__ == '__main__':
    """
    conda activate myDeepdoc
    cd /mnt/data/llch/deepdoc2/myDeepdoc
    python pdf2word_ui.py
    nohup python pdf2word_ui.py>ss_pdf2word_ui.log &
    """
    file_out_path = '/mnt/data/llch/ForMinerU/output'
    upload_default_path = './z_pdf2word_default_dir'
    if not os.path.exists(upload_default_path):
        os.makedirs(upload_default_path)
    llm = Translate_LLM()
    app = create_app()
    app.launch(server_name="0.0.0.0", server_port=812, share=False)
