import "element-plus/es/components/message/style/css";
import "element-plus/es/components/message-box/style/css";

export { ElMessage } from "element-plus/es/components/message/index.mjs";
export { ElMessageBox } from "element-plus/es/components/message-box/index.mjs";

import { ElMessage } from "element-plus/es/components/message/index.mjs";

const FEEDBACK_MESSAGE_CLASS = "app-feedback-message";

function showFeedbackMessage(options: { message: string; type: "success" | "error" | "warning" }) {
  ElMessage({
    ...options,
    offset: 20,
    duration: 3000,
    showClose: true,
    customClass: FEEDBACK_MESSAGE_CLASS,
  });
}

export function notifyLoadError(subject: string) {
  showFeedbackMessage({
    message: `加载${subject}失败，请稍后重试`,
    type: "error",
  });
}

export function notifyActionSuccess(message: string) {
  showFeedbackMessage({
    message,
    type: "success",
  });
}

export function notifyActionError(action: string) {
  showFeedbackMessage({
    message: `${action}失败，请稍后重试`,
    type: "error",
  });
}

export function notifyWarning(message: string) {
  showFeedbackMessage({
    message,
    type: "warning",
  });
}

export function notifyErrorMessage(message: string) {
  showFeedbackMessage({
    message,
    type: "error",
  });
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
