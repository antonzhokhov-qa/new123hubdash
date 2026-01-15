import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, Source } from "@/lib/api";
import { mockSyncStatus } from "@/lib/mock-data";

const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "true";

export function useSyncStatus() {
  return useQuery({
    queryKey: ["sync", "status"],
    queryFn: async () => {
      if (USE_MOCK) {
        await new Promise((r) => setTimeout(r, 300));
        return { data: mockSyncStatus };
      }
      return api.getSyncStatus();
    },
    staleTime: 10_000,
    refetchInterval: 30_000,
  });
}

export function useTriggerSync() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (source?: Source) => {
      if (USE_MOCK) {
        await new Promise((r) => setTimeout(r, 500));
        return {
          data: {
            source: source || "all",
            status: "triggered",
            message: `Sync triggered for ${source || "all sources"}`,
          },
        };
      }
      return api.triggerSync(source);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sync", "status"] });
    },
  });
}
