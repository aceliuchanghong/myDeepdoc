from abc import ABC, abstractmethod
import threading
from langchain_openai import ChatOpenAI
import json
import re


class LLM:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = ChatOpenAI(
                    model="qwen57Bfp16:latest",
                    api_key="qwen2",
                    openai_api_base="http://112.48.199.202:11434/v1/"
                )
        return cls._instance


class NamingRule(ABC):
    def __init__(self):
        self.name = None
        self.coon = "-"
        self.result_dict = {}
        self.prompt_start = "以下是图片OCR识别的结果:\n```\n"
        self.prompt_end = "\n```\n就上述信息填充下面字典,不知道或者不确定的字段填充DK,仅返回该字典结果json文本,不要多给出文字:\n"

    @abstractmethod
    def set_rule(self, **kwargs) -> dict:
        pass

    @abstractmethod
    def set_name(self, **kwargs):
        pass

    def __str__(self):
        return f"File(name={self.name})"

    def translate_json(self, json_string) -> dict:
        try:
            json_string = json_string.replace("json", "").replace("`", "").replace("\n", "")
            new_dict = json.loads(json_string)
            self.result_dict = new_dict
            self.set_name()
            return new_dict
        except json.JSONDecodeError:
            try:
                json_string = re.sub(r"```json|```", "", json_string)
                json_string = re.sub(r"\s+", " ", json_string).strip()
                # print("re:", json_string)
                new_dict = json.loads(json_string)
                self.result_dict = new_dict
                self.set_name()
                return new_dict
            except json.JSONDecodeError as e:
                print("JSONDecodeError:", e)
                return {}


class PurchaseOrderContractConvention(NamingRule):
    """
    购销类(订单合同)
    单号+客户名称+业务专员名字
    eg:S0B202202-00899-北京xxx(全称)-曾xx
    """

    def __init__(self, **kwargs):
        super(PurchaseOrderContractConvention, self).__init__()
        self.SOB = None
        self.customer_name = None
        self.specialist_name = None

    def set_rule(self, **kwargs) -> dict:
        return {
            "SOB": "[此处填充SOB编号]",
            "customer_name": "[此处填充客户名称]",
            "specialist_name": "[此处填充业务专员名字]"
        }

    def set_name(self, **kwargs):
        attributes = self.result_dict
        self.SOB = attributes.get("SOB", "DK")
        self.customer_name = attributes.get("customer_name", "DK")
        self.specialist_name = attributes.get("specialist_name", "DK")
        self.name = self.SOB + self.coon + self.customer_name + self.coon + self.specialist_name


class AgreementConvention(NamingRule):
    """
    协议类
    客户名称+**协议+业务专员名字+申请年月
    eg:江苏xxx系统有限公司(全称)-框架协议-吴xx-202005
    """

    def __init__(self, **kwargs):
        super(AgreementConvention, self).__init__()
        self.customer_name = None
        self.frame_agreement = None
        self.specialist_name = None
        self.apply_date = None

    def set_rule(self, **kwargs) -> dict:
        return {
            "customer_name": "[此处填充客户名称]",
            "frame_agreement": "[此处填充协议类型]",
            "specialist_name": "[此处填充业务专员名字]",
            "apply_date": "[此处填充申请年月eg:202005]"
        }

    def set_name(self, **kwargs):
        attributes = self.result_dict
        self.customer_name = attributes.get("customer_name", "DK")
        self.frame_agreement = attributes.get("frame_agreement", "DK")
        self.specialist_name = attributes.get("specialist_name", "DK")
        self.apply_date = attributes.get("apply_date", "DK")
        self.name = self.customer_name + self.coon + self.frame_agreement + \
                    self.coon + self.specialist_name + self.coon + self.apply_date


class ReviewFormConvention(NamingRule):
    """
    JP评审单类
    单号+客户名称(全称)+业务专员
    """

    def __init__(self, **kwargs):
        super(ReviewFormConvention, self).__init__()
        self.SOB = None
        self.customer_name = None
        self.specialist_name = None

    def set_rule(self, **kwargs) -> dict:
        return {
            "SOB": "[此处填充单号]",
            "customer_name": "[此处填充客户名称]",
            "specialist_name": "[此处填充业务专员名字]"
        }

    def set_name(self, **kwargs):
        attributes = self.result_dict
        self.SOB = attributes.get("SOB", "DK")
        self.customer_name = attributes.get("customer_name", "DK")
        self.specialist_name = attributes.get("specialist_name", "DK")
        self.name = self.SOB + self.coon + self.customer_name + self.coon + self.specialist_name


class InvoiceAndAcceptanceConvention(NamingRule):
    """
    发票签收单与产品验收单类
    发票签收:客户名称+业务专员名字+年月_发票号
    产品验收:客户名称(全称)-产品验收单-业务专员名字-年月
    """

    def __init__(self, **kwargs):
        super(InvoiceAndAcceptanceConvention, self).__init__()
        self.type_model = {
            '0': "发票签收",
            '1': "产品验收",
        }
        self.customer_name = None
        self.specialist_name = None
        self.invoice = None  # 发票号
        self.apply_date = None
        self.receipt = None  # 产品验收单号
        self.type = '0'

    def set_rule(self, **kwargs) -> dict:
        if self.type == '1':
            return self.set_rule_1()
        else:
            return self.set_rule_0()

    @staticmethod
    def set_rule_0() -> dict:
        return {
            "customer_name": "[此处填充客户名称]",
            "specialist_name": "[此处填充业务专员名字]",
            "apply_date": "[此处填充开票日期年月eg:202005]",
            "invoice": "[此处填充发票号]"
        }

    @staticmethod
    def set_rule_1() -> dict:
        return {
            "customer_name": "[此处填充客户名称]",
            "specialist_name": "[此处填充业务专员名字]",
            "apply_date": "[此处填充年月eg:202005]",
            "receipt": "[此处填充产品验收单号]"
        }

    def set_name(self, **kwargs):
        attributes = self.result_dict
        self.customer_name = attributes.get("customer_name", "DK")
        self.specialist_name = attributes.get("specialist_name", "DK")
        self.apply_date = attributes.get("apply_date", "DK")
        if self.type == 1:
            self.receipt = attributes.get("receipt", "DK")
            self.name = f"{self.customer_name}{self.coon}{self.receipt}{self.coon}{self.specialist_name}{self.coon}{self.apply_date}"
        else:
            self.invoice = attributes.get("invoice", "DK").replace(",","-")
            self.name = f"{self.customer_name}{self.coon}{self.specialist_name}{self.coon}{self.apply_date}{self.coon}{self.invoice}"


class StatementConvention(NamingRule):
    """
    对账单类
    客户名称+业务专员名字+年月
    """

    def __init__(self, **kwargs):
        super(StatementConvention, self).__init__()
        self.customer_name = None
        self.specialist_name = None
        self.apply_date = None

    def set_rule(self, **kwargs) -> dict:
        return {
            "customer_name": "[此处填充客户名称]",
            "specialist_name": "[此处填充业务专员名字]",
            "apply_date": "[此处填充年月eg:202005]"
        }

    def set_name(self, **kwargs):
        attributes = self.result_dict
        self.customer_name = attributes.get("customer_name", "DK")
        self.specialist_name = attributes.get("specialist_name", "DK")
        self.apply_date = attributes.get("apply_date", "DK")
        self.name = f"{self.customer_name}{self.coon}{self.specialist_name}{self.coon}{self.apply_date}"


class VerificationDocumentConvention(NamingRule):
    """
    核销单类
    客户名称+业务专员名字+年份+核销金额
    """

    def __init__(self, **kwargs):
        super(VerificationDocumentConvention, self).__init__()
        self.customer_name = None
        self.specialist_name = None
        self.apply_year_date = None
        self.write_off = None

    def set_rule(self, **kwargs) -> dict:
        return {
            "customer_name": "[此处填充客户名称]",
            "specialist_name": "[此处填充业务专员名字]",
            "apply_year_date": "[此处填充年份eg:2020]",
            "write_off": "[此处填充核销金额]"
        }

    def set_name(self, **kwargs):
        attributes = self.result_dict
        self.customer_name = attributes.get("customer_name", "DK")
        self.specialist_name = attributes.get("specialist_name", "DK")
        self.apply_year_date = attributes.get("apply_year_date", "DK")
        self.write_off = attributes.get("write_off", "DK")
        self.name = f"{self.customer_name}{self.coon}{self.specialist_name}{self.coon}{self.apply_year_date}{self.coon}{self.write_off}"


class AuthorizationLetterConvention(NamingRule):
    """
    委托书类
    客户名称(全称)+业务专员名字+年月+到期日
    """

    def __init__(self, **kwargs):
        super(AuthorizationLetterConvention, self).__init__()
        self.customer_name = None
        self.specialist_name = None
        self.apply_date = None
        self.expire_date = None

    def set_rule(self, **kwargs) -> dict:
        return {
            "customer_name": "[此处填充客户名称]",
            "specialist_name": "[此处填充业务专员名字]",
            "apply_date": "[此处填充年月eg:202005]",
            "expire_date": "[此处填充到期日eg:20200501]"
        }

    def set_name(self, **kwargs):
        attributes = self.result_dict
        self.customer_name = attributes.get("customer_name", "DK")
        self.specialist_name = attributes.get("specialist_name", "DK")
        self.apply_date = attributes.get("apply_date", "DK")
        self.expire_date = attributes.get("expire_date", "DK")
        self.name = f"{self.customer_name}{self.coon}{self.specialist_name}{self.coon}{self.apply_date}{self.coon}{self.expire_date}"


class TenderDocumentConvention(NamingRule):
    """
    招标文件类
    客户名称(全称)+业务专员名字+年月_流水号
    """

    def __init__(self, **kwargs):
        super(TenderDocumentConvention, self).__init__()
        self.customer_name = None
        self.specialist_name = None
        self.apply_date = None
        self.seq_no = None

    def set_rule(self, **kwargs) -> dict:
        return {
            "customer_name": "[此处填充客户名称]",
            "specialist_name": "[此处填充业务专员名字]",
            "apply_date": "[此处填充年月eg:202005]",
            "seq_no": "[此处填充流水号]"
        }

    def set_name(self, **kwargs):
        attributes = self.result_dict
        self.customer_name = attributes.get("customer_name", "DK")
        self.specialist_name = attributes.get("specialist_name", "DK")
        self.apply_date = attributes.get("apply_date", "DK")
        self.seq_no = attributes.get("seq_no", "DK")
        self.name = f"{self.customer_name}{self.coon}{self.specialist_name}{self.coon}{self.apply_date}_{self.seq_no}"


class FileConventionFactory:
    @staticmethod
    def create_file_convention(file_convention: str) -> NamingRule:
        if file_convention == "PurchaseOrderContract":
            return PurchaseOrderContractConvention()
        elif file_convention == "Agreement":
            return AgreementConvention()
        elif file_convention == "ReviewForm":
            return ReviewFormConvention()
        elif file_convention == "InvoiceAndAcceptance":
            return InvoiceAndAcceptanceConvention()
        elif file_convention == "Statement":
            return StatementConvention()
        elif file_convention == "VerificationDocument":
            return VerificationDocumentConvention()
        elif file_convention == "AuthorizationLetter":
            return AuthorizationLetterConvention()
        elif file_convention == "TenderDocument":
            return TenderDocumentConvention()
        else:
            raise ValueError("Invalid file convention type")


if __name__ == "__main__":
    llm = LLM()
    file_convention = "PurchaseOrderContract"
    new_file = FileConventionFactory.create_file_convention(file_convention)
    ocr_content = """
    SOB201902-236729
    工业品
    买卖合同
    供方：福建渠看股份有限公司
    合同编号：
    买方：喵喵有限公司
    签订时间：
    2019/2/26
    """
    msgs = new_file.prompt_start + ocr_content + new_file.prompt_end + str(new_file.set_rule()) + "\n"
    result = llm.invoke(msgs).content
    new_file.translate_json(result)

    print(new_file)
