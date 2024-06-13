import argparse
import os
import sys

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(
            os.path.dirname(
                os.path.abspath(__file__)),
            '.')))
from vision import init_in_out

parser = argparse.ArgumentParser()
args = parser.parse_args()
ocr_path = 'ocr_outputs'


input_file = r'C:\Users\liuch\AppData\Local\Temp\gradio\04b3b5b7fb87723f8e3082f97905b669184cb33f\sdt.pdf'
work_dir = os.path.dirname(input_file)
output_dir = os.path.join(work_dir, ocr_path)
args.inputs = input_file
args.output_dir = output_dir
images, outputs = init_in_out(args)
print(args)
print(images, outputs)