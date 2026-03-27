export { ElMessage } from "element-plus/es/components/message/index.mjs";
export { ElMessageBox } from "element-plus/es/components/message-box/index.mjs";

import { ElMessage } from "element-plus/es/components/message/index.mjs";

export function notifyLoadError(subject: string) {
  ElMessage.error(`加载${subject}失败，请稍后重试`);
}

export function notifyActionSuccess(message: string) {
  ElMessage.success(message);
}

export function notifyActionError(action: string) {
  ElMessage.error(`${action}失败，请稍后重试`);
}

export function notifyWarning(message: string) {
  ElMessage.warning(message);
}

export function notifyErrorMessage(message: string) {
  ElMessage.error(message);
}

export function extractApiErrorMessage(error: unknown, fallback = "操作失败，请稍后重试") {
  const responseData = (error as { response?: { data?: any } })?.response?.data;

  if (typeof responseData === "string" && responseData.trim()) {
    return responseData;
  }

  const candidates = [
    responseData?.message,
    responseData?.detail,
    responseData?.error,
    Array.isArray(responseData?.non_field_errors) ? responseData.non_field_errors[0] : null,
  ];

  for (const value of candidates) {
    if (typeof value === "string" && value.trim()) {
      return value;
    }
  }

  if (responseData && typeof responseData === "object") {
    for (const value of Object.values(responseData)) {
      if (typeof value === "string" && value.trim()) {
        return value;
      }
      if (Array.isArray(value) && typeof value[0] === "string" && value[0].trim()) {
        return value[0];
      }
    }
  }

  return fallback;
}
