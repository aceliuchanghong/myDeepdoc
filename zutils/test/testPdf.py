import pdfplumber
import os


def process_pdf(file_obj):
    outputs = []
    zoomin = 3
    this_pdf = pdfplumber.open(file_obj)
    # 72 * zoomin表示分辨率是72的倍数，zoomin是一个变量，表示放大倍数。
    images = [p.to_image(resolution=72 * zoomin).annotated for i, p in
              enumerate(this_pdf.pages)]
    for i, page in enumerate(images):
        filename = os.path.split(file_obj)[0] + "/" + os.path.split(file_obj)[-1] + f"_{i}.jpg"
        page.save(filename)
        outputs.append(filename)
    print('file_obj:', file_obj, '\nimages:', images, '\noutputs:', outputs)
    return outputs[0]


if __name__ == '__main__':
    file_obj = r'C:\Users\liuch\AppData\Local\Temp\gradio\04b3b5b7fb87723f8e3082f97905b669184cb33f\sdt.pdf'
    print(process_pdf(file_obj))
