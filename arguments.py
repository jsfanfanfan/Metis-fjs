# Copyright 2024 Samsung Electronics Co., Ltd. All Rights Reserved
import argparse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser = _add_model_args(parser)
    parser = _add_gpt_model_args(parser)
    parser = _add_cluster_args(parser)
    parser = _add_hetspeed_args(parser)
    parser = _add_env_args(parser)
    args = parser.parse_args()
    return args


def _add_model_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument('--model_name', type=str) # 名称
    parser.add_argument('--model_size', type=str) # 大小
    parser.add_argument('--num_layers', type=int) # 层数
    parser.add_argument('--gbs', type=int) # global batch size
    return parser

def _add_gpt_model_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument('--hidden_size', type=int) # 隐藏层大小
    parser.add_argument('--sequence_length', type=int) # 序列长度
    parser.add_argument('--vocab_size', type=int) # 词表大小
    parser.add_argument('--attention_head_size', type=int) # 注意力头大小
    return parser

def _add_cluster_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument('--hostfile_path') # hostfile：ip 和 gpu 数量
    parser.add_argument('--clusterfile_path') # clusterfile：节点的 GPU 显存通信等指标
    return parser


def _add_env_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument('--log_path') # log的存放路径
    parser.add_argument('--home_dir') # 工作目录
    return parser


def _add_hetspeed_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument('--profile_data_path') # profile 信息的存放路径
    parser.add_argument('--max_profiled_tp_degree', type=int) # 最大 TP
    parser.add_argument('--max_profiled_batch_size', type=int) # 最大 batchsize
    parser.add_argument('--min_group_scale_variance', type=int) # 控制设备组内的 GPU 数量
    parser.add_argument('--max_permute_len', type=int) # 控制设备组数量

    return parser
