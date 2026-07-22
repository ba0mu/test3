from bytedance import ivory
import euler
import json
import time
from cairo_v2.idls import Base, GetTaskReportRequest, CairoService, GetTaskReportResponse, SubmitAsyncTaskRequest, Task
from euler import base_compat_middleware
from .utils import upload_to_imagex, download_video,tensor2rgb
from PIL import Image
from io import BytesIO
from ivory.tools.download import download_from_varch

import logging
import bytedlogger

bytedlogger.config_default()

# 初始化Cairo客户端
cairo_client = euler.Client(CairoService, target="sd://aip.tce.cairo_v2?cluster=default&idc=maliva",timeout=120)
cairo_client.use(base_compat_middleware.client_middleware)

cairo_client_dev = euler.Client(CairoService, target="sd://aipdev.tce.cairo_v2?cluster=default&idc=maliva",timeout=120)
cairo_client_dev.use(base_compat_middleware.client_middleware)

class I2V:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "Firstimage": ("IMAGE",),
                "MODEL": (["i2v", "fl2v"],),
                "MODE":(["8nfe", "12nfe", "v0.4"],),
                "do_rephrase":(["true", "false"],),
                "do_facegan":(["true", "false"],),
                # 音频控制：with_audio 同时决定 generate_audio，remove_audio 用于显式移除音频
                "with_audio": ("BOOLEAN", {"default": True}),
                "remove_audio": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "Lastimage": ("IMAGE",),
                "seed":("INT", {"default": 0}),
                "prompt": ("STRING", {"default": "", "multiline": True, "dynamicPrompts": False}),
                "req_json": ("STRING", {"default": "", "multiline": True, "dynamicPrompts": False}),
            }
        }

    CATEGORY = "TemplateNode"

    RETURN_TYPES = ("STRING","STRING")
    RETURN_NAMES = ("url", "resp_json")
    FUNCTION = "process"

    def process(self, Firstimage, MODEL, MODE, do_rephrase, do_facegan,
                with_audio=True, remove_audio=False, **kwargs):
        
        """
        适配二进制数据输入的图像转视频处理函数
        Args:
            binary_list: 图像二进制数据（支持列表）
            prompt: 生成视频的提示词
        """
        seed = kwargs.get("seed")
        req_json_str = kwargs.get("req_json")
        print(f"原始req_json: {req_json_str}")

        is_dev = False  # 默认值

        if req_json_str:
            try:
                # 解析JSON字符串
                req_data = json.loads(req_json_str)

                 # 新增：提取 req_json 中的 biz_id 和 workflow_id（若存在）
                req_biz_id = req_data.pop("biz_id", None)  # 从req_data中移除并保存
                req_workflow_id = req_data.pop("workflow_id", None)  # 从req_data中移除并保存

                
                # 提取is_dev属性并转为布尔值
                if "is_dev" in req_data:
                    is_dev_value = req_data.pop("is_dev")  # 移除is_dev字段
                    is_dev = bool(is_dev_value)  # 转换为布尔值
                    
                    # 特殊处理字符串形式的布尔值（如"true", "false"）
                    if isinstance(is_dev_value, str):
                        is_dev = is_dev_value.lower() == "true"
                
                # 重新构建剩余的JSON字符串
                req_json = json.dumps(req_data)
                print(f"处理后的req_json: {req_json}")
                print(f"提取的is_dev: {is_dev}")
                
            except json.JSONDecodeError as e:
                print(f"JSON解析错误: {e}")
                # 处理解析失败的情况，保持原始值或设置默认值
                req_json = req_json_str
        else:
            req_json = req_json_str  # 保持为空或None
            req_biz_id = None
            req_workflow_id = None


        if is_dev != True:
            print("false")

        print(f"zyl{type(seed)}")
        prompt = kwargs.get("prompt")
        if MODEL=="i2v" and MODE=="8nfe":
            biz_id = "image2video_dit_prompt"
            workflow_id = "image2video_dit_prompt_inference_only_v2"
            print("mode1")
        elif MODEL=="i2v" and MODE=="12nfe":
            biz_id = "image2video_dit_effect_12nfe"
            workflow_id = "image2video_dit_effect_12nfe_inference_only_v2"
            print("mode2")
        elif MODEL=="fl2v" and MODE=="8nfe":
            biz_id = "image2video_dit_fl2v"
            workflow_id = "image2video_dit_fl2v_inference_only_v2"
            print("mode3")
        elif MODEL=="fl2v" and MODE=="12nfe":
            biz_id = "image2video_dit_effect_12nfe_fl2v"
            workflow_id = "image2video_dit_effect_12nfe_fl2v_inference_only_v2"
            print("mode4")
        elif MODEL=="fl2v" and MODE=="v0.4":
            biz_id = "image2video_dit_effect_fl2v_v04"
            workflow_id = "image2video_dit_effect_fl2v_v04_inference_only_v2"
        else:
            raise ValueError(f"No support for {MODEL}:{MODE}!")

        if req_biz_id is not None:
                biz_id = req_biz_id
                print(f"已通过 req_json 覆盖 biz_id: {biz_id}")
        if req_workflow_id is not None:
                workflow_id = req_workflow_id
                print(f"已通过 req_json 覆盖 workflow_id: {workflow_id}")


        import time
        image1 = tensor2rgb(Firstimage,  format="PNG")
        imagex_uri = upload_to_imagex(image1)
        logging.info(f"[image-saver] upload image to imagex, uri is {imagex_uri}")
        if(MODEL == "fl2v"):
            Lastimage = kwargs.get("Lastimage")
            image2 = tensor2rgb(Lastimage,  format="PNG")
            imagex_uri2 = upload_to_imagex(image2)
            logging.info(f"[image-saver] upload image to imagex, uri2 is {imagex_uri2}")
        ### change tos_style_url to the style you want to test
        req_json_dict = {
                "seed": seed,
                "prompt": prompt,
                "do_rephrase": True if do_rephrase == "true" else False,
                "do_facegan": True if do_facegan == "true" else False,
                # 后端要求 generate_audio 与 with_audio 保持一致
                "with_audio": bool(with_audio),
                "generate_audio": bool(with_audio),
                "remove_audio": bool(remove_audio)
            }
        req_json_dict.update(json.loads(req_json))
        print(f"{req_json_dict}")

        algo_config = [{
            "req_key": biz_id,
            "req_json": json.dumps(
                req_json_dict
            )
        }]
        if(MODEL == "fl2v"):
            data = {
                imagex_uri:{
                    "Uri":imagex_uri,"Gender":0,"SkinColor":"","ImageType":0,"Extra":""
                },
                imagex_uri2:{
                    "Uri":imagex_uri2,"Gender":0,"SkinColor":"","ImageType":0,"Extra":""
                }
            }
        else:
            data = {
                imagex_uri:{
                    "Uri":imagex_uri,"Gender":0,"SkinColor":"","ImageType":0,"Extra":""
                }
            }
        req = SubmitAsyncTaskRequest(
            workflow_id = workflow_id,
            task = Task(
                biz_id = biz_id,
                input = json.dumps(
                    {
                        "data": json.dumps(data),
                        "algo_config": json.dumps(algo_config),
                        "upload_region":"Singapore-Central"
                    }
                ),
                priority = 6
            ),
        
            Base=Base(),
        )
        cur_cairo_client = cairo_client_dev if is_dev else cairo_client
        print(f"req is:{req}")
        resp: GetTaskReportResponse = cur_cairo_client.SubmitAsyncTask(req)
        start_time = time.time()
        timeout_seconds = 300  # 5分钟超时
        while(1):
            # query
            req = GetTaskReportRequest(
                task_id=resp.task_id, #"57f6a369dce947c1b4c321a49dafdbef",#"45996e9ce8d942c7bc865052f2e76771",#"840a16203a984a04b9a022bc6a542868",#"023b25e65ced471f97e20e8bc20903ce",#
                biz_id = biz_id,
                type="basic",
                Base=Base()
            )
            print(f"req2 is:{req}")
            report = cur_cairo_client.GetTaskReport(req)
            # print("report",report)
            report_dict = json.loads(report.task)
            print(report_dict)
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout_seconds:
                logging.warning(f"任务查询超时，耗时: {elapsed_time:.2f}秒")
                return None  # 超时返回
            if (report_dict["output"]):
                output_json = json.loads(report_dict['output'])["results"]
                vid = list(output_json.keys())[0]
                print(f"vid:{vid}")
                url = None
                for i in range(3): #Retry 3 次
                    try:
                        print(f"try {i} times")
                        from ivory.tools.download import download_from_varch
                        # download_from_varch.set_video_status(vid)
                        url = download_from_varch.vid_to_url(vid, url_type=8)
                        if url is None:
                            print("url is None")
                            raise Exception("url is None")
                        break
                    except Exception as e:
                        print("vid error", e)
                        time.sleep(5)
                        continue
                return (url, output_json)
            else:
                print( "progress:"+str(json.loads(report.report)['progress']))
