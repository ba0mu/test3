import hashlib
import os
import random
import time
from types import ModuleType

import euler
import thriftpy2
from euler.base_compat_middleware import client_middleware

from .resp_error import RespError
from .retry import safe_retry


class IdlLoader:
    def __init__(self):
        self.current_dir: str = os.path.dirname(os.path.realpath(__file__))
        self.algo_service_idl: ModuleType = self.load_idl("idls/vproxy.thrift", "service_thrift")
        self.base_idl: ModuleType = self.load_idl("idls/base.thrift", "base_thrift")
        self.common_idl: ModuleType = self.load_idl("idls/common.thrift", "common_thrift")

    def load_idl(self, target_path: str, module_name: str):
        idl_path = os.path.join(self.current_dir, target_path)
        return thriftpy2.load(path=idl_path, module_name=module_name)


class AlgoVProxyClient:
    algo_psm = 'toutiao.labcv.algo_vproxy'
    algo_cluster = 'default'
    idc_adaptor_list: set[str] = {'pd', 'yg', 'hj'}

    def __init__(self, app_key: str, app_secret: str):
        self.app_key = app_key
        self.app_secret = app_secret
        self.idl_loader: IdlLoader = IdlLoader()
        psm_idc = os.getenv('TCE_INTERNAL_IDC')
        euler_target = f"sd://{AlgoVProxyClient.algo_psm}?cluster={AlgoVProxyClient.algo_cluster}"
        if psm_idc and psm_idc.lower() in AlgoVProxyClient.idc_adaptor_list:
            euler_target += '&idc=lq'
        self.algo_v_proxy_client: euler.Client = euler.Client(
            service_cls=self.idl_loader.algo_service_idl.VisionService,
            target=euler_target,
            timeout=30
        )
        self.algo_v_proxy_client.use(client_middleware)

    def gen_sign(self, nonce, app_secret, timestamp):
        keys = [str(nonce), str(app_secret), str(timestamp)]
        keys.sort()
        key_str = ''.join(keys)
        key_str = key_str.encode('utf-8')
        signature = hashlib.sha1(key_str).hexdigest()
        return signature.lower()

    @safe_retry()
    def send(self, req_key: str, req_json: str = '', binary_data: list[bytes] = []):
        auth_info = self.idl_loader.common_idl.AuthInfo()
        req = self.idl_loader.common_idl.AlgoReq(
            req_key=req_key,
            req_json=req_json,
            binary_data=binary_data,
            auth_info=auth_info
        )
        nonce = str(random.randint(0, (1 << 31) - 1))
        timestamp = str(int(time.time()))

        req.auth_info.app_key = self.app_key
        req.auth_info.timestamp = timestamp
        req.auth_info.nonce = nonce
        req.auth_info.sign = self.gen_sign(nonce, self.app_secret, timestamp)

        response = self.algo_v_proxy_client.Process(req)

        if not hasattr(response, "BaseResp"):
            return response
        if getattr(response.BaseResp, "StatusCode", 0) != 0:
            message = getattr(response.BaseResp, "StatusMessage", "unknown error")
            extra = getattr(response.BaseResp, "Extra", {})
            log_id = extra.get('log_id', '') if isinstance(extra, dict) else ''
            raise RespError(error_code=response.BaseResp.StatusCode, message=message, log_id=log_id, req_key=req_key)
        return response

# 智创网关RPC调用服务，填写智创控制台上应用的app_key和app_secret
# algo_v_proxy_client = AlgoVProxyClient(app_key='xxx',
#                                        app_secret='xxx')

# 比如在nodes目录中的某个节点需要使用算法网关服务，需要通过相对路径引入algo_v_proxy_client
# 比如在nodes/image_node.py中可以通过以下语句导入algo_v_proxy_client实例
# from ..algo_vproxy.algo_vproxy import algo_v_proxy_client
