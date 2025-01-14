# Copyright 2024 Samsung Electronics Co., Ltd. All Rights Reserved
#!/bin/bash
# $0 是一个 Shell 脚本内置变量，表示当前脚本的文件名（包括路径）
# dirname 是一个命令，用于提取路径的目录部分
# 这条命令进入 shell 脚本文件所在的目录
cd "$(dirname $"0")"
# "$@" 表示传递给脚本的所有参数，每个参数是一个独立的字符串
for ARGUMENT in "$@"
do
   # cut -f1 -d= 使用 = 作为分隔符，提取第一个字段，即参数的 KEY
   KEY=$(echo $ARGUMENT | cut -f1 -d=) # 提取出参数的 key
   # 获取字符串长度
   KEY_LENGTH=${#KEY}
   # 字符串切片操作，从索引 $KEY_LENGTH+1 开始提取子串，跳过 KEY= 后的内容
   VALUE="${ARGUMENT:$KEY_LENGTH+1}" # 使用字符串切片提取 value
   # 设置环境变量
   export "$KEY"="$VALUE"
done

model_options="
                --model_name=${MODEL_NAME}
                --model_size=${MODEL_SIZE}
                --num_layers=${NUM_LAYERS}
                --gbs=${GBS}
              "
if [ "${MODEL_NAME}" == "GPT" ]; then
  if [ "${MODEL_SIZE}" == "1.5B" ] ; then
    HIDDEN_SIZE=4096
    SEQUENCE_LENGTH=1024
    NUM_LAYERS=10
    VOCAB_SIZE=51200
    ATTENTION_HEAD_SIZE=32
  fi

  model_specific_options="
                --hidden_size=${HIDDEN_SIZE}
                --sequence_length=${SEQUENCE_LENGTH}
                --vocab_size=${VOCAB_SIZE}
              "
fi
# ${HOME_DIR} 需要定义吗？
HOME_DIR="."
HOST_FILE_PATH="${HOME_DIR}/hostfile"
CLUSTER_INFO_FILE_PATH="${HOME_DIR}/clusterfile.json"

cluster_options="
                  --hostfile_path=${HOST_FILE_PATH}
                  --clusterfile_path=${CLUSTER_INFO_FILE_PATH}
                "

LOG_PATH="${HOME_DIR}/logs"
current_time=$(date "+%Y.%m.%d-%H.%M.%S")

env_options="
              --home_dir=${HOME_DIR}
              --log_path=${LOG_PATH}
            "

PROFILE_DATA_PATH="${HOME_DIR}/profile"

hetspeed_options="
                    --profile_data_path=${PROFILE_DATA_PATH}
                    --max_profiled_tp_degree=${MAX_PROFILED_TP}
                    --max_profiled_batch_size=${MAX_PROFILED_BATCH_SIZE}
                    --min_group_scale_variance=${SCALE_VARIANCE}
                    --max_permute_len=${MAX_PERMUTE_LEN}
                 "
# &> 是 Bash 的一个输出重定向操作符，用于将 标准输出（stdout） 和 标准错误（stderr） 都重定向到同一个文件中
run_cmd="python3 ../cost_het_cluster.py ${model_options} ${model_specific_options} ${cluster_options} ${hetspeed_options} ${env_options}
         &> ${LOG_PATH}/${MODEL_NAME}_${MODEL_SIZE}_${current_time}.log"

echo ${run_cmd}
eval ${run_cmd}
# set +x 关闭追踪，避免不必要的调试信息被打印出来，保持输出的简洁性
set +x
