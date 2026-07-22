from bytedance.vcloud.imagex.imagex_service import ImageXService 
import base64
import bytedenv
from hashlib import md5
import requests
import io
import cv2
import torch
import numpy as np
from PIL import Image


from bytedance.vcloud.imagex.const import (
    REGION_CN_NORTH1,
    REGION_AP_SINGAPORE1,
    REGION_US_EAST2,
    REGION_US_EAST1
)


# use base64 to decode the ak and sk
IMAGEX_REGION_AK = {
    REGION_AP_SINGAPORE1: base64.b64decode(b"QUtMVE16STBNamt3T0RNeU0yWTBORE00T1dJMU0yWXlOelJqT0RFd1lXRmpNakk=").decode(),
    REGION_US_EAST1: base64.b64decode(b"QUtMVE16STBNamt3T0RNeU0yWTBORE00T1dJMU0yWXlOelJqT0RFd1lXRmpNakk=").decode(),
}
IMAGEX_REGION_SK = {
    REGION_AP_SINGAPORE1: base64.b64decode(b"VFRKVmVGcHFhelJOUkZWNlRXMVJlazVFVVRWT01rWm9UbXBSTkZsVVFUSlBSR013VFZSU2JWcHRSUT09").decode(),
    REGION_US_EAST1: base64.b64decode(b"VFRKVmVGcHFhelJOUkZWNlRXMVJlazVFVVRWT01rWm9UbXBSTkZsVVFUSlBSR013VFZSU2JWcHRSUT09").decode(),
}


def tensor2rgb(tensor, format=""):
    img = 255. * tensor.cpu().numpy()
    if not format:
        format = "PNG" if (len(img.shape)) == 3 and img.shape[2] == 4 else "JPEG"
    if img.ndim == 4:
        img = img.squeeze(0)
    img = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format=format)
    img_binary = img_byte_arr.getvalue()
    return img_binary

def upload_to_imagex(file:bytes, idc:str=None, region=None)->str:
    """
        upload image to imagex and return the uri of the imageX
        imageX space:

    """
    client = ImageXService()
    if not region:
        region = REGION_US_EAST1
    client = ImageXService(region=REGION_US_EAST1)
    ak, sk = IMAGEX_REGION_AK[region], IMAGEX_REGION_SK[region]
    print(ak, sk)
    client.set_ak(ak)
    client.set_sk(sk)

    resp = client.upload_images(
        params={
            "ServiceId": "51pdn7bo8b",
            "SkipMeta": False,
            "UploadByHost": False,
            "TosIDC": "maliva"
        },
        img_datas=[file])
    return resp["Results"][0]["Uri"]


def download_video(vid):
    from ivory.tools.download import download_from_varch
    # download_from_varch.set_video_status(vid=vid,psm="ic.aip.image2video")
    url = download_from_varch.vid_to_url(vid)
    tmp_path = f"/tmp/{vid}.mp4"
    with open(tmp_path, "wb") as fp:
        fp.write(requests.get(url)  .content)
    return tmp_path



if __name__ == "__main__":
    test_jpg = "/mlx_devbox/users/likaiyun/playground/arnold_workspace_root/vpipe/vpipe/deployment/vgfm_automl/test.jpg"

    with open(test_jpg, "rb") as fp:
        image_data = fp.read()
        uri = upload_to_imagex(image_data)
        print(uri)