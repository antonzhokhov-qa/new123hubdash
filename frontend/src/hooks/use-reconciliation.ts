import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { mockReconciliationSummary, mockDiscrepancies } from "@/lib/mock-data";

const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "true";

export function useReconciliationSummary(date: string) {
  return useQuery({
    queryKey: ["reconciliation", "summary", date],
    queryFn: async () => {
      if (USE_MOCK) {
        await new Promise((r) => setTimeout(r, 400));
        return { data: { ...mockReconciliationSummary, date } };
      }
      return api.getReconciliationSummary(date);
    },
    enabled: !!date,
  });
}

interface DiscrepancyParams {
  from_date?: string;
  to_date?: string;
  type?: string;
  page?: number;
  limit?: number;
}

export function useDiscrepancies(params: DiscrepancyParams) {
  return useQuery({
    queryKey: ["reconciliation", "discrepancies", params],
    queryFn: async () => {
      if (USE_MOCK) {
        await new Promise((r) => setTimeout(r, 400));
        let filtered = [...mockDiscrepancies];
        
        if (params.type) {
          filtered = filtered.filter((d) => 
            d.discrepancy_type === params.type || d.match_status === params.type
          );
        }
        
        const page = params.page || 1;
        const limit = params.limit || 50;
        
        return {
          data: filtered,
          meta: {
            page,
            limit,
            total: filtered.length,
            total_pages: Math.ceil(filtered.length / limit),
          },
        };
      }
      return api.getDiscrepancies(params);
    },
  });
}

export function useRunReconciliation() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (date: string) => {
      if (USE_MOCK) {
        await new Promise((r) => setTimeout(r, 1000));
        return {
          data: {
            run_id: "mock-run-id",
            status: "completed",
            message: "Reconciliation completed successfully",
          },
        };
      }
      return api.runReconciliation(date);
    },
    onSuccess: (_, date) => {
      queryClient.invalidateQueries({ queryKey: ["reconciliation", "summary", date] });
      queryClient.invalidateQueries({ queryKey: ["reconciliation", "discrepancies"] });
    },
  });
}
