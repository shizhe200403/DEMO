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
