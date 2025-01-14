# Copyright 2024 Samsung Electronics Co., Ltd. All Rights Reserved
import json
import os
import re
from typing import Dict, Union, List, Tuple

from search_space.plan import UniformPlan


class ProfileDataLoader:
    def __init__(self, profile_dir: str):
        self.profile_dir = profile_dir
        # Find a list of files that contain profile data
        self.profile_data_list = [fname for fname in os.listdir(profile_dir) if fname.endswith('.json')]

    def _get_model_profile_data(self, raw_data: Dict[str, Dict]) \
            -> Dict[str, Dict[str, Union[int, float, List]]]:
        model_profile_data = dict()
        # optimizer time 为什么 * 2？
        model_profile_data['optimizer_time'] = raw_data['execution_time']['optimizer_time_ms'] * 2
        num_layers = len(raw_data['execution_time']['layer_compute_total_ms'])
        model_profile_data['num_layers'] = num_layers
        model_profile_data['batch_generator'] = raw_data['execution_time']['batch_generator_time_ms']
        # 每一层参数的字节数
        model_profile_data['parameters'] = raw_data['model']['parameters']['parameters_per_layer_bytes']
        return model_profile_data

    def _get_device_type_specific_profile_data(self, raw_data: Dict[str, Dict[str, Union[int, float, List]]])\
            -> Dict[str, Dict[str, Union[int, float, List]]]:
        profile_data = dict()
        profile_data["time"] = dict()
        layer_computes = raw_data['execution_time']['layer_compute_total_ms']
        layer_compute_times = [layer_compute for layer_compute in layer_computes]
        profile_data["time"]["layer-computes"] = layer_compute_times
        forward_backward_time = raw_data['execution_time']['forward_backward_time_ms']
        # 同步的时间等于 forward_backward_time 减去层计算时间之和
        profile_data["time"]["fb_sync"] = forward_backward_time - sum(layer_compute_times)
        profile_data['memory'] = raw_data['execution_memory']['layer_memory_total_mb']

        return profile_data
    # 获取所有 profile data 数据
    def load_profile_data_all(self) -> Tuple[Dict, List]:
        profile_data = dict()
        device_types = []
        # 遍历 profile_data 中的所有 json 文件
        for profile_data_path in self.profile_data_list:
            # 从 profile_data_path 提取出符合正则表达式模式的子串
            # 具体是提取 DeviceType.XXX_ 中的 XXX 部分(A100, V100...)
            device_type = re.search(r"DeviceType\.(\w+?)_", profile_data_path).group(1)
            if f'DeviceType.{device_type}' not in profile_data.keys():
                profile_data[f'DeviceType.{device_type}'] = dict()
                device_types.append(device_type)
            # 获取 tp degree 和 batchsize
            tp = re.search(r"tp(\d+)", profile_data_path).group(1)
            bs = re.search(r"bs(\d+)", profile_data_path).group(1)
            # 解析 json 文件
            with open(f'{self.profile_dir}/{profile_data_path}', 'r') as content:
                raw_profile_data = json.loads(content.read())

                if "model" not in profile_data.keys():
                    model_profile_data = self._get_model_profile_data(raw_profile_data)
                    profile_data["model"] = model_profile_data

                profile_data[f"DeviceType.{device_type}"][f"tp{tp}_bs{bs}"] = \
                    self._get_device_type_specific_profile_data(raw_profile_data)
        # 返回 profile_data 和 device_types
        return profile_data, device_types
