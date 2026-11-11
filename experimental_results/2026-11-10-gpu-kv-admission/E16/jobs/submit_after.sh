#!/bin/bash
# submit_after.sh <job id to wait for> <node> <time limit> <job name> <results dir for the slurm log> <job script>
# Waits until the given job has left the queue, then 40 s more (a job that starts in the second in which the previous job on the node ends was
# killed once, 334506), then submits the script to the node.
J=$1; N=$2; TL=$3; NAME=$4; LOG=$5; SCR=$6
until [ -z "$(squeue -h -j "$J" 2>/dev/null)" ]; do sleep 20; done
T=$(( $(date +%s) + 40 )); until [ "$(date +%s)" -ge "$T" ]; do sleep 5; done
cd /mnt/beegfs/ghu4/kvadm && env -u SLURM_JOB_ID -u SLURM_JOBID -u SLURM_NODELIST -u SLURM_JOB_NODELIST -u SLURM_NNODES -u SLURM_TASKS_PER_NODE -u SLURM_CPUS_ON_NODE -u SLURM_JOB_CPUS_PER_NODE -u SLURM_MEM_PER_NODE -u SLURM_JOB_PARTITION -u SLURM_SUBMIT_HOST sbatch -p rtx4060ti16g --exclusive -w "$N" -t "$TL" -J "$NAME" -o "$LOG/slurm-%j.out" "$SCR"; date
