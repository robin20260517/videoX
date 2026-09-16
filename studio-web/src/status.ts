import type { Job } from "./api";
export const statusNames: Record<string, string> = {
  drafting: "正在导演构思",
  draft_ready: "草稿待审核",
  submitting: "正在提交",
  submission_unknown: "提交状态待确认",
  queued: "服务商排队中",
  running: "视频生成中",
  succeeded: "已完成",
  failed: "失败",
  interrupted: "任务已中断",
};
export const pendingStatuses = ["drafting", "submitting", "queued", "running"];
export const shouldPoll = (j: Job) =>
  pendingStatuses.includes(j.status) ||
  (j.status === "submission_unknown" && !!j.task_id);
