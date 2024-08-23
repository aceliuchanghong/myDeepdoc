import os
import subprocess
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI()


@app.post("/convert-pdf/")
async def convert_pdf(input_pdf_path: str, output_dir: str = "/mnt/data/llch/ForMinerU/output", mode: str = "auto"):
    # 检查输入PDF文件路径是否存在
    if not os.path.isfile(input_pdf_path):
        raise HTTPException(status_code=400, detail="Input PDF file does not exist.")
    name = os.path.splitext(os.path.basename(input_pdf_path))[0]

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 构建magic-pdf命令
    # https://github.com/opendatalab/MinerU
    command = ["magic-pdf", "-p", input_pdf_path, "-o", output_dir, "-m", mode]
    print(f"Executing command: {command}")
    # 执行命令
    try:
        process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return JSONResponse(
            content={"message": "PDF converted successfully",
                     "output_dir": os.path.join(output_dir, name, mode),
                     "output_md_path": os.path.join(output_dir, name, mode, name + ".md")})
    except subprocess.CalledProcessError as e:
        # 处理命令执行失败的情况
        return JSONResponse(content={"error": e.stderr.decode("utf-8")}, status_code=500)


if __name__ == "__main__":
    """
    source activate MinerU
    nohup python pdf2word_server_magic_pdf.py > magic_pdf_server.log &
    
    import requests
    # 设置API的URL和测试用的输入数据
    url = "http://112.48.199.7:9521/convert-pdf/"
    input_pdf_path = "/mnt/data/llch/ForMinerU/input/NPD2308检验报告及检验记录.pdf"
    output_dir = "/mnt/data/llch/ForMinerU/output"
    mode = "auto"
    # 创建POST请求的数据
    data = {
        "input_pdf_path": input_pdf_path,
        "output_dir": output_dir,
        "mode": mode
    }
    # 发送POST请求并获取响应
    response = requests.post(url, params=data)
    # 打印响应内容
    if response.status_code == 200:
        print("Success:", response.json())
    else:
        print("Error:", response.status_code, response.json())
    """
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9521)
