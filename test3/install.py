# from helper.model_download import download_model_hdfs, download_model_hdfs_batch, download_model_url, \
#     download_model_url_batch
# from helper.path_manager import path_manager
#
# # 根据单个hdfs链接下载模型到指定目录
# download_model_hdfs(
#     # hdfs链接地址
#     hdfs_path="hdfs://haruna/...",
#     # 模型文件存放目录，统一通过path_manager管理模型存放目录
#     model_dir=path_manager.model_dict['clip'],
#     # 当模型存放目录已经存在同名模型文件，是否覆盖，默认为False
#     # is_overwrite=False,
# )
# # 根据多个hdfs链接下载模型到指定目录
# download_model_hdfs_batch(
#     # hdfs链接地址列表
#     hdfs_paths=[
#         "hdfs://xxx",
#         "hdfs://xxx2",
#     ],
#     # 模型文件存放目录
#     model_dir=path_manager.model_dict['facexlib'],
#     # 当模型存放目录已经存在同名模型文件，是否覆盖，默认为False
#     # is_overwrite=False,
# )
#
# # 根据http地址下载模型，参数说明和hdfs下载方法一致
# download_model_url(
#     model_url='https://xxx',
#     model_dir='xxx'
# )
# # 根据http地址批量下载模型，参数说明和hdfs下载方法一致
# download_model_url_batch(
#     model_urls=[
#         'https://xx',
#         'https://xx2',
#     ],
#     model_dir='xxx'
# )
