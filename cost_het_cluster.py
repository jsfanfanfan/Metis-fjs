# Copyright 2024 Samsung Electronics Co., Ltd. All Rights Reserved
import argparse
from typing import Dict, List, Tuple
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from arguments import parse_args
from data_loader import ProfileDataLoader
from model.cost_estimator import HeteroCostEstimator
from model.activation_parameter import GPTActivationAndParam
from model.device_group import StagePerformance
from model.load_balancer import LayerLoadBalancer
from search_space.plan import IntraStagePlanGenerator, InterStagePlanGenerator
from gpu_cluster import GPUCluster
from utils import ModelConfig


def cost_het_cluster(args: argparse.Namespace, gpu_cluster: GPUCluster, profile_data: Dict, model_config: ModelConfig,
                     cost_estimator: HeteroCostEstimator, layer_load_balancer:LayerLoadBalancer) -> List[Tuple]:

    estimate_costs = []
    # plan.py 100 行 生成流水级间的策略
    for inter_stage_plan in InterStagePlanGenerator(device_types=set(gpu_cluster.get_device_types()),
                                                    num_devices=gpu_cluster.get_total_num_devices(),
                                                    gbs=args.gbs, num_layers=args.num_layers,
                                                    variance=args.min_group_scale_variance,
                                                    max_permute_len=args.max_permute_len):

        print(f'\n\ninter_stage_plan: {inter_stage_plan}')
        # device_group.py 13 行
        stage_performance = StagePerformance(model_config, profile_data, gpu_cluster, inter_stage_plan)
        # 获取 rank 和 device 的映射
        rank_device_map = stage_performance.get_device_placement()
        # plan.py 178 行 生成流水级内的并行策略
        intra_stage_plan_generator = IntraStagePlanGenerator(inter_stage_plan, stage_performance, layer_load_balancer,
                                                             args.max_profiled_tp_degree, args.max_profiled_batch_size)

        while intra_stage_plan_generator.has_next:
            intra_stage_plan = intra_stage_plan_generator.next()
            try:# 获得执行开销
                cost = cost_estimator.get_cost(inter_stage_plan, intra_stage_plan.strategies,
                                               intra_stage_plan.layer_partition, rank_device_map)
                print(f'cost: {cost}')
                estimate_costs.append((inter_stage_plan.node_sequence, inter_stage_plan.device_groups,
                                       intra_stage_plan.strategies, inter_stage_plan.batches,
                                       intra_stage_plan.layer_partition, intra_stage_plan.num_repartition, cost))
            except KeyError as e:
                print(f'KeyError: {e}')

    return estimate_costs


if __name__ == '__main__':
    args = parse_args() # arguments.py 获取基本参数
    # gpu_cluster.py 8 行；返回一个 GPUCluster 类, 获取到集群信息
    gpu_cluster = GPUCluster(hostfile_path=args.hostfile_path, clusterfile_path=args.clusterfile_path) # GPU 集群信息
    # data_loader.py 10 行；建立 profile_data 的列表
    data_loader = ProfileDataLoader(args.profile_data_path)
    # 返回 profile_data 和 device type
    # data_loader.py 42 行
    profile_data, _ = data_loader.load_profile_data_all()
    print(profile_data)

    assert len(profile_data.keys()) > 0, 'There is no profiled data at the specified path.'
    # utils.py 72行 获取模型配置信息; ModelConfig 是一个数据类
    model_config = ModelConfig(model_name=args.model_name, num_layers=args.num_layers,
                               sequence_length=args.sequence_length, vocab_size=args.vocab_size,
                               hidden_size=args.hidden_size, attention_head_size=args.attention_head_size)
    # activation_parameter.py 5 行, 获得模型层的参数量和激活大小
    model_volume = GPTActivationAndParam(model_config, profile_data['model']['parameters'])
    # cost_estimator.py 141 行; 初始化一个 HeteroCostEstimator 类
    cost_estimator = HeteroCostEstimator(profile_data, model_config, model_volume, gpu_cluster)
    # load_balancer.py 14 行
    layer_load_balancer = LayerLoadBalancer(gpu_cluster, profile_data, model_config, args.gbs)
    # 调用第 20 行的函数估计开销
    estimate_costs = cost_het_cluster(args, gpu_cluster, profile_data, model_config, cost_estimator, layer_load_balancer)

    print(f'len(costs): {len(estimate_costs)}')
    sorted_result = sorted(estimate_costs, key=lambda kv: kv[6])
    print(
        'rank, cost, node_sequence, device_groups, strategies(dp_deg, tp_deg), batches(number of batch), layer_partition')
    for idx, result in enumerate(sorted_result):
        print(f'{idx + 1}, {result[6]}, {result[0]}, {result[1]}, {result[2]}, {result[3]}, {result[4]}')