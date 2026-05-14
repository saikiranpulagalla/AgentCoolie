import { useEffect, useRef } from "react";
import { useToast } from "@/hooks/use-toast";
import { useNotification } from "@/contexts/NotificationContext";
import { apiFetch } from "@/lib/api";

type ReminderRow = {
  id: string;
  type: string;
  message: string;
  datetime?: string;
  status: string;
  notify_by_call?: boolean;
  call_error_code?: string;
};

const MISSED_OFFLINE_GRACE_MS = 120000;

function openUrl(url: string) {
  try {
    const opened = window.open(url, "_blank");
    if (opened) {
      try {
        opened.opener = null;
      } catch {
        // opener hardening is best effort
      }
      try {
        opened.focus();
      } catch {
        // focus is best effort
      }
      return;
    }
  } catch (e) {
    console.warn("Scheduled task window.open failed:", e);
  }
}

export function ScheduledTaskRunner() {
  const processingIds = useRef(new Set<string>());
  const nextAllowedCheckAt = useRef(0);
  const { toast } = useToast();
  const { addNotification } = useNotification();

  useEffect(() => {
    let stopped = false;
    let intervalId: number | undefined;

    const runDueTasks = async () => {
      if (document.hidden) return;

      const now = Date.now();
      if (now < nextAllowedCheckAt.current) return;

      try {
        const response = await apiFetch("/api/reminders");
        if (!response.ok) {
          if (response.status === 503) {
            nextAllowedCheckAt.current = Date.now() + 60000;
          }
          return;
        }
        nextAllowedCheckAt.current = 0;

        const rows = (await response.json()) as ReminderRow[];
        if (!Array.isArray(rows)) return;

        const currentTime = Date.now();
        const dueTasks = rows.filter((row) => {
          if (row.status === "sent" || row.status === "missed_offline" || row.status === "calling" || row.status === "failed" || !row.datetime) return false;
          const dueAt = Date.parse(row.datetime);
          return !Number.isNaN(dueAt) && dueAt <= currentTime;
        });

        for (const task of dueTasks) {
          if (stopped || processingIds.current.has(task.id)) continue;
          processingIds.current.add(task.id);

          try {
            const dueAt = task.datetime ? Date.parse(task.datetime) : currentTime;
            const missedWhileOffline = Number.isFinite(dueAt) && currentTime - dueAt > MISSED_OFFLINE_GRACE_MS;

            if (missedWhileOffline && !task.notify_by_call) {
              const message = "This task was due while this PC was offline, asleep, or the app was closed.";
              const patchResponse = await apiFetch(`/api/reminders/${task.id}`, {
                method: "PATCH",
                body: JSON.stringify({
                  status: "missed_offline",
                  execution_message: message,
                  last_attempt_at: new Date().toISOString(),
                }),
              });

              if (patchResponse.ok) {
                toast({
                  title: "Task missed while offline",
                  description: task.message,
                });
                addNotification({
                  id: task.id,
                  title: task.message.slice(0, 40),
                  description: message,
                  type: task.type || "general",
                  completedAt: new Date(),
                });
              }
              continue;
            }

            const executeResponse = await apiFetch(`/api/reminders/${task.id}/execute`, {
              method: "POST",
            });

            if (!executeResponse.ok) {
              processingIds.current.delete(task.id);
              continue;
            }
            const executePayload = await executeResponse.json().catch(() => ({}));
            if (executePayload?.status === "already_handled") {
              processingIds.current.delete(task.id);
              continue;
            }
            const failed = executePayload?.status === "failed";
            const failedTask = executePayload?.task || {};
            const callErrorCode = failedTask?.call_error_code;
            const isUnverifiedCall = callErrorCode === "twilio_unverified_number";
            const friendlyError = executePayload?.error || task.message;

            toast({
              title: failed ? (isUnverifiedCall ? "Call number not verified" : "Task failed") : task.type === "youtube" ? "YouTube task due" : "Task completed",
              description: failed ? friendlyError : task.message,
            });
            addNotification({
              id: task.id,
              title: task.message.slice(0, 40),
              description: failed ? friendlyError : task.message,
              type: task.type || "general",
              completedAt: new Date(),
            });

            const url = executePayload?.action?.open_url;
            if (!failed && typeof url === "string" && url.trim()) {
              openUrl(url);
            }
          } catch (e) {
            console.error("Failed to run scheduled task:", e);
          } finally {
            processingIds.current.delete(task.id);
          }
        }
      } catch (e) {
        nextAllowedCheckAt.current = Date.now() + 60000;
        console.warn("Scheduled task check failed:", e);
      }
    };

    const stopPolling = () => {
      if (intervalId !== undefined) {
        window.clearInterval(intervalId);
        intervalId = undefined;
      }
    };

    const startPolling = () => {
      stopPolling();
      if (document.hidden) return;
      runDueTasks();
      intervalId = window.setInterval(runDueTasks, 15000);
    };

    const handleVisibilityChange = () => {
      if (document.hidden) {
        stopPolling();
      } else {
        startPolling();
      }
    };

    startPolling();
    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      stopped = true;
      stopPolling();
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [addNotification, toast]);

  return null;
}
