# Copyright 2024 Samsung Electronics Co., Ltd. All Rights Reserved
#!/bin/bash
# 工作目录切换到脚本的目录下
cd "$(dirname $"0")"

for ARGUMENT in "$@" # 遍历每一个传入的参数
do
   KEY=$(echo $ARGUMENT | cut -f1 -d=) # 提取出参数的 key

   KEY_LENGTH=${#KEY} # 获取字符串长度
   VALUE="${ARGUMENT:$KEY_LENGTH+1}" # 使用字符串切片提取 value

   export "$KEY"="$VALUE" # 设置环境变量
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
